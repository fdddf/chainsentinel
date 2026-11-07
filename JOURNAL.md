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

**13:45–14:22 — Hop 3 (parents) and hop 4 (uncles) fetched.** `fetch_seeds.py --hop3`, `--hop4`.
- **Bug found and fixed while fetching:** Etherscan returns at most 1000 rows per call, not 10000,
  so the old truncation check (`≥ 10000`) could never fire.
  It now pages 1000 at a time and continues from the last block seen;
  an action is truncated (and its address marked a service) past 50 000 rows (10 000 in `--hop4`).
  The hop-1 and hop-2 caches are unaffected: no file there reaches 1000 rows.
- Parents: 14 addresses paid ≥ 1 ETH to ≥ 2 seed funders; LI.FI's router was skipped,
  13 fetched (418 076 edges). `0x0cef320d…` and `0x23617e59…` were truncated and are marked as services, not expanded.
- Uncles: 3181 recipients of ≥ 1 ETH from parents; **capped to the 600 that received the most** (each ≥ 14.5 ETH).
  4 of them are services (Uniswap v4 PoolManager, WETH, LI.FI, `0x3d90f66b…`).
  225 083 edges, 1973 API calls, no errors.
- Size: the cache grew to 656 MB, with one 226 MB file. Every file over 50 MB is now committed gzipped
  (`*.json.gz`, `edges_hop3.csv.gz`); `chainsentinel.edges.open_text` reads either form,
  and iteration 3 reproduces exactly from the gzipped data.

**14:24 — Iteration 3 (cousins): reach 0.523 → 0.687; recall@50 unchanged at 0.095 (failure 2 of 3).**
Rule `rules/cousins.py`, tests `tests/test_cousins.py` (written first, failed at import, then passed).
Siblings keep their iteration-2 order (ranks 1–331); 1660 cousins follow,
scored by parent focus × how much the uncle pays like a seed funder × the payment's fit to the seeds' interquartile amount band.
Dev, `results/iter_3.json` (precision is a lower bound):

| k | hits | recall@k | precision_lb@k |
|---|---|---|---|
| 50 | 23 | 0.095 | 0.46 |
| 200 | 98 | 0.403 | 0.49 |
| 331 (end of siblings) | 127 | 0.523 | 0.38 |
| 500 | 155 | 0.638 | 0.31 |
| 1000 | 167 | 0.687 | 0.17 |
| all (1991) | 167 | 0.687 | — |

40 dev addresses that no seed funder paid are now reached, 28 of them in the first 169 cousins.
**Why it fails the 0.15 goal:** the iteration was aimed at reach, and siblings are ranked first by construction,
so the top 50 cannot change. Even interleaving would not help, because the top 50 is already near the ~0.103 ceiling.
Still out of reach: 76 dev addresses (31%).
They may hang off the 2581 uncles cut by the cap, behind the two parents marked as services,
or be funded outside the 2026-10-27 to 11-01 window.

**14:25–14:48 — Own activity of the top candidates fetched** (`scripts/fetch_candidates.py`,
expansion from the rule's own candidates: iteration 2's 331, then iteration 3's top 600; 2186 API calls).
Label-free check first: only 19 of the 331 siblings sent ≥ 0.01 ETH in the window, none of them in the top 50 and 2 in the top 100.
So the sink signal could reorder only below rank 50.
Two of these "candidates" are services: Binance's hot wallet `0x28c6…1d60` entered iteration 3 as a cousin at rank 367,
and `0x23617e59…` is both a sibling (rank 324) and a parent marked as a service.
Iteration 3 lets services through as candidates; iteration 4 is meant to push them down.

**14:49 — Iteration 4 (sinks): recall@50 unchanged at 0.095 (failure 3 of 3); mid-ranks improve.**
Rule `rules/sinks.py`, tests `tests/test_sinks.py`.
*Process note:* the first two tests were written together with the rule, not run failing first.
A third test was added after the first run showed that the candidates' files leaked into the base graph
(1991 → 2486 candidates, because the candidates' payments created new parents and uncles).
Fixed: the base ranking uses the same graph as iteration 3, and the candidates' files only supply evidence of sending.
The first score was discarded.
819 of the 1991 candidates sent ≥ 0.01 ETH in the window and were moved down: 19 siblings, 107 of the top 600.
Dev, `results/iter_4.json` (precision is a lower bound), against iteration 3:

| k | iter 3 hits | iter 4 hits | iter 4 recall@k | iter 4 precision_lb@k |
|---|---|---|---|---|
| 50 | 23 | 23 | 0.095 | 0.46 |
| 100 | 51 | 52 | 0.214 | 0.52 |
| 200 | 98 | 101 | 0.416 | 0.51 |
| 331 | 127 | 140 | 0.576 | 0.42 |
| 500 | 155 | 162 | 0.667 | 0.32 |
| all (1991) | 167 | 167 | 0.687 | — |

The hypothesis holds where it can act: wallets that forwarded funds are less often listed,
and moving them down gains 13 dev hits by rank 331.
**Why it fails the 0.15 goal:** the top 50 contained no senders, so nothing above rank 65 changed.
Every top candidate already looks like a holding wallet, as the seeds do.
Our reading is that the ~27 non-dev addresses in the top 50 are mostly test-listed,
but that is only checked at the final scoring.

**14:50 — Condition 1 met by the alternative: three further iterations (2, 3, 4) failed to reach dev recall@50 ≥ 0.15, each with its reason.**
The common cause is the split ceiling (13:37): about 0.103 expected for any rule that does not see the dev/test split.
Iteration 2 reached 92% of it. Rule design stops here; next is the one-time final scoring on test.

**14:51 — Final scoring, once, after rule design stopped.**
`python -m chainsentinel.evaluate results/candidates_iter_N.csv --final` for N = 0..4,
and `scripts/final_report.py` → `results/final.json` (checked identical to the CLI output) and `results/recall_by_iteration.png`.
The plot was then redrawn with `--plot-only` (label position only), without scoring again.

| iter | dev r@50 | test r@50 | dev r@all | test r@all | listed precision_lb@50 |
|---|---|---|---|---|---|
| 0 baseline | 0.000 | 0.000 | 0.000 | 0.000 | 0.00 |
| 1 siblings | 0.074 | 0.082 | 0.523 | 0.519 | 0.76 |
| 2 similarity | 0.095 | 0.107 | 0.523 | 0.519 | 0.98 |
| 3 cousins | 0.095 | 0.107 | 0.687 | 0.724 | 0.98 |
| 4 sinks | 0.095 | 0.107 | 0.687 | 0.724 | 0.98 |

- **Test agrees with dev.** It is within 6 points everywhere and higher on reach, so no sign of overfitting to dev.
- **The ceiling argument holds.** From iteration 2 on, 49 of the top 50 are FBI-listed (23 dev + 26 test).
  The top of the ranking is as good as it can be for this metric.
- Over the whole held-out set, iteration 3/4 candidates contain 343 of 486 addresses (71%).
- Precision figures stay lower bounds (unlisted ≠ benign).
- Bookkeeping caveat: `code_commit` in `results/iter_N.json` is the HEAD at run time,
  and the rule being scored was not yet committed then. The rule is in the next commit.

README "Results" section written: table, plot, findings, failures with the reason, limits, next steps.

**15:35 — README corrected after review (session 1).**
The Loop table claimed a literature step that no journal entry shows; now marked as not used today, with the real "explore" step and a next step to close the gap.
Noted that the 0.15 target was ours and unreachable by construction. Removed the duplicated Limits section.

**15:55 — Fixes after a mock review against the official judging skill (session 1).**
- `fetch_seeds.py --hop4`: uncle selection no longer depends on the cache, so a rerun reuses the same 600 uncles
  instead of fetching the next 600. Checked: same 3181 before the cap, all 600 selected already cached.
- New `scripts/recount.py` → `results/recount.json`: top-50 listed counts with a random-order base rate.
  Iteration 2: 49 vs ~38 expected (pool 76% listed). Iterations 3–4: 49 vs ~9 expected (pool 17% listed).
- Reproduction check: `run_iteration.py 4 sinks` gives a byte-identical `candidates_iter_4.csv` (5.6 s, 1.26 GB peak RSS).
- Corrected ranks (Binance hot wallet 367, `0x23617e59…` 324; 368/325 were CSV line numbers).
- README/PROMPT: `final_report.py` also reads the holdout; iteration 4 was not test-first;
  the iteration-2 variant table came from an uncommitted prototype. Removed unused dependencies.
