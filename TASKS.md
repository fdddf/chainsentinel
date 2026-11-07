# Tasks

Highest priority first.
Move finished tasks to the bottom with the commit hash.

## Open

1. **Fetch 1-hop data for the seeds.**
   For each address in `data/seeds.csv`, fetch normal transactions (`txlist`), internal transactions and ERC-20 transfers (`tokentx`)
   from Etherscan API V2 (`chainid=1`), limited to the window 2026-10-27 to 2026-11-05.
   Cache raw JSON in `data/raw/etherscan/`, write a normalised edge list `data/edges.csv`
   (`tx_hash, block, timestamp, from, to, asset, value, kind`).
   Respect the free-tier rate limit.
2. **Iteration 0: baseline.**
   Rank every 1-hop counterparty of the seeds by the total value it received from seeds.
   Evaluate and write `results/iter_0.json`.
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
