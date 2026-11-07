"""Iteration 1: siblings of the seeds.

Hypothesis: the listed addresses are holding wallets filled in batches by distributor addresses.
Other wallets paid by the same distributor in the same window are likely part of the same batch.

Score of a candidate x = sum over funders f that paid x of
    w(f) = (seeds paid by f) / (distinct recipients paid by f).
A funder that paid mostly seeds is a focused distributor (w near 1);
an exchange paying thousands of customers gets w near 0.

Only native ETH (normal and internal transactions) is used:
ERC-20 events here are spoofed "ETH" tokens whose `from` can be forged (see JOURNAL, 13:20).
Funders themselves are not candidates (iteration 0 showed they are not listed).
"""

from collections import defaultdict


def rank(edges, seeds) -> list[str]:
    seeds = {s.lower() for s in seeds}
    paid = defaultdict(set)  # funder -> recipients
    for e in edges:
        if e["kind"] in ("normal", "internal") and e["asset"] == "ETH":
            paid[e["from"]].add(e["to"])

    funders = {f for f, rec in paid.items() if rec & seeds}
    score, n_funders = defaultdict(float), defaultdict(int)
    for f in funders:
        rec = paid[f]
        w = len(rec & seeds) / len(rec)
        for x in rec - seeds - funders:
            score[x] += w
            n_funders[x] += 1
    return sorted(score, key=lambda x: (-score[x], -n_funders[x], x))
