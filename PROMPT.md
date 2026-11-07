# Session prompt

Start a new session with:

```
/goal continue the goal described in PROMPT.md
```

## Goal

Find out whether a research loop can recover held-out FBI-listed TraderTraitor addresses
from the 2026-10-29 Binance theft,
starting from a 20% seed sample and using only public Ethereum transaction data
and explainable heuristics.

Done when either:

- `results/iter_*.json` contains an iteration whose `recall@50` beats iteration 0 (the baseline),
  and README.md reports it with links to the files; or
- JOURNAL.md documents at least 4 iterations that failed to beat the baseline, with the reasons,
  and README.md reports that negative result.

## Loop

1. Take the top task in TASKS.md.
2. Run each atomic step in its own subagent.
3. For a new heuristic: read `refs/` for an idea not tried yet,
   write it as a hypothesis in JOURNAL.md,
   write a failing test in `tests/`, then implement it in `src/chainsentinel/rules/`.
4. Produce a ranked candidate list `results/candidates_iter_N.csv` (column `address`)
   using only `data/seeds.csv` and the cached transaction data.
5. Score it only with `python -m chainsentinel.evaluate results/candidates_iter_N.csv`
   and save the output as `results/iter_N.json`.
6. Look at the top false positives and at held-out addresses that were missed,
   write what you learned to JOURNAL.md, and add the next hypothesis to TASKS.md.
7. Update this file if the plan changed. Commit after each finished task.

## Hard rules

- Rules and features must never read `data/holdout.csv` or `data/labels.csv`.
  Only `chainsentinel.evaluate` may read the holdout.
- Never expand the graph from a held-out address because it is held out.
  Expansion starts from seeds and from candidates the rule itself produced.
- Never call an address malicious or attribute control.
  Outputs are "candidates"; an address not on the FBI list is "unlabelled", not benign.
- Precision is a lower bound (`precision_lb@k`). Say so wherever it is reported.
- Keep the seed split fixed (`seed=42`, 20%) so iterations are comparable.
- Never commit API keys. They live in `.env` (see `.env.example`).
- Cache every API response under `data/raw/etherscan/` and commit it,
  so the evaluation can be reproduced offline.
