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

- `results/iter_*.json` contains an iteration whose dev `recall@50` beats iteration 0 (the baseline),
  and README.md reports it with links to the files; or
- JOURNAL.md documents at least 4 iterations that failed to beat the baseline, with the reasons,
  and README.md reports that negative result.

## Loop

1. Take the top task in TASKS.md.
2. Run each atomic step in its own subagent.
3. For a new heuristic: read `refs/` for an idea not tried yet,
   write it as a hypothesis in JOURNAL.md,
   write a failing test in `tests/`, then implement it in `src/chainsentinel/rules/`.
4. Run `python scripts/run_iteration.py N <rule_module> "note"`.
   It gives the rule only `data/edges.csv` and `data/seeds.csv`,
   writes `results/candidates_iter_N.csv` and scores it on the **dev** half of the holdout into `results/iter_N.json`.
5. Look at `dev_hits_top`, `dev_missed_sample` and the top unlabelled candidates,
   write what you learned to JOURNAL.md, and add the next hypothesis to TASKS.md.
6. Compare iterations on dev only. The test half is scored once at the end with
   `python -m chainsentinel.evaluate results/candidates_iter_N.csv --final`
   for every iteration, and reported as is, whether or not it agrees with dev.
7. Update this file if the plan changed. Commit after each finished task.

## Hard rules

- Rules and features must never read `data/holdout.csv` or `data/labels.csv`.
  Only `chainsentinel.evaluate` may read the holdout.
- Never look at test-split addresses or test metrics while designing a rule.
- Never expand the graph from a held-out address because it is held out.
  Expansion starts from seeds and from candidates the rule itself produced.
- Never call an address malicious or attribute control.
  Outputs are "candidates"; an address not on the FBI list is "unlabelled", not benign.
- Precision is a lower bound (`precision_lb@k`). Say so wherever it is reported.
- Keep the seed split fixed (`seed=42`, 20%) so iterations are comparable.
- Never commit API keys. They live in `.env` (see `.env.example`).
- Cache every API response under `data/raw/etherscan/` and commit it,
  so the evaluation can be reproduced offline.
