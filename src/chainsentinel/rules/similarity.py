"""Iteration 2: siblings paid like the seeds.

Hypothesis: the listed addresses are holding wallets that a distributor filled with tens of ETH each.
Among the other recipients of the same distributor, those paid a similar amount
are more likely part of the same batch than those paid something very different.
Dust and zero-value transfers are address poisoning: vanity look-alike addresses
(e.g. 0x747ad856…a44e mimicking the real funder 0x747af825…a44e) send near-nothing
to the recipients of the real funder. They are dropped before anything else,
so they neither create candidates nor dilute a funder's focus.

Score of a candidate x = sum over funders f that paid x of w(f) * sim(f, x), where
    w(f)      = (seeds paid by f) / (distinct recipients paid by f), after the dust filter;
    sim(f, x) = max over f's payments to x of exp(-d),
    d         = min over f's seed payments of |log10(v) - log10(seed_v)|.

Only native ETH (normal and internal transactions) is used;
ERC-20 events here are spoofed "ETH" tokens whose `from` can be forged (see JOURNAL, 13:20).
Funders themselves are not candidates (iteration 0 showed they are not listed).
"""

import math
from collections import defaultdict

MIN_VALUE = 0.01  # ETH; below this a payment is treated as dust / poisoning


def _log(v: float) -> float:
    return math.log10(v + 1e-9)


def rank(edges, seeds) -> list[str]:
    seeds = {s.lower() for s in seeds}
    unique = {}
    for e in edges:
        if e["kind"] in ("normal", "internal") and e["asset"] == "ETH" and e["value"] >= MIN_VALUE:
            unique[(e.get("tx_hash"), e["from"], e["to"], e["value"])] = e
    pays = defaultdict(list)  # funder -> payments
    for e in unique.values():
        pays[e["from"]].append(e)

    funders = {f for f, ps in pays.items() if any(p["to"] in seeds for p in ps)}
    score = defaultdict(float)
    for f in funders:
        ps = pays[f]
        rec = {p["to"] for p in ps}
        w = len(rec & seeds) / len(rec)
        seed_logs = [_log(p["value"]) for p in ps if p["to"] in seeds]
        best = defaultdict(float)
        for p in ps:
            x = p["to"]
            if x in seeds or x in funders:
                continue
            d = min(abs(_log(p["value"]) - s) for s in seed_logs)
            best[x] = max(best[x], math.exp(-d))
        for x, s in best.items():
            score[x] += w * s
    return sorted(score, key=lambda x: (-score[x], x))
