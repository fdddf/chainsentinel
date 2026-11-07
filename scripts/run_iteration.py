"""Run one rule and score it.

Usage: python scripts/run_iteration.py <N> <rule_module> ["note"]
e.g.   python scripts/run_iteration.py 0 baseline "1-hop neighbours, no filtering"

The rule module lives in src/chainsentinel/rules/ and exposes rank(edges, seeds) -> list[str].
It receives only data/seeds.csv and the fetched edges (data/edges.csv, data/edges_hop{2,3,4}.csv),
never the holdout or the labels.
A rule that sets USES_CANDIDATE_EDGES = True also gets data/edges_cand.csv.
Writes results/candidates_iter_N.csv and results/iter_N.json (dev metrics only).
"""

import csv
import importlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from chainsentinel.edges import cache_exists, open_text
from chainsentinel.evaluate import read_addresses, score_file

ROOT = Path(__file__).parents[1]


def load_edges(candidate_edges: bool = False):
    rows = []
    names = ["edges.csv", "edges_hop2.csv", "edges_hop3.csv", "edges_hop4.csv"]
    if candidate_edges:  # own activity of earlier candidates (scripts/fetch_candidates.py)
        names.append("edges_cand.csv")
    for name in names:
        path = ROOT / "data" / name
        if cache_exists(path):
            with open_text(path) as f:
                rows.extend(csv.DictReader(f))
    for r in rows:
        r["value"] = float(r["value"])
        r["timestamp"] = int(r["timestamp"])
        r["block"] = int(r["block"])
    return rows


def main():
    n, rule = int(sys.argv[1]), sys.argv[2]
    note = sys.argv[3] if len(sys.argv) > 3 else ""
    module = importlib.import_module(f"chainsentinel.rules.{rule}")
    edges = load_edges(getattr(module, "USES_CANDIDATE_EDGES", False))
    ranking = module.rank(edges, set(read_addresses(ROOT / "data/seeds.csv")))

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
