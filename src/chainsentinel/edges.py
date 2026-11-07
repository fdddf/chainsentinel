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


def open_text(path):
    """Open a data file, or its gzipped copy `<path>.gz` (used for files over 50 MB)."""
    import gzip
    from pathlib import Path

    path = Path(path)
    if path.exists():
        return open(path, newline="")
    return gzip.open(f"{path}.gz", "rt", newline="")


def cache_exists(path) -> bool:
    from pathlib import Path

    return Path(path).exists() or Path(f"{path}.gz").exists()


def read_cache(path) -> dict:
    """One cached Etherscan response file (plain or gzipped)."""
    import json

    with open_text(path) as f:
        return json.load(f)
