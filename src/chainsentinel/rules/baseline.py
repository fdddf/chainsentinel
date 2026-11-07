"""Iteration 0 baseline.

Every 1-hop neighbour of a seed, in either direction,
ranked by the number of distinct seeds it transacted with,
then by the number of transfers with seeds.

Deliberately naive: no value weighting (assets have no common price here),
no filtering of exchanges, routers or spam.
"""

from collections import defaultdict


def rank(edges, seeds) -> list[str]:
    seeds = {s.lower() for s in seeds}
    linked = defaultdict(set)
    transfers = defaultdict(int)
    for ed in edges:
        a, b = ed["from"], ed["to"]
        for seed, other in ((a, b), (b, a)):
            if seed in seeds and other not in seeds:
                linked[other].add(seed)
                transfers[other] += 1
    return sorted(linked, key=lambda x: (-len(linked[x]), -transfers[x], x))
