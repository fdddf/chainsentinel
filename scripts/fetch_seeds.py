"""Fetch 1-hop Ethereum activity of the seed addresses from Etherscan API V2.

Window: 2026-10-27 00:00 UTC to 2026-11-01 00:00 UTC
(two days before the theft up to the day the FBI list was published).

Raw responses are cached in data/raw/etherscan/<address>.json and reused,
so re-running only fetches what is missing.
Writes data/edges.csv and data/raw/etherscan/manifest.json.

Usage: python scripts/fetch_seeds.py [--hop2]   (needs ETHERSCAN_API_KEY in .env)
  --hop2  fetch the neighbours of the seeds instead, into data/edges_hop2.csv
"""

import csv
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from chainsentinel.edges import FIELDS, KINDS, normalise

ROOT = Path(__file__).parents[1]
CACHE = ROOT / "data/raw/etherscan"
API = "https://api.etherscan.io/v2/api"
WINDOW = ("2026-10-27T00:00:00+00:00", "2026-11-01T00:00:00+00:00")
PAGE = 10000
PAUSE = 0.4  # free tier allows a few calls per second


def api_key() -> str:
    m = re.search(r"^ETHERSCAN_API_KEY=(\S+)", (ROOT / ".env").read_text(), re.M)
    if not m:
        raise SystemExit("ETHERSCAN_API_KEY missing in .env")
    return m.group(1)


def call(key: str, **params):
    for attempt in range(5):
        time.sleep(PAUSE * (attempt + 1))
        r = requests.get(API, params={"chainid": 1, "apikey": key, **params}, timeout=30)
        body = r.json()
        result = body.get("result")
        if body.get("status") == "1":
            return result
        msg = f"{body.get('message')} {result if isinstance(result, str) else ''}".lower()
        if "no transactions found" in msg or "no records found" in msg:
            return []
        if "rate limit" in msg:
            continue
        raise RuntimeError(f"Etherscan error for {params.get('action')}: {msg.strip()}")
    raise RuntimeError("Etherscan rate limit: gave up after retries")


def block_at(key: str, iso: str, closest: str) -> int:
    ts = int(datetime.fromisoformat(iso).timestamp())
    return int(call(key, module="block", action="getblocknobytime", timestamp=ts, closest=closest))


def main():
    key = api_key()
    CACHE.mkdir(parents=True, exist_ok=True)
    manifest_path = CACHE / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    if "blocks" not in manifest:
        manifest["window"] = WINDOW
        manifest["blocks"] = [block_at(key, WINDOW[0], "after"), block_at(key, WINDOW[1], "before")]
    start, end = manifest["blocks"]
    manifest.setdefault("truncated", [])

    hop2 = "--hop2" in sys.argv
    with open(ROOT / "data/seeds.csv", newline="") as f:
        seed_set = {row["address"] for row in csv.DictReader(f)}
    if hop2:
        # Neighbours of the seeds, taken from the hop-1 edges (no labels involved).
        with open(ROOT / "data/edges.csv", newline="") as f:
            rows = list(csv.DictReader(f))
        seeds = sorted({x for r in rows for x in (r["from"], r["to"])} - seed_set)
        out_path = ROOT / "data/edges_hop2.csv"
    else:
        seeds = sorted(seed_set)
        out_path = ROOT / "data/edges.csv"

    edges = []
    for i, addr in enumerate(seeds, 1):
        path = CACHE / f"{addr}.json"
        if path.exists():
            responses = json.loads(path.read_text())
        else:
            responses = {}
            for action in KINDS:
                res = call(key, module="account", action=action, address=addr,
                           startblock=start, endblock=end, page=1, offset=PAGE, sort="asc")
                responses[action] = res
                if len(res) >= PAGE:
                    manifest["truncated"].append(f"{addr}:{action}")
            path.write_text(json.dumps(responses))
            print(f"[{i}/{len(seeds)}] {addr} " + " ".join(f"{a}={len(v)}" for a, v in responses.items()), flush=True)
        edges.extend(normalise(responses))

    # The same transfer appears in the files of both endpoints when two seeds trade with each other.
    unique = {(e["tx_hash"], e["kind"], e["from"], e["to"], e["asset"], e["value"]): e for e in edges}
    edges = sorted(unique.values(), key=lambda e: (e["block"], e["tx_hash"]))
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(edges)

    tag = "hop2" if hop2 else "hop1"
    manifest[f"fetched_at_{tag}"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest[f"n_addresses_{tag}"] = len(seeds)
    manifest[f"n_edges_{tag}"] = len(edges)
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"edges={len(edges)} blocks={start}-{end} truncated={len(manifest['truncated'])}")


if __name__ == "__main__":
    main()
