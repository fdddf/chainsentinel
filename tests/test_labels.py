from pathlib import Path

from chainsentinel.labels import parse_fbi_alert

SNAPSHOT = Path(__file__).parents[1] / "data/raw/fbi_alert_2026-10-31.wayback-20261107060018.html"


def test_parses_published_counts():
    # Counts as reported by press coverage of the FBI alert: 608 ETH, 19 BTC, 1 SOL (628 total).
    labels = parse_fbi_alert(SNAPSHOT.read_text(encoding="utf-8", errors="replace"))
    by_chain = {}
    for row in labels:
        by_chain[row["chain"]] = by_chain.get(row["chain"], 0) + 1
    assert by_chain == {"ETH": 608, "BTC": 19, "SOL": 1}


def test_eth_addresses_are_normalised_and_unique():
    labels = parse_fbi_alert(SNAPSHOT.read_text(encoding="utf-8", errors="replace"))
    eth = [r["address"] for r in labels if r["chain"] == "ETH"]
    assert all(a == a.lower() and a.startswith("0x") and len(a) == 42 for a in eth)
    assert len(eth) == len(set(eth))
