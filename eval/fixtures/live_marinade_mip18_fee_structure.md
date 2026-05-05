---
name: live_marinade_mip18_fee_structure
source_url: https://forum.marinade.finance/t/mip-18-marinade-fee-structure-revamp-updated/1967
dao_context: "Marinade Finance DAO, MNDE + mSOL tokens, fee-structure revision following SAM experience (fetched 2026-04-22)"
is_live: true
expected_behaviors:
  - "treasury_impact.direction is typically 'none' or 'unknown' — this is a parameter / policy change, not a direct spend. amount_usd null."
  - "Red flag with category=vague_kpi likely — 'Solana Staking Rate' is defined in proposal but 'outperformance' threshold is not quantified (how much over SSR triggers fee?)"
  - "Red flag technical_risk possible — SAM mechanics and validator bidding inefficiencies are cited but the SSR computation source is not specified"
  - "NO red_flag for treasury_impact categories (outflow, unbounded_spend) — this is fee policy, not spend"
  - "stakeholders include helloiamvu (proposer), stakers (affected_group), validators (affected_group via SAM)"
  - "questions_to_ask probes exact SSR trigger formula, fee rate when triggered, and interaction with prior failed-quorum vote"
  - "Summary captures THREE changes: drop fixed 9.5%, introduce conditional fee, unify 20bps unstake"
---

# MIP-18 - Marinade Fee Structure Revamp [UPDATED]

**Author:** helloiamvu
**Date:** November 28, 2025, 3:55pm
**Updated:** December 22, 2025, 3:00pm

---

## Abstract

This proposal modifies the fee structure from MIP-5 by removing the fixed 9.5% performance fee and replacing it with "a conditional fee that is charged only when Marinade outperforms the Solana Staking Rate." A unified 20 basis point unstake fee applies across all Marinade products, designed to maintain yield competitiveness while aligning DAO revenue with demonstrated outperformance.

---

## Motivation

Marinade's core mission centers on TVL growth and staker acquisition. The proposal identifies that stakers increasingly prioritize APY and select providers offering optimal net returns. While the Stake Auction Marketplace (SAM) enhances APY optimization, its effectiveness diminishes under fixed performance fees applied regardless of outperformance.

Key concerns addressed:

- **Competitive disadvantage during lower-reward periods:** Static fees reduce APY competitiveness when Marinade merely matches market rates rather than exceeding them
- **Misaligned incentives:** Users pay continuously even when Marinade delivers only baseline performance
- **Revenue-reality gap:** The DAO approved 9.5% fees but actual capture falls short due to SAM mechanics and validator bidding inefficiencies

The proposal argues this creates a "worst of both worlds" scenario — users face constant fee drag while the DAO fails to earn intended take rates.

**Solana Staking Rate (SSR) Definition:**

SSR represents "network-wide staking rewards derived from inflation and transaction fees (including priority fees)." MEV is explicitly excluded, establishing a neutral chain-native benchmark.

**User Yield Parity Goal:**

The objective delivers optimal staking yields matching or exceeding self-delegation returns. A 20 bps unstake fee shifts revenue collection toward exits rather than long-term rewards, avoiding penalty of long-term stakers while offsetting performance fee changes.

---

## Proposal

Three primary changes:

1. **Deprecate Fixed Performance Fee**
   - Removes the current 9.5% performance fee from Marinade Native and mSOL rewards

2. **Introduce Conditional Performance Fee**
   - New performance fee applies only when Marinade APY exceeds the Solana Staking Rate

3. **Unify Unstake Fee**
   - 20 basis points (0.20%) unstake fee applied uniformly across:
     - Marinade Native
     - mSOL
     - Marinade Select

---

## Conclusion

The updated fee model prioritizes user yield competitiveness while connecting DAO revenue to actual value delivery. By conditioning performance fees on outperformance relative to baseline, "Marinade remains competitive in all market conditions and only charges when it outperforms the chain-wide baseline."

---

**Voting Status:** Vote went live on Realms December 22, 2025. Previous vote failed to meet quorum despite strong approval sentiment; rerun enables broader participation.
