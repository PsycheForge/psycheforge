---
name: live_jito_jip26_csd_budget
source_url: https://forum.jito.network/t/jip-26-extend-the-budget-of-the-cryptoeconomics-subdao-csd/902
dao_context: "Jito DAO, JTO + JitoSOL tokens, Cryptoeconomics subDAO (CSD) operating under JIP-17 multisig. Fetched 2026-04-22."
is_live: true
expected_behaviors:
  - "treasury_impact.direction is outflow — 50,000 JitoSOL (~$12.5m)"
  - "amount_usd should be ~12_500_000 (mentioned explicitly as 'roughly $12.5m')"
  - "Red flag centralization expected — 4-of-6 multisig controls budget, DAO only gets quarterly reports (no direct on-chain rebuke mechanism)"
  - "Red flag missing_milestone possible — quarterly reports required but no concrete deliverable gates (what happens if Vault or Auction contracts slip past Q1-Q2 2026?)"
  - "Red flag vague_kpi possible — 'POL research paper' and 'strengthened data infrastructure' are outputs without measurable thresholds"
  - "NO red_flag for backdoor_permission — JIP-17 already established multisig; this is a renewal, not a new authority"
  - "stakeholders include drnick (proposer), CSD multisig (4/6 signers, beneficiary), JTO holders (affected_group via buybacks)"
  - "questions_to_ask probes: CSD multisig signers identity, Q1/Q2 deliverable gates, what triggers return-of-unused-funds"
  - "Summary captures 50,000 JitoSOL + 100% revenue buybacks mandate + open-source-license requirement"
---

# JIP-26: Extend the Budget of the Cryptoeconomics subDAO (CSD)

**Author:** drnick
**Date:** October 28, 2025
**Category:** Treasury

## Abstract

The proposal requests "50,000 JitoSOL in order to empower the CSD to execute buybacks equivalent to 100% of Jito Network revenue (roughly $12.5m)."

## Motivation

The CSD has executed over $3.2 million in buybacks since its activation and launched development of three mechanisms: Vault, TWAP, and JTO Auction. However, "its current runway will be exhausted within the next quarter due to the rate of buybacks."

Without renewed funding, the DAO risks halting:
- Ongoing TWAP-based buybacks and market-data analysis
- Vault and Auction contract finalization (Q1–Q2 2026)
- Protocol-owned liquidity mechanism research

## Specification

Upon passage, the DAO transfers 50,000 JitoSOL to the CSD multi-sig, governed by its existing 4/6 multisig established in JIP-17. Requirements include quarterly progress reports covering buyback execution, treasury balances, and development milestones. "All code and research outputs must be open-sourced under an MIT-style license."

## Key Outcomes

- Vault and JTO Auction v1 smart contracts delivery
- Monthly TWAP buybacks maintaining revenue-to-JTO price linkage
- POL research paper with implementation recommendations
- Strengthened data infrastructure for future automated buyback algorithms

## Cost Summary

50,000 JitoSOL for JTO buybacks
