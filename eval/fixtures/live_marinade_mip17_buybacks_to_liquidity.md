---
name: live_marinade_mip17_buybacks_to_liquidity
source_url: https://forum.marinade.finance/t/mip-17-refocusing-from-buybacks-to-building-liquidity/1960
dao_context: "Marinade Finance DAO, MNDE + mSOL tokens, protocol-fee reallocation proposal post-MIP-11 (fetched 2026-04-22)"
is_live: true
expected_behaviors:
  - "treasury_impact.direction is 'internal_transfer' or 'none' — reallocation of protocol-fee flow, not a spend"
  - "Red flag vague_kpi likely — 'deeper liquidity' and 'lower slippage' are not quantified (no TVL target, no basis-point slippage goal, no $ liquidity floor)"
  - "Red flag missing_milestone likely — MIP-16 is referenced for deployment but no checkpoints are defined for when MNDE/mSOL liquidity pool depth would be evaluated"
  - "NO red_flag for backdoor_permission or centralization — this is a strategic policy shift, not a permission grant"
  - "stakeholders include helloiamvu (proposer), MNDE holders (affected_group), DAO treasury (affected_group)"
  - "questions_to_ask probes concrete liquidity targets, reversal conditions, interaction with MIP-16, and fate of in-flight TWAP orders"
  - "Summary captures: pause buybacks + mint mSOL + deploy to MNDE/mSOL pools via MIP-16"
---

# MIP-17: Refocusing from Buybacks to Building Liquidity

**Author:** helloiamvu
**Date:** November 7, 2025, 9:23am
**Status:** Voted (did not pass initially; re-voted December 22, 2025)

---

## Abstract

This proposal recommends that the DAO pause its current MNDE buyback program and instead accumulate mSOL in the treasury. The goal is to enable deeper MNDE/mSOL liquidity across decentralized exchanges. The accumulated mSOL may be deployed to liquidity pools as outlined in MIP-16, helping improve MNDE's trading experience, slippage profile, and accessibility across Solana DeFi.

---

## Motivation

MIP-11 introduced a mechanism where the DAO used 50% of protocol performance fees (collected in SOL) to perform monthly MNDE buybacks via TWAP orders. These operations have now run for several months.

While this initiative aligned value accrual to MNDE holders, the DAO has identified a higher-priority challenge in the current market: "shallow liquidity in MNDE trading pairs". This condition limits capital efficiency, deters integrations, and raises slippage for both buyers and sellers.

Deeper liquidity is a prerequisite for improved MNDE market access. Enhancing liquidity depth is expected to:

- Lower slippage for traders and integrators
- Attract new buyers deterred by thin books
- Support MNDE's broader utility and adoption across Solana DeFi

Accumulating mSOL rather than converting treasury SOL into MNDE is a necessary first step toward enabling this liquidity.

---

## Proposal

- **Pause all MNDE buybacks** initiated under MIP-11
- **Retain 100% of protocol performance fees** (in SOL) in the DAO treasury
- **Mint mSOL** from these SOL funds as appropriate, enabling deployment into MNDE/mSOL liquidity pools, starting with those defined in MIP-16

This proposal is forward-looking and creates the foundation for improved MNDE market conditions through liquidity-focused deployments.

---

## Implementation Details

- MNDE buybacks will be "paused one epoch after proposal approval" to ensure sufficient transition time.
- Any outstanding TWAP orders (e.g., placed via Jupiter) will be allowed to execute fully.
- From that point onward, no new MNDE purchases will be made under MIP-11.

---

## Rationale

This is not a reversal of value alignment — it is a strategic shift in *how* the DAO delivers that value. Liquidity is the critical bottleneck for MNDE's usability and market presence today. By accumulating mSOL, the DAO gains the flexibility to:

- Seed deeper liquidity in priority markets
- Improve MNDE trading conditions
- Better support long-term demand

The goal is to support deeper MNDE/mSOL liquidity through initiatives such as MIP-16, which is expected to have greater impact on MNDE's price stability and utility in the current market environment.

---

## Conclusion

MIP-17 proposes a pause on MNDE buybacks and a reallocation of protocol revenues toward strengthening MNDE liquidity. This represents a tactical pivot that aligns with evolving priorities and prepares MNDE for more sustainable long-term growth.
