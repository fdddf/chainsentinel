# Journal

Every result, decision and exchange, newest last.
Times are CET.

## 2026-11-07

**12:58 — Problem framed.**
The FBI alert of 2026-10-31 lists 628 addresses "holding or have held assets from the theft" of 2026-10-29 at Binance.
Question: from 20% of the 608 Ethereum addresses as seeds,
how many of the other 80% can explainable heuristics on public transaction data recover?
Ethereum only, because 608 of 628 addresses are on Ethereum and the FBI reports the stolen assets were converted mainly into ETH.

**13:00 — Ground truth.**
fbi.gov returned HTTP 403 to scripted requests,
so the alert was taken from the Wayback Machine snapshot of 2026-11-07 06:00 UTC
and committed to `data/raw/`.
Parsed counts match press coverage: 608 ETH, 19 BTC, 1 SOL.
Test: `tests/test_labels.py`.

**13:02 — Split and evaluation fixed before any rule exists.**
`seed=42`, 20% → 122 seeds, 486 held out.
Metrics: `recall@k` and `precision_lb@k`.
Precision is a lower bound because unlisted addresses are unlabelled, not benign.
Seeds are removed from every ranking before scoring.
Tests: `tests/test_split.py`, `tests/test_evaluate.py`.

**Known biases, recorded before seeing any result:**
- The FBI list is itself the product of tracing by investigators,
  likely by the same kind of fund-flow following we test.
  High recall may partly mean "we re-derived their method", not "we found hidden actors".
- The list is a snapshot of 2026-10-31; addresses used later are absent and would count as false positives.
- One incident, one actor, one chain. No claim of generality.

**13:12 — Held-out set split into dev and test.**
To avoid tuning rules on the numbers we report,
`chainsentinel.evaluate` splits the 486 held-out addresses by SHA-256 into dev (243) and test (243).
Rules are designed looking only at dev; test is scored once at the end with `--final`.
Test: `test_holdout_split_is_stable_disjoint_and_balanced`.

**13:20 — Seed data fetched.**
`scripts/fetch_seeds.py`, Etherscan API V2, blocks 26280314–26316188 (2026-10-27 to 2026-11-01 UTC).
122 seeds × (txlist, txlistinternal, tokentx), nothing truncated.
244 edges, see `data/edges.csv` and `data/raw/etherscan/manifest.json`.

Observations before any rule:
- **All 244 edges point into a seed. No seed sent anything before 2026-11-01.**
  Matches the FBI wording "holding or have held": in this window the listed addresses are sinks.
- All activity is between 2026-10-30 05:32 and 2026-10-31 17:40 UTC, one to two days after the theft.
- 118 distinct funders; 22 of them funded more than one seed; the largest funded 23 seeds.
- **All 64 ERC-20 rows are tokens with the symbol "ETH"** from 26 different contracts,
  and every one mirrors a real ETH transfer with the same from, to and value.
  We read this as spoofed fake-token events (address-poisoning spam),
  whose `from` field the token contract can forge. Not yet filtered.

**13:21 — Iteration 0 (baseline): recall 0.**
Rule: 1-hop neighbours of seeds, either direction, ranked by distinct seeds touched (`rules/baseline.py`).
Dev: 118 candidates, 0 hits; recall@50 = recall@all = 0 (`results/iter_0.json`).
Interpretation: the funders of the seeds are not on the dev list.
The list appears to name holding addresses, not the distributors that filled them.
Next hypothesis (iteration 1): **siblings** — other addresses paid by the same funders in the same window
are likely to be listed. Requires fetching the funders' outgoing transfers.

**13:27 — Hop 2 fetched.**
`scripts/fetch_seeds.py --hop2`: the 118 neighbours of the seeds (all funders), same window.
8530 edges in `data/edges_hop2.csv`, nothing truncated.
Note: `run_iteration.py` now loads hop-1 and hop-2 edges; iteration 0 was scored on hop-1 only.

**13:27 — Iteration 1 (siblings): first signal.**
Hypothesis: listed addresses are holding wallets filled in batches;
other recipients of the same funders are likely in the same batch.
Rule `rules/siblings.py`: score = Σ over funders of (seeds paid / recipients paid); native ETH only, spoofed tokens ignored.
Dev (243 addresses), `results/iter_1.json`:

| k | hits | recall@k | precision_lb@k |
|---|---|---|---|
| 10 | 6 | 0.025 | 0.60 |
| 50 | 18 | 0.074 | 0.36 |
| 100 | 43 | 0.177 | 0.43 |
| 200 | 76 | 0.313 | 0.38 |
| all (482) | 127 | 0.523 | — |

Beats iteration 0 (recall 0 everywhere), so the first goal condition is met on dev.
Ceiling: 48% of dev addresses are not paid by any seed funder in the window,
so no reordering of these 482 candidates can find them; reaching them needs another hop or a wider window.
Precision_lb@10 of 0.60 but only 0.36 at 50: the top of the ranking is diluted.
Next: re-rank siblings by similarity to the seeds' own funding (amount band, time of the batch).

**13:33 — Handover to a fresh Claude Code session.**
PROMPT.md goal raised to dev recall@50 ≥ 0.15 (or 3 documented failures), plus final test scoring, plot and README, time-boxed to 16:00.
TASKS.md reordered: iteration 2 (amount/time similarity), iteration 3 (another hop).

**13:36 — Session 2 starts. Goal: dev recall@50 ≥ 0.15, or 3 documented failures; final scoring, plot and README by 16:00.**

**13:37 — Exploration of the funding pattern (seeds and funder edges only, no labels).**
- 180 payments into seeds, all `normal` transactions; 18 of them are zero-value.
  Every seed also has at least one payment > 0.
- Median non-dust seed payment is about 30 ETH; 75th percentile 64 ETH.
- More than half of the funders' payments to non-seeds are zero or dust (< 0.01 ETH).
- Several "funders" are vanity look-alikes of real funders,
  e.g. `0x747ad856…a44e` imitating `0x747af825…a44e`, sending dust to the same recipients.
  This is address poisoning: the dust sender copies the first and last characters of a real counterparty.
  Their recipients overlap the real funder's, so they add noise to the funder weights rather than new reach.

**13:37 — A ceiling on dev recall@50, derived before any further rule.**
`recall@k` on dev counts only dev addresses as hits.
Dev and test are halves of the held-out set split by SHA-256 of the address,
which no rule can see, so a listed candidate is in dev with probability 243/486 = 0.5.
Even a perfect "is it on the FBI list?" ranking therefore expects about 25 dev hits in its top 50:
**expected ceiling recall@50 ≈ 25/243 ≈ 0.103** for any rule that does not use the split.
Reaching 0.15 needs ≥ 37 dev addresses in 50 listed ones; P(Binomial(50, 0.5) ≥ 37) ≈ 0.0005.
The goal threshold of 0.15 is therefore not reachable by an honest rule,
and the session will be judged by the alternative condition (documented failures).
What can still improve is (a) how close the top of the ranking gets to 0.103
and (b) reach, measured by recall@all, which has no such cap.
The same effect makes dev `precision_lb@k` a lower bound twice over: test-listed candidates count as misses on dev.
Combined dev+test precision is reported only once, at the final scoring.

**13:38 — Prototype variants scored on dev (all recorded, to make the selection visible).**
Script `/tmp` prototype of the sibling rule with optional dust filter, amount similarity and time similarity:

| variant | r@10 | r@50 | r@100 | r@all |
|---|---|---|---|---|
| iteration 1 as is | 0.025 | 0.074 | 0.177 | 0.523 |
| drop < 0.01 ETH | 0.004 | 0.078 | 0.193 | 0.523 |
| drop < 0.1 ETH | 0.004 | 0.082 | 0.189 | 0.523 |
| drop < 1 ETH | 0.012 | 0.086 | 0.202 | 0.523 |
| drop < 5 ETH | 0.012 | 0.086 | 0.202 | 0.510 |
| amount similarity | 0.021 | 0.086 | 0.198 | 0.523 |
| drop < 0.01 + amount similarity | 0.008 | 0.095 | 0.210 | 0.523 |
| time similarity (6 h scale) | 0.025 | 0.070 | 0.173 | 0.523 |
| drop < 0.01 + time similarity | 0.012 | 0.078 | 0.193 | 0.523 |
| drop < 0.01 + amount + time | 0.016 | 0.086 | 0.210 | 0.523 |
| drop < 1 + amount + time | 0.021 | 0.086 | 0.210 | 0.523 |

11 variants were compared on dev, so the best one is selected on dev and its dev number is optimistic.
Time similarity does not help: the whole batch happened within 36 hours, so time does not separate recipients.

**Hypothesis, iteration 2 (`rules/similarity.py`):**
holding wallets were filled with tens of ETH; dust and zero-value transfers are poisoning.
Dropping payments < 0.01 ETH (also from the funder weights)
and weighting each sibling payment by how close its amount is (in log10) to the same funder's seed payments
should move holding wallets up. Expected: recall@50 near the 0.103 ceiling, recall@all unchanged at 0.523.

**Hypothesis, iteration 3 (another hop, for reach):**
14 addresses paid ≥ 1 ETH to ≥ 2 seed funders ("parents"; the top three paid 22, 20 and 14 funders).
Their other recipients ("uncles") are likely distributors of the same batch,
and the uncles' recipients ("cousins") are likely the 48% of dev the siblings cannot reach.
Needs two fetch levels (`--hop3` parents, `--hop4` uncles), capped and with a service guard.

**13:39 — Iteration 2 (similarity): recall@50 0.074 → 0.095, still below 0.15 (failure 1 of 3).**
Rule `rules/similarity.py`, tests `tests/test_similarity.py` (written first, failed, then passed).
Dev, `results/iter_2.json` (precision is a lower bound):

| k | hits | recall@k | precision_lb@k |
|---|---|---|---|
| 10 | 2 | 0.008 | 0.20 |
| 50 | 23 | 0.095 | 0.46 |
| 100 | 51 | 0.210 | 0.51 |
| 200 | 98 | 0.403 | 0.49 |
| all (331) | 127 | 0.523 | — |

The dust filter cuts the candidates from 482 to 331 without losing a dev hit,
and recall@50 and recall@100 improve, while the top 10 gets worse (6 → 2 hits).
**Why it fails the 0.15 goal:** 23 dev hits in 50 is 92% of the expected split-agnostic ceiling (about 25).
The top 20 candidates that are not in dev each got one payment of 13 to 200 ETH (mostly 20 to 85) from a seed funder,
13 of them from `0xfef67e…`, which paid 12 seeds.
They look like the same batches as the seeds. Many are probably on the test half,
and nothing in the transaction data could tell them apart from the dev hits.
Ranking is close to saturated; the remaining lever is reach (iteration 3).
