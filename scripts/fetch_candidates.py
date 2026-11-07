"""Fetch the own activity of a rule's top candidates (expansion from the rule's candidates, never from labels).

Usage: python scripts/fetch_candidates.py results/candidates_iter_N.csv K
Same window, cache and edge format as fetch_seeds.py.
Writes data/edges_cand.csv and data/raw/etherscan/manifest_cand.json
(a separate manifest so it can run alongside fetch_seeds.py).
"""

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import fetch_seeds as fs  # noqa: E402

from chainsentinel.edges import FIELDS, KINDS, cache_exists, normalise, read_cache  # noqa: E402


def main():
    cand_path, k = Path(sys.argv[1]), int(sys.argv[2])
    with open(cand_path, newline="") as f:
        addrs = [r["address"].lower() for r in csv.DictReader(f)][:k]
    start, end = json.loads((fs.CACHE / "manifest.json").read_text())["blocks"]
    key = fs.api_key()
    truncated, edges = [], []
    for i, addr in enumerate(addrs, 1):
        path = fs.CACHE / f"{addr}.json"
        if cache_exists(path):
            responses = read_cache(path)
        else:
            responses = {}
            for action in KINDS:
                rows, trunc = fs.fetch_all(key, action, addr, start, end)
                responses[action] = rows
                if trunc:
                    truncated.append(f"{addr}:{action}")
            path.write_text(json.dumps(responses))
            print(f"[{i}/{len(addrs)}] {addr} " + " ".join(f"{a}={len(v)}" for a, v in responses.items()),
                  flush=True)
        edges.extend(normalise(responses))

    unique = {(e["tx_hash"], e["kind"], e["from"], e["to"], e["asset"], e["value"]): e for e in edges}
    edges = sorted(unique.values(), key=lambda e: (e["block"], e["tx_hash"]))
    with open(fs.ROOT / "data/edges_cand.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(edges)
    manifest = {
        "source": str(cand_path), "top_k": k, "n_addresses": len(addrs), "n_edges": len(edges),
        "truncated": truncated, "api_calls": fs.N_CALLS,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (fs.CACHE / "manifest_cand.json").write_text(json.dumps(manifest, indent=2))
    print(f"edges={len(edges)} calls={fs.N_CALLS} truncated={len(truncated)}")


if __name__ == "__main__":
    main()
