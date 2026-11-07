from chainsentinel.rules.similarity import rank


def eth(frm, to, value=10.0, kind="normal", tx=None):
    return {"tx_hash": tx or f"{frm}-{to}-{value}", "from": frm, "to": to,
            "value": value, "asset": "ETH", "kind": kind, "timestamp": 0}


def spoof(frm, to):
    return {"tx_hash": f"s-{frm}-{to}", "from": frm, "to": to, "value": 10.0,
            "asset": "ETH:0xfake", "kind": "erc20", "timestamp": 0}


def test_dust_payments_neither_create_candidates_nor_dilute_the_funder():
    seeds = {"0xs1"}
    edges = [eth("0xa", "0xs1", 30.0), eth("0xa", "0xx1", 30.0)]
    edges += [eth("0xa", f"0xdust{i}", 0.001) for i in range(50)]
    edges += [eth("0xa", "0xzero", 0.0)]
    ranking = rank(edges, seeds)
    assert ranking == ["0xx1"]
    # Without dilution by the 51 dust recipients, x1 competes with a focused funder's sibling.
    edges += [eth("0xb", "0xs1", 30.0), eth("0xb", "0xx2", 30.0), eth("0xb", "0xx3", 30.0)]
    assert rank(edges, seeds)[0] == "0xx1"


def test_sibling_paid_like_the_seeds_outranks_one_paid_differently():
    seeds = {"0xs1"}
    edges = [eth("0xa", "0xs1", 40.0), eth("0xa", "0xclose", 35.0), eth("0xa", "0xfar", 0.05)]
    assert rank(edges, seeds) == ["0xclose", "0xfar"]


def test_spoofed_tokens_seeds_and_funders_are_ignored():
    seeds = {"0xs1"}
    edges = [eth("0xa", "0xs1"), spoof("0xa", "0xy"), eth("0xa", "0xb"), eth("0xb", "0xs1"),
             eth("0xa", "0xx1")]
    assert rank(edges, seeds) == ["0xx1"]
