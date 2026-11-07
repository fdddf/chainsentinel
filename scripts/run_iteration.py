"""Run one rule and score it.

Usage: python scripts/run_iteration.py <N> <rule_module> ["note"]
e.g.   python scripts/run_iteration.py 0 baseline "1-hop neighbours, no filtering"

The rule module lives in src/chainsentinel/rules/ and exposes rank(edges, seeds) -> list[str].
It receives only data/edges.csv and data/seeds.csv.
Writes results/candidates_iter_N.csv and results/iter_N.json (dev metrics only).
"""

import csv
import importlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from chainsentinel.evaluate import read_addresses, score_file

ROOT = Path(__file__).parents[1]


def load_edges():
    with open(ROOT / "data/edges.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["value"] = float(r["value"])
        r["timestamp"] = int(r["timestamp"])
        r["block"] = int(r["block"])
    return rows


def main():
    n, rule = int(sys.argv[1]), sys.argv[2]
    note = sys.argv[3] if len(sys.argv) > 3 else ""
    module = importlib.import_module(f"chainsentinel.rules.{rule}")
    ranking = module.rank(load_edges(), set(read_addresses(ROOT / "data/seeds.csv")))

    cand = ROOT / f"results/candidates_iter_{n}.csv"
    with open(cand, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rank", "address"])
        w.writerows(enumerate(ranking, 1))

    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                            capture_output=True, text=True).stdout.strip()
    out = {
        "iteration": n, "rule": rule, "note": note, "code_commit": commit,
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **score_file(cand),
    }
    (ROOT / f"results/iter_{n}.json").write_text(json.dumps(out, indent=2))
    d = out["dev"]
    print(f"iter {n} [{rule}] candidates={d['n_candidates']} "
          f"dev recall@50={d['recall@50']:.3f} recall@200={d['recall@200']:.3f} "
          f"recall@all={d['recall@all']:.3f} precision_lb@50={d['precision_lb@50']:.2f}")


if __name__ == "__main__":
    main()
