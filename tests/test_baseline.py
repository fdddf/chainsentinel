from chainsentinel.rules.baseline import rank


def e(frm, to):
    return {"from": frm, "to": to, "value": 1.0, "asset": "ETH"}


def test_ranks_by_distinct_seeds_then_transfers():
    seeds = {"0xs1", "0xs2", "0xs3"}
    edges = [
        e("0xs1", "0xa"), e("0xs2", "0xa"), e("0xs3", "0xa"),  # 3 seeds
        e("0xs1", "0xb"), e("0xs1", "0xb"), e("0xs1", "0xb"),  # 1 seed, 3 transfers
        e("0xc", "0xs2"), e("0xc", "0xs3"),                    # 2 seeds, incoming
    ]
    assert rank(edges, seeds) == ["0xa", "0xc", "0xb"]


def test_seeds_and_unrelated_edges_are_not_candidates():
    seeds = {"0xs1", "0xs2"}
    edges = [e("0xs1", "0xs2"), e("0xx", "0xy"), e("0xs1", "0xa")]
    assert rank(edges, seeds) == ["0xa"]
