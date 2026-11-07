from chainsentinel.rules.siblings import rank


def eth(frm, to, kind="normal"):
    return {"from": frm, "to": to, "value": 1.0, "asset": "ETH", "kind": kind}


def spoof(frm, to):
    return {"from": frm, "to": to, "value": 1.0, "asset": "ETH:0xfake", "kind": "erc20"}


def test_siblings_of_a_focused_funder_outrank_those_of_a_busy_one():
    seeds = {"0xs1", "0xs2"}
    edges = [eth("0xa", "0xs1"), eth("0xa", "0xs2"), eth("0xa", "0xx1"), eth("0xa", "0xx2")]
    # A busy funder (exchange-like): pays one seed and 98 others.
    edges += [eth("0xe", "0xs1")] + [eth("0xe", f"0xo{i}") for i in range(98)]
    ranking = rank(edges, seeds)
    assert ranking[:2] == ["0xx1", "0xx2"]
    assert ranking.index("0xx1") < ranking.index("0xo0")


def test_spoofed_token_events_and_seeds_are_ignored():
    seeds = {"0xs1"}
    edges = [eth("0xa", "0xs1"), spoof("0xa", "0xy"), eth("0xa", "0xs1")]
    assert rank(edges, seeds) == []


def test_funders_themselves_are_not_candidates():
    seeds = {"0xs1"}
    edges = [eth("0xa", "0xs1"), eth("0xa", "0xx1")]
    assert rank(edges, seeds) == ["0xx1"]
