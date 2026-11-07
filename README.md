# ChainSentinel

A research loop that asks:
**given a few addresses that law enforcement tied to a theft,
how many of the other addresses can be recovered from public on-chain data alone?**

Built at the [Claude Impact Lab x Foresight Institute](https://luma.com/claude-wmbq), Berlin, 2026-11-07.

## Open problem

On 2026-10-29, more than $6 billion in crypto assets were stolen from Binance.
On 2026-10-31 the FBI attributed the theft to North Korea's TraderTraitor
and published 628 addresses holding or having held the stolen assets
(608 Ethereum, 19 Bitcoin, 1 Solana).

Tracing such funds is done mostly with closed commercial tools,
and there are few public, reproducible benchmarks for how well open heuristics do.
This repository turns the FBI list into one:

- 20% of the 608 Ethereum addresses are given to the loop as **seeds** (122 addresses, `seed=42`);
- the other 80% are **held out** (486 addresses) and only used for scoring;
- the loop proposes heuristics, ranks candidate addresses, and is scored by `recall@k` on the held-out set.

The result can be checked by computation:
every number in `results/` is produced by `chainsentinel.evaluate` from committed data.

## The loop

| Step | What happens | Where |
|---|---|---|
| Read | Pick an untested heuristic from the literature and incident reports | `refs/README.md` |
| Hypothesise | Write it down before running anything | `JOURNAL.md` |
| Test first | Write a failing test showing how the rule is used | `tests/` |
| Run | Rank candidates from the seeds and the cached transaction graph | `src/chainsentinel/rules/` |
| Check | Score against the held-out addresses | `src/chainsentinel/evaluate.py`, `results/iter_N.json` |
| Reflect | Inspect misses and top unlabelled candidates, queue the next idea | `JOURNAL.md`, `TASKS.md` |

State lives in files (`PROMPT.md`, `TASKS.md`, `JOURNAL.md`),
so the loop survives restarts:
`/goal continue the goal described in PROMPT.md`.

## Results

*In progress.* See `results/` and `JOURNAL.md`.

## Limits

- **Precision is a lower bound.**
  An address missing from the FBI list is unlabelled, not innocent;
  we report `precision_lb@k`.
- **Circularity.**
  The FBI list was itself produced by tracing funds.
  High recall may mean we re-derived the investigators' method, not that we found anything new.
- **Snapshot.**
  The list is from 2026-10-31; addresses used afterwards are absent.
- **Scope.**
  One incident, one actor, Ethereum only.
- **No attribution.**
  This tool ranks addresses for review.
  It does not establish who controls an address and must not be used to accuse anyone.

## How to run

```shell
python -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
pytest                                   # labels, split and evaluation tests
python scripts/build_labels.py           # rebuild data/*.csv from the archived FBI alert
python -m chainsentinel.evaluate results/candidates_iter_0.csv
```

Fetching new transaction data needs an Etherscan API key in `.env` (see `.env.example`).
Evaluating the committed results needs no key.

## Data and sources

- FBI alert of 2026-10-31, archived by the Wayback Machine on 2026-11-07:
  `data/raw/fbi_alert_2026-10-31.wayback-20261107060018.html`.
  A work of the US federal government.
- Ethereum transaction data from the Etherscan API, cached in `data/raw/etherscan/`.
- All data is public. No private or personal data is used.

## License

Code: [Apache 2.0](LICENSE). Text: [CC BY 4.0](LICENSE-CC-BY-4.0).
Donated to [Foresight Institute](https://foresight.org/) as part of the Claude Impact Lab.
