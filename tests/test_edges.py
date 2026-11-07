import pytest

from chainsentinel.edges import normalise

NORMAL = {
    "hash": "0xT1", "blockNumber": "100", "timeStamp": "1793318400",
    "from": "0xAAA", "to": "0xBBB", "value": "1500000000000000000", "isError": "0",
}
FAILED = dict(NORMAL, hash="0xT2", isError="1")
CONTRACT_CREATION = dict(NORMAL, hash="0xT3", to="")
INTERNAL = {
    "hash": "0xT4", "blockNumber": "101", "timeStamp": "1793318500",
    "from": "0xCCC", "to": "0xAAA", "value": "2000000000000000000", "isError": "0",
}
TOKEN = {
    "hash": "0xT5", "blockNumber": "102", "timeStamp": "1793318600",
    "from": "0xAAA", "to": "0xDDD", "value": "2500000", "tokenDecimal": "6",
    "tokenSymbol": "USDT", "contractAddress": "0xUSDT",
}


def test_normal_internal_and_token_rows():
    rows = normalise({"txlist": [NORMAL], "txlistinternal": [INTERNAL], "tokentx": [TOKEN]})
    by_hash = {r["tx_hash"]: r for r in rows}
    assert by_hash["0xt1"]["value"] == pytest.approx(1.5)
    assert by_hash["0xt1"]["asset"] == "ETH"
    assert by_hash["0xt1"]["kind"] == "normal"
    assert by_hash["0xt4"]["kind"] == "internal"
    assert by_hash["0xt5"]["value"] == pytest.approx(2.5)
    assert by_hash["0xt5"]["asset"] == "USDT:0xusdt"
    assert by_hash["0xt1"]["from"] == "0xaaa"


def test_failed_and_contract_creation_are_dropped():
    rows = normalise({"txlist": [FAILED, CONTRACT_CREATION], "txlistinternal": [], "tokentx": []})
    assert rows == []
