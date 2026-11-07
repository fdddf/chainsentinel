"""Recount the headline numbers from the committed files, independently of evaluate.py.

Evaluation-side script: it reads data/labels.csv and data/holdout.csv, which rules never do.
For each iteration it reports how many of the top 50 candidates are FBI-listed,
and the base rate: how many a random order of the same candidate pool would put in the top 50.
The gap between the two is what the ranking adds; the pool itself is what candidate generation adds.

Usage: python scripts/recount.py   -> results/recount.json
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
TOP = 50


def addresses(path, chain=None):
    with open(path, newline="") as f:
        return [r["address"].lower() for r in csv.DictReader(f) if chain is None or r["chain"] == chain]


def main():
    listed = set(addresses(ROOT / "data/labels.csv", chain="ETH"))
    seeds = set(addresses(ROOT / "data/seeds.csv"))
    holdout = set(addresses(ROOT / "data/holdout.csv"))
    out = []
    n = 0
    while (path := ROOT / f"results/candidates_iter_{n}.csv").exists():
        pool = [a for a in addresses(path) if a not in seeds]
        in_pool = sum(a in listed for a in pool)
        share = in_pool / len(pool) if pool else 0.0
        out.append({
            "iteration": n,
            "candidates": len(pool),
            "listed_in_pool": in_pool,
            "listed_share_of_pool": round(share, 3),
            f"listed_in_top{TOP}": sum(a in listed for a in pool[:TOP]),
            f"expected_listed_in_top{TOP}_random_order": round(min(TOP, len(pool)) * share, 1),
            "holdout_reached": len(set(pool) & holdout),
            "holdout_size": len(holdout),
        })
        n += 1
    (ROOT / "results/recount.json").write_text(json.dumps(out, indent=2))
    for r in out:
        print(r)


if __name__ == "__main__":
    main()
