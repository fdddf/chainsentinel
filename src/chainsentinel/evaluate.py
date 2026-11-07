"""Score a ranked candidate list against the held-out FBI addresses.

This is the only module that may read data/holdout.csv.
Rules must never see it, otherwise the evaluation is leaked.

The held-out set is split once, by address hash, into
- dev:  the loop may look at its metrics and misses to design the next rule;
- test: reported only with --final, to check that progress on dev is not overfitting.

Precision is reported as a *lower bound* (precision_lb@k):
an address absent from the FBI list is unlabelled, not proven benign.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path

DEFAULT_KS = (10, 50, 100, 200)
ROOT = Path(__file__).parents[2]


def evaluate(ranking, holdout, seeds, ks=DEFAULT_KS) -> dict:
    holdout = {a.lower() for a in holdout}
    seeds = {a.lower() for a in seeds}
    ranked, seen = [], set()
    for a in ranking:
        a = a.lower()
        if a in seeds or a in seen:
            continue
        seen.add(a)
        ranked.append(a)

    m = {"n_candidates": len(ranked), "n_holdout": len(holdout)}
    for k in ks:
        hits = sum(1 for a in ranked[:k] if a in holdout)
        m[f"hits@{k}"] = hits
        m[f"recall@{k}"] = hits / len(holdout) if holdout else 0.0
        m[f"precision_lb@{k}"] = hits / k
    m["recall@all"] = sum(1 for a in ranked if a in holdout) / len(holdout) if holdout else 0.0
    return m


def split_holdout(holdout) -> tuple[list[str], list[str]]:
    dev, test = [], []
    for a in sorted({a.lower() for a in holdout}):
        (dev if hashlib.sha256(a.encode()).digest()[0] % 2 == 0 else test).append(a)
    return dev, test


def read_addresses(path: Path) -> list[str]:
    with open(path, newline="") as f:
        return [row["address"].lower() for row in csv.DictReader(f)]


def score_file(candidates: Path, final: bool = False) -> dict:
    ranking = read_addresses(candidates)
    seeds = read_addresses(ROOT / "data/seeds.csv")
    dev, test = split_holdout(read_addresses(ROOT / "data/holdout.csv"))
    out = {"dev": evaluate(ranking, dev, seeds)}
    if final:
        out["test"] = evaluate(ranking, test, seeds)
    # Diagnostics for reflection: only dev labels are revealed.
    dev_set = set(dev)
    found = [a for a in ranking if a in dev_set]
    out["dev_hits_top"] = found[:20]
    out["dev_missed_sample"] = sorted(dev_set - set(ranking))[:20]
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("candidates", type=Path)
    p.add_argument("--final", action="store_true", help="also report the test split")
    args = p.parse_args(argv)
    out = score_file(args.candidates, final=args.final)
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
