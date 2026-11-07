"""Iteration 4: holding wallets are sinks.

Observation (JOURNAL 13:20): every one of the 244 seed edges points *into* a seed;
no seed sent anything between 2026-10-27 and 2026-11-01.
Hypothesis: the listed addresses were holding wallets at the time of the list,
while the unlisted recipients of the same distributors include pass-through wallets,
next-level distributors and service deposit addresses, which forward what they receive.

Rule: take the iteration-3 ranking (`cousins`) and move every candidate that sent
≥ 0.01 ETH natively in the window below all candidates that did not, keeping the order inside both groups.
Evidence of sending comes from any fetched file, including the candidates' own activity
(`fetch_seeds.py --cand`, expansion from the rule's own candidates, not from labels).
"""

from chainsentinel.rules.cousins import rank as rank_cousins

USES_CANDIDATE_EDGES = True
from chainsentinel.rules.similarity import MIN_VALUE


def demote_senders(ranking, edges):
    senders = {e["from"] for e in edges
               if e["kind"] in ("normal", "internal") and e["asset"] == "ETH" and e["value"] >= MIN_VALUE}
    return [x for x in ranking if x not in senders] + [x for x in ranking if x in senders]


def rank(edges, seeds) -> list[str]:
    # The base ranking is iteration 3's on the same graph; the candidates' own files only supply evidence of sending.
    graph = [e for e in edges if e.get("source") != "edges_cand"]
    return demote_senders(rank_cousins(graph, seeds), edges)
