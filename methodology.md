---
layout: markdown
title: Data Methodology
permalink: /methodology/
# redirect from the old path
redirect_from: /client-fingerprinting/

header: Data Methodology
subheader: 
---


There's no inherent way to know exactly what client a validator is running. Researchers use other metrics to make deductions on which client a validator is most likely operating. The problem is they cannot distinguish with 100% certainty which client a validator is running.


## Consensus Client Data

[Blockprint](https://blockprint.sigp.io/) - Developed by Sigma Prime's Michael Sproul, Blockprint  analyzes each client's block proposal style as described in [this Twitter thread](https://twitter.com/sproulM_/status/1440512518242197516) ([Nitter](https://nitter.snopyta.org/sproulM_/status/1440512518242197516)).

## Execution Client Data

[Node Crawler](https://github.com/ethereum/node-crawler) - Developed by Ethereum team, is used for crawling network nodes and gathering the client data. Please note that it collects data based on number of **physical** machines, not validators themselves.  
This means that this data should be used only as a guideline to the overall client sentiment on the network, not the actual validator count.
