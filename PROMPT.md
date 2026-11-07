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

Status (2026-11-07 14:52 CET): **goal met by the alternative condition.**
Iterations 2 (`similarity`), 3 (`cousins`) and 4 (`sinks`) all stayed at dev recall@50 = 0.095.
JOURNAL.md records each with its reason: recall@50 per half has an expected ceiling of ≈ 0.103,
because no rule can see the dev/test split. 49 of the top 50 are FBI-listed.
Reach rose from recall@all 0.523 to 0.687 (dev) and 0.724 (test).
Final scores are in `results/final.json`, the plot in `results/recall_by_iteration.png`, and the write-up in the README "Results" section.
A next session should start from TASKS.md: seed variance, a service filter, the uncle cap and the window,
and recall@k on the whole held-out set.

Done when **all** of these hold:

1. Either an iteration ≥ 2 reaches dev `recall@50` ≥ 0.15 (about double iteration 1),
   or JOURNAL.md documents at least 3 further iterations that failed to, each with the reason.
2. Every iteration has been scored once on test with `--final`, and the numbers are in `results/final.json`.
3. `results/recall_by_iteration.png` plots dev and test recall@50 and recall@all per iteration.
4. README.md "Results" section reports the table, links the files, and states the limits.

**Time box:** stop starting new iterations at 16:00 CET on 2026-11-07
and go straight to items 2–4; the submission deadline is 17:00.

## Environment

- Run Python through the project venv: `.venv/bin/python`, `.venv/bin/pytest`.
- Data for rules: `data/edges.csv` (hop 1, into seeds), `data/edges_hop2.csv` (funders), `data/edges_hop3.csv.gz` (parents),
  `data/edges_hop4.csv` (uncles), `data/edges_cand.csv.gz` (own activity of top candidates, only for rules with `USES_CANDIDATE_EDGES`).
  More data: `scripts/fetch_seeds.py`, `scripts/fetch_candidates.py` (need `.env`); cache every response; gzip files over 50 MB.

## Loop

1. Take the top task in TASKS.md.
2. Run each atomic step in its own subagent.
3. For a new heuristic: read `refs/` for an idea not tried yet,
   write it as a hypothesis in JOURNAL.md,
   write a failing test in `tests/`, then implement it in `src/chainsentinel/rules/`.
4. Run `python scripts/run_iteration.py N <rule_module> "note"`.
   It gives the rule only the seeds and the fetched edges (never holdout or labels),
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
