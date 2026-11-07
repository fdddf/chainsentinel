from chainsentinel.rules.sinks import demote_senders


def eth(frm, to, value=30.0):
    return {"tx_hash": f"{frm}-{to}-{value}", "from": frm, "to": to,
            "value": value, "asset": "ETH", "kind": "normal", "timestamp": 0}


def test_candidates_that_sent_eth_drop_below_silent_ones_keeping_order():
    ranking = ["0xa", "0xb", "0xc", "0xd"]
    edges = [eth("0xa", "0xelsewhere", 25.0), eth("0xc", "0xelsewhere", 1.0)]
    assert demote_senders(ranking, edges) == ["0xb", "0xd", "0xa", "0xc"]


def test_dust_and_spoofed_tokens_do_not_count_as_sending():
    ranking = ["0xa", "0xb"]
    edges = [eth("0xa", "0xz", 0.001),
             {"tx_hash": "t", "from": "0xa", "to": "0xz", "value": 9.0,
              "asset": "ETH:0xfake", "kind": "erc20", "timestamp": 0}]
    assert demote_senders(ranking, edges) == ["0xa", "0xb"]
