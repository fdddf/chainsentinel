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
