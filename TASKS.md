# Tasks

Highest priority first.
Move finished tasks to the bottom with the commit hash.

## Open

1. **Iteration 3: one more hop for the 48% of dev that siblings cannot reach.**
   Parents (paid ≥ 1 ETH to ≥ 2 seed funders) → uncles → cousins; `fetch_seeds.py --hop3/--hop4`, cached, service guard.
   Goal: raise recall@all above 0.523 without dropping recall@50 below iteration 2.
2. **Iteration 4: sinks.** Every seed edge points into the seed; no seed sent anything before 2026-11-01.
   Fetch the top candidates' own activity (expansion from the rule's own candidates)
   and demote candidates that sent funds out in the window (distributors, pass-throughs, exchange deposits).
3. **Service-address filter** (partly done by the truncation guard in `--hop3`).
4. **Ablation and sensitivity**: rerun the best rule with `seed=1..5` to show variance of recall (if time).
5. **Final** (from 16:00 at the latest): `python scripts/final_report.py` → `results/final.json`,
   `results/recall_by_iteration.png`; README "Results" section with table, links and limits.

## Done

- Ground truth parsed from the archived FBI alert: 608 ETH, 19 BTC, 1 SOL (`data/labels.csv`).
- Fixed split: 122 seeds, 486 held out (`data/seeds.csv`, `data/holdout.csv`).
- Evaluation with tests (`src/chainsentinel/evaluate.py`, `tests/`).
- Seed data fetched (hop 1: 244 edges) and funders fetched (hop 2: 8530 edges) — 634bd28, 7cbbcf5.
- Iteration 0 baseline: dev recall 0 — 634bd28.
- Iteration 1 siblings: dev recall@50 0.074, recall@all 0.523 — 7cbbcf5.
- Ceiling analysis: split-agnostic expected max of dev recall@50 ≈ 0.103 — 5702507.
- Iteration 2 similarity: dev recall@50 0.095, recall@all 0.523 — 5702507.
