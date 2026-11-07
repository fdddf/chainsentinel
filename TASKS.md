# Tasks

Highest priority first.
Move finished tasks to the bottom with the commit hash.

## Open

1. **Iteration 2: re-rank siblings by similarity to the seeds' own funding.**
   Seeds were funded 2026-10-30 05:32 to 10-31 17:40 UTC with tens of ETH each.
   Weight sibling payments by closeness in amount and time to the seed payments of the same funder.
   Goal: raise dev recall@50 above 0.074 (iteration 1).
2. **Iteration 3: one more hop for the 48% of dev that siblings cannot reach.**
   Funders of the funders, or a longer window (to 2026-11-07); cache and journal the extra API calls.
3. **Service-address filter.**
   Mark high-degree counterparties (exchanges, routers, bridges, swap services) and stop expansion there.
   Measure how the filter changes the baseline.
4. **Heuristic from refs: fan-out / peel chain.**
   Candidates receiving from seeds within N minutes of the seed being funded, with similar amounts.
5. **Heuristic from refs: fast pass-through.**
   Addresses with no history before the window that receive and forward most of their balance within a short time.
6. **2-hop expansion** from the best-ranked candidates of the best rule so far (capped).
7. **Ablation and sensitivity**: rerun the best rule with `seed=1..5` to show variance of recall.
8. **Plot** recall@k per iteration to `results/recall_by_iteration.png`.
9. **README results section**: findings, failures, limits, next steps.

## Done

- Ground truth parsed from the archived FBI alert: 608 ETH, 19 BTC, 1 SOL (`data/labels.csv`).
- Fixed split: 122 seeds, 486 held out (`data/seeds.csv`, `data/holdout.csv`).
- Evaluation with tests (`src/chainsentinel/evaluate.py`, `tests/`).
- Seed data fetched (hop 1: 244 edges) and funders fetched (hop 2: 8530 edges) — 634bd28, 7cbbcf5.
- Iteration 0 baseline: dev recall 0 — 634bd28.
- Iteration 1 siblings: dev recall@50 0.074, recall@all 0.523 — 7cbbcf5.
