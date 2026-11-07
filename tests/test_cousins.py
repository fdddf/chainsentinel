from chainsentinel.rules.cousins import rank


def eth(frm, to, value=30.0):
    return {"tx_hash": f"{frm}-{to}-{value}", "from": frm, "to": to,
            "value": value, "asset": "ETH", "kind": "normal", "timestamp": 0}


def family():
    """Parent P funds two seed funders F1, F2 and one other distributor U (an uncle)."""
    seeds = {"0xs1", "0xs2"}
    edges = [
        eth("0xp", "0xf1", 500.0), eth("0xp", "0xf2", 500.0), eth("0xp", "0xu", 500.0),
        eth("0xf1", "0xs1"), eth("0xf1", "0xsib"),
        eth("0xf2", "0xs2"),
        eth("0xu", "0xcousin", 40.0), eth("0xu", "0xodd", 0.05),
    ]
    return seeds, edges


def test_cousins_are_reached_and_ranked_after_siblings():
    seeds, edges = family()
    ranking = rank(edges, seeds)
    assert ranking[0] == "0xsib"
    assert "0xcousin" in ranking


def test_cousin_paid_in_the_seed_band_outranks_one_paid_dust_like_amounts():
    seeds, edges = family()
    ranking = rank(edges, seeds)
    assert ranking.index("0xcousin") < ranking.index("0xodd")


def test_distributors_are_never_candidates():
    seeds, edges = family()
    ranking = rank(edges, seeds)
    assert not {"0xp", "0xf1", "0xf2", "0xu"} & set(ranking)


def test_a_parent_of_only_one_funder_does_not_open_a_new_branch():
    seeds = {"0xs1"}
    edges = [eth("0xp", "0xf1", 500.0), eth("0xp", "0xu", 500.0),
             eth("0xf1", "0xs1"), eth("0xu", "0xcousin", 40.0)]
    assert "0xcousin" not in rank(edges, seeds)
