"""Normalise Etherscan account responses into one transfer edge list."""

KINDS = {"txlist": "normal", "txlistinternal": "internal", "tokentx": "erc20"}
FIELDS = ["tx_hash", "block", "timestamp", "from", "to", "asset", "value", "kind"]


def _row(tx: dict, kind: str) -> dict | None:
    if tx.get("isError", "0") != "0" or not tx.get("to"):
        return None
    if kind == "erc20":
        decimals = int(tx.get("tokenDecimal") or 0)
        asset = f"{tx.get('tokenSymbol', '?')}:{tx['contractAddress'].lower()}"
    else:
        decimals, asset = 18, "ETH"
    return {
        "tx_hash": tx["hash"].lower(),
        "block": int(tx["blockNumber"]),
        "timestamp": int(tx["timeStamp"]),
        "from": tx["from"].lower(),
        "to": tx["to"].lower(),
        "asset": asset,
        "value": int(tx["value"]) / 10**decimals,
        "kind": kind,
    }


def normalise(responses: dict) -> list[dict]:
    """responses: {"txlist": [...], "txlistinternal": [...], "tokentx": [...]} for one address."""
    rows = []
    for action, kind in KINDS.items():
        for tx in responses.get(action, []):
            r = _row(tx, kind)
            if r:
                rows.append(r)
    return rows
