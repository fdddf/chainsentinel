"""Rebuild data/labels.csv, data/seeds.csv and data/holdout.csv from the archived FBI alert.

Usage: python scripts/build_labels.py
"""

import csv
from pathlib import Path

from chainsentinel.labels import parse_fbi_alert
from chainsentinel.split import split_seeds

ROOT = Path(__file__).parents[1]
SNAPSHOT = ROOT / "data/raw/fbi_alert_2026-10-31.wayback-20261107060018.html"
SEED_FRAC, SEED = 0.2, 42


def write(path, rows, fields):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main():
    labels = parse_fbi_alert(SNAPSHOT.read_text(encoding="utf-8", errors="replace"))
    write(ROOT / "data/labels.csv", labels, ["chain", "address", "source", "published"])
    eth = [r["address"] for r in labels if r["chain"] == "ETH"]
    seeds, holdout = split_seeds(eth, seed_frac=SEED_FRAC, seed=SEED)
    write(ROOT / "data/seeds.csv", [{"address": a} for a in seeds], ["address"])
    write(ROOT / "data/holdout.csv", [{"address": a} for a in holdout], ["address"])
    print(f"labels={len(labels)} eth={len(eth)} seeds={len(seeds)} holdout={len(holdout)}")


if __name__ == "__main__":
    main()
