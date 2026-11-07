"""Fetch 1-hop Ethereum activity of the seed addresses from Etherscan API V2.

Window: 2026-10-27 00:00 UTC to 2026-11-01 00:00 UTC
(two days before the theft up to the day the FBI list was published).

Raw responses are cached in data/raw/etherscan/<address>.json and reused,
so re-running only fetches what is missing.
Writes data/edges.csv and data/raw/etherscan/manifest.json.

Usage: python scripts/fetch_seeds.py [--hop2 | --hop3 | --hop4]   (needs ETHERSCAN_API_KEY in .env)
  --hop2  fetch the neighbours of the seeds instead, into data/edges_hop2.csv
  --hop3  fetch the "parents": non-seed addresses that paid >= 1 ETH (native) to at least
          two distinct funders (funder = sender of >= 1 ETH native to a seed),
          from hop-1 and hop-2 edges, into data/edges_hop3.csv
  --hop4  fetch the "uncles": recipients of >= 1 ETH native from the parents
          (excluding seeds, funders, parents and already cached addresses),
          into data/edges_hop4.csv

Service guard: an address whose response for any action is truncated
(more than MAX_ROWS rows, after paging) is listed in manifest["services"] and is not expanded from in --hop4.
Known routers in SKIP_PARENTS are never used as parents.
At most MAX_UNCLES uncles are fetched, those that received the most ETH from parents.
No labels are read: expansion starts from the seeds only.
"""

import csv
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from chainsentinel.edges import FIELDS, KINDS, cache_exists, normalise, open_text, read_cache

ROOT = Path(__file__).parents[1]
CACHE = ROOT / "data/raw/etherscan"
API = "https://api.etherscan.io/v2/api"
WINDOW = ("2026-10-27T00:00:00+00:00", "2026-11-01T00:00:00+00:00")
PAGE = 1000  # the API returns at most 1000 rows per call
WINDOW_ROWS = 10000  # and at most page * offset = 10000 rows per block range
MAX_ROWS = 50000  # per address and action; beyond this the address is a service
PAUSE = 0.4  # free tier allows a few calls per second
MIN_ETH = 1.0  # payments below this are dust/poisoning, not funding
SKIP_PARENTS = {"0x1231deb6f5749ef6ce6943a275a1d3e7486f4eae"}  # LI.FI router
MAX_UNCLES = 600
N_CALLS = 0


def api_key() -> str:
    m = re.search(r"^ETHERSCAN_API_KEY=(\S+)", (ROOT / ".env").read_text(), re.M)
    if not m:
        raise SystemExit("ETHERSCAN_API_KEY missing in .env")
    return m.group(1)


def call(key: str, **params):
    global N_CALLS
    for attempt in range(5):
        N_CALLS += 1
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


def fetch_all(key: str, action: str, addr: str, start: int, end: int) -> tuple[list, bool]:
    """All rows for one address and action in [start, end], paging and then
    restarting from the last block seen when a block range holds more than WINDOW_ROWS.
    Returns (rows, truncated)."""
    rows, seen, lo = [], set(), start
    while True:
        batch = []
        for page in range(1, WINDOW_ROWS // PAGE + 1):
            res = call(key, module="account", action=action, address=addr,
                       startblock=lo, endblock=end, page=page, offset=PAGE, sort="asc")
            batch.extend(res)
            if len(res) < PAGE:
                break
        for r in batch:
            k = json.dumps(r, sort_keys=True)
            if k not in seen:
                seen.add(k)
                rows.append(r)
        if len(batch) < WINDOW_ROWS:
            return rows, False
        if len(rows) >= MAX_ROWS:
            return rows, True
        last = int(batch[-1]["blockNumber"])
        if last == lo:  # one block holds more than WINDOW_ROWS rows
            return rows, True
        lo = last


def block_at(key: str, iso: str, closest: str) -> int:
    ts = int(datetime.fromisoformat(iso).timestamp())
    return int(call(key, module="block", action="getblocknobytime", timestamp=ts, closest=closest))


def read_edges(*names: str) -> list[dict]:
    rows = []
    for name in names:
        with open_text(ROOT / "data" / name) as f:
            rows.extend(csv.DictReader(f))
    return rows


def eth_payments(rows: list[dict]) -> list[dict]:
    """Native ETH transfers of at least MIN_ETH."""
    return [r for r in rows if r["kind"] in ("normal", "internal") and r["asset"] == "ETH"
            and float(r["value"]) >= MIN_ETH]


def funders_of(seed_set: set[str]) -> set[str]:
    pays = eth_payments(read_edges("edges.csv", "edges_hop2.csv"))
    return {r["from"] for r in pays if r["to"] in seed_set}


def parents_of(seed_set: set[str]) -> list[str]:
    funders = funders_of(seed_set)
    paid = {}
    for r in eth_payments(read_edges("edges.csv", "edges_hop2.csv")):
        if r["to"] in funders and r["from"] not in seed_set:
            paid.setdefault(r["from"], set()).add(r["to"])
    return sorted(p for p, fs in paid.items() if len(fs) >= 2 and p not in SKIP_PARENTS)


def uncles_of(seed_set: set[str], manifest: dict) -> list[str]:
    funders = funders_of(seed_set)
    parents = set(parents_of(seed_set))
    services = set(manifest.get("services", []))
    received = {}
    for r in eth_payments(read_edges("edges_hop3.csv")):
        if r["from"] in parents and r["from"] not in services:
            received[r["to"]] = received.get(r["to"], 0.0) + float(r["value"])
    excluded = seed_set | funders | parents
    # Selection must not depend on what is already cached, so that a rerun picks the same uncles
    # (cached ones are then reused by main() instead of being fetched again).
    uncles = [u for u in received if u not in excluded]
    print(f"uncles before cap: {len(uncles)}")
    manifest["n_uncles_before_cap_hop4"] = len(uncles)
    if len(uncles) > MAX_UNCLES:
        uncles = sorted(uncles, key=lambda u: (-received[u], u))[:MAX_UNCLES]
        print(f"capped to the {MAX_UNCLES} uncles that received the most ETH from parents")
    return sorted(uncles)


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

    manifest.setdefault("services", [])
    hop2 = "--hop2" in sys.argv
    tag = next((t for t in ("hop2", "hop3", "hop4") if f"--{t}" in sys.argv), "hop1")
    with open(ROOT / "data/seeds.csv", newline="") as f:
        seed_set = {row["address"] for row in csv.DictReader(f)}
    if tag == "hop3":
        seeds = parents_of(seed_set)
        out_path = ROOT / "data/edges_hop3.csv"
    elif tag == "hop4":
        global MAX_ROWS
        MAX_ROWS = WINDOW_ROWS  # an uncle with more rows than this is treated as a service
        seeds = uncles_of(seed_set, manifest)
        out_path = ROOT / "data/edges_hop4.csv"
    elif hop2:
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
        if cache_exists(path):
            responses = read_cache(path)
        else:
            responses = {}
            for action in KINDS:
                res, truncated = fetch_all(key, action, addr, start, end)
                responses[action] = res
                if truncated:
                    manifest["truncated"].append(f"{addr}:{action}")
                    if addr not in manifest["services"]:
                        manifest["services"].append(addr)
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

    manifest[f"fetched_at_{tag}"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest[f"n_addresses_{tag}"] = len(seeds)
    manifest[f"n_edges_{tag}"] = len(edges)
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"addresses={len(seeds)} api_calls={N_CALLS} edges={len(edges)} blocks={start}-{end} truncated={len(manifest['truncated'])}")


if __name__ == "__main__":
    main()
