"""Ground-truth labels from the FBI TraderTraitor alert of 2026-10-31.

The FBI describes these addresses as "holding or have held assets from the theft,
and are operated by or closely connected to North Korean TraderTraitor actors".
We treat them as positives for evaluation only; we never infer new labels from them.
"""

import html
import re

SOURCE_URL = "https://www.fbi.gov/investigate/cyber/alerts/2026/north-korea-responsible-for-6-billion-binance-attack"
PUBLISHED = "2026-10-31"

_SECTIONS = [("ETH", "ETH addresses"), ("BTC", "BTC addresses"), ("SOL", "SOL addresses")]
_PATTERNS = {
    "ETH": re.compile(r"\b0x[a-fA-F0-9]{40}\b"),
    "BTC": re.compile(r"\b(?:bc1[a-z0-9]{25,87}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})\b"),
    "SOL": re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b"),
}
_END_MARKER = "Submit Tips"


def _page_text(raw_html: str) -> str:
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", raw_html, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", "\n", t))


def parse_fbi_alert(raw_html: str) -> list[dict]:
    text = _page_text(raw_html)
    rows, seen = [], set()
    for i, (chain, heading) in enumerate(_SECTIONS):
        start = text.index(heading) + len(heading)
        nxt = _SECTIONS[i + 1][1] if i + 1 < len(_SECTIONS) else _END_MARKER
        body = text[start : text.index(nxt, start)]
        for addr in _PATTERNS[chain].findall(body):
            if chain == "ETH":
                addr = addr.lower()
            if (chain, addr) in seen:
                continue
            seen.add((chain, addr))
            rows.append({"chain": chain, "address": addr, "source": SOURCE_URL, "published": PUBLISHED})
    return rows
