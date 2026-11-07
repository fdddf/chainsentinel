"""Score a ranked candidate list against the held-out FBI addresses.

This is the only module that may read data/holdout.csv.
Rules must never see it, otherwise the evaluation is leaked.

Precision is reported as a *lower bound* (precision_lb@k):
an address absent from the FBI list is unlabelled, not proven benign.
"""

import csv
import json
import sys
from pathlib import Path

DEFAULT_KS = (10, 50, 100, 200)


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


def _read_addresses(path: Path) -> list[str]:
    with open(path, newline="") as f:
        return [row["address"] for row in csv.DictReader(f)]


def main(argv=None):
    """python -m chainsentinel.evaluate results/candidates_iter_N.csv"""
    argv = argv or sys.argv[1:]
    root = Path(__file__).parents[2]
    ranking = _read_addresses(Path(argv[0]))
    m = evaluate(
        ranking,
        holdout=_read_addresses(root / "data/holdout.csv"),
        seeds=_read_addresses(root / "data/seeds.csv"),
    )
    print(json.dumps(m, indent=2))
    return m


if __name__ == "__main__":
    main()
