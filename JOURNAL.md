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
