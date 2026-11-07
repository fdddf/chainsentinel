# Tasks

Highest priority first.
Move finished tasks to the bottom with the commit hash.

## Open

1. **Final**: `python scripts/final_report.py` → `results/final.json`, `results/recall_by_iteration.png`;
   README "Results" section with table, links and limits.
2. **Ablation and sensitivity**: rerun the best rule with `seed=1..5` to show variance of recall (next session).
3. **Service filter for candidates**: exchanges such as Binance's hot wallet reach the cousin list (iteration 3); demote them before ranking (next session).
4. **Lift the uncle cap** (600 of 3181) and widen the window past 2026-11-01 for the 31% of dev still unreached (next session).

## Done

- Ground truth parsed from the archived FBI alert: 608 ETH, 19 BTC, 1 SOL (`data/labels.csv`).
- Fixed split: 122 seeds, 486 held out (`data/seeds.csv`, `data/holdout.csv`).
- Evaluation with tests (`src/chainsentinel/evaluate.py`, `tests/`).
- Seed data fetched (hop 1: 244 edges) and funders fetched (hop 2: 8530 edges) — 634bd28, 7cbbcf5.
- Iteration 0 baseline: dev recall 0 — 634bd28.
- Iteration 1 siblings: dev recall@50 0.074, recall@all 0.523 — 7cbbcf5.
- Ceiling analysis: split-agnostic expected max of dev recall@50 ≈ 0.103 — 5702507.
- Iteration 2 similarity: dev recall@50 0.095, recall@all 0.523 — 5702507.
- Iteration 3 cousins: dev recall@all 0.523 → 0.687 — 682b9ba.
- Iteration 4 sinks: dev recall@50 0.095, recall@331 0.523 → 0.576; condition 1 met by three documented failures.
