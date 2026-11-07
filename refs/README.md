# References

Sources the loop reads for heuristics.
Summaries here are our own words; follow the links for the originals.

## Address clustering and tracing

- **Victor, F. (2020). Address Clustering Heuristics for Ethereum.**
  Financial Cryptography and Data Security (FC 2020).
  Heuristics: exchange deposit addresses, airdrop multi-participation, self-authorisation of tokens.
  Relevance: deposit-address reuse could link laundering hops to the same off-ramp.
- **Meiklejohn, S. et al. (2013). A Fistful of Bitcoins: Characterizing Payments Among Men with No Names.**
  ACM IMC 2013.
  Heuristics: multi-input and change-address clustering on Bitcoin; following peel chains.
  Relevance: the peel-chain idea transfers to account-based fan-out on Ethereum.

## This incident

- FBI, *North Korea Responsible for $6 Billion+ Binance Attack*, 2026-10-31.
  https://www.fbi.gov/investigate/cyber/alerts/2026/north-korea-responsible-for-6-billion-binance-attack
  Ground truth; snapshot in `data/raw/`.
  States that stolen assets were converted mainly into ETH and are expected to move through DeFi and instant swap services.
- CNBC, *Binance's $6.3 billion hack: what we know and what comes next*, 2026-10-30.
  https://www.cnbc.com/2026/10/30/billions-in-crypto-frozen-in-binance-hack-heres-what-happens-next-.html
- Cointelegraph, *Binance hackers had 8 weeks of access before $6.3B exploit, Security Alliance estimates*.
  https://cointelegraph.com/news/binance-hackers-8-weeks-access-63b-exploit-security-alliance

## To check

- Chainalysis and TRM write-ups on this incident.
  A pattern of "receive 1 TRX, then a large amount, then forward" on TRON has been attributed to Chainalysis,
  but we have not read the original yet. Do not use it until verified.
