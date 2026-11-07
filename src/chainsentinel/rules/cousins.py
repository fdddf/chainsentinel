"""Iteration 3: cousins, one hop up and back down.

Hypothesis: 48% of the dev addresses are paid by no seed funder in the window,
but they may be paid by *other* distributors fed by the same upstream wallets.
The funders' own funders ("parents") also paid other distributors ("uncles");
the uncles' recipients ("cousins") may be holding wallets of the same operation.

Ranking:
1. The siblings, ranked exactly as in iteration 2 (`similarity`), come first.
2. Cousins follow, scored by
       Σ over uncles u that paid x of  focus(u) · share(u) · band(v)
   focus(u) = max over parents p of u of (funders paid by p) / (recipients paid ≥ 1 ETH by p);
   share(u) = mean band fit of u's payments over its recipients (does u pay like a seed funder?);
   band(v)  = exp(-d), d = log10 distance of the payment v to the interquartile band of the seed payments.

Parents are addresses that paid ≥ 1 ETH to at least two distinct seed funders,
so a single coincidental payment does not open a branch.
Parents and uncles with more than MAX_FANOUT recipients are treated as services (exchange, router) and not followed.
Distributors at any level (funders, parents, uncles) are never candidates (iteration 0: funders are not listed).
Dust (< 0.01 ETH) is dropped as in iteration 2. Only native ETH is used.
The rule sees only the edges and the seeds; which addresses were fetched was decided from seeds and funders only.
"""

import math
from collections import defaultdict

from chainsentinel.rules.similarity import MIN_VALUE, _log
from chainsentinel.rules.similarity import rank as rank_siblings

PARENT_MIN = 1.0  # ETH a parent must have sent to a funder (and to an uncle)
MAX_FANOUT = 1000  # recipients above which a parent or uncle is treated as a service


def _quantile(xs, q):
    xs = sorted(xs)
    i = (len(xs) - 1) * q
    lo, hi = math.floor(i), math.ceil(i)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def rank(edges, seeds) -> list[str]:
    seeds = {s.lower() for s in seeds}
    siblings = rank_siblings(edges, seeds)

    unique = {}
    for e in edges:
        if e["kind"] in ("normal", "internal") and e["asset"] == "ETH" and e["value"] >= MIN_VALUE:
            unique[(e.get("tx_hash"), e["from"], e["to"], e["value"])] = e
    pays = defaultdict(list)
    for e in unique.values():
        pays[e["from"]].append(e)

    seed_pays = [e for e in unique.values() if e["to"] in seeds]
    funders = {e["from"] for e in seed_pays}
    logs = [_log(e["value"]) for e in seed_pays]
    q1, q3 = _quantile(logs, 0.25), _quantile(logs, 0.75)

    def band(v):
        lv = _log(v)
        return math.exp(-max(0.0, q1 - lv, lv - q3))

    focus = {}
    for p, ps in pays.items():
        if p in seeds:
            continue
        big = {e["to"] for e in ps if e["value"] >= PARENT_MIN}
        n_funders = len(big & funders)
        if n_funders >= 2 and len(big) <= MAX_FANOUT:
            focus[p] = n_funders / len(big)

    uncle_focus = defaultdict(float)
    for p, f in focus.items():
        for e in pays[p]:
            u = e["to"]
            if e["value"] >= PARENT_MIN and u not in seeds and u not in funders and u not in focus:
                uncle_focus[u] = max(uncle_focus[u], f)

    exclude = seeds | funders | set(focus) | set(uncle_focus) | set(siblings)
    score = defaultdict(float)
    for u, f in uncle_focus.items():
        ps = pays.get(u, [])
        rec = {e["to"] for e in ps}
        if not rec or len(rec) > MAX_FANOUT:
            continue
        fit = defaultdict(float)  # recipient -> best band fit of u's payments to it
        for e in ps:
            fit[e["to"]] = max(fit[e["to"]], band(e["value"]))
        share = sum(fit.values()) / len(fit)
        for x, b in fit.items():
            if x not in exclude:
                score[x] += f * share * b
    cousins = sorted((x for x in score if score[x] > 0), key=lambda x: (-score[x], x))
    return siblings + cousins
