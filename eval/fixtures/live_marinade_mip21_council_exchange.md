---
name: live_marinade_mip21_council_exchange
source_url: https://forum.marinade.finance/t/mip-21-exchange-msol-from-the-dao-treasury-with-the-council-wallet-and-redirect-fees-to-the-council-wallet/1975
dao_context: "Marinade Finance DAO, MNDE + mSOL tokens, post-MIP-15 fee-flow era (fetched 2026-04-22)"
is_live: true
expected_behaviors:
  - "treasury_impact.direction is outflow or internal_transfer — 2,279 mSOL ($437,000) leaves DAO treasury to Council wallet"
  - "At least one red_flag with category=centralization (Council wallet holds redirected protocol fees + can dictate monthly MNDE transfer back)"
  - "Red flag for backdoor_permission expected if fee-redirect mechanism has no time-bound sunset (the proposal hints 'until fees redirect back to the DAO treasury' but does not enforce this on-chain)"
  - "stakeholders include Cerba (proposer), Marinade Labs (beneficiary), Council Wallet (beneficiary / counterparty)"
  - "questions_to_ask probes Council Wallet composition, fee-redirect sunset mechanism, and MNDE exchange-rate basis"
  - "Summary captures the mSOL↔MNDE swap AND the ongoing fee-redirect — NOT just the one-time swap"
---

# MIP-21: Exchange mSOL from DAO Treasury with Council Wallet

**Author:** Cerba
**Date:** January 14, 2026, 12:48pm

---

## Introduction

Since MIP-15 passed, protocol revenues accrue directly to the DAO treasury, while Marinade Labs received a 100M MNDE grant for 12-18 months of operations. This means Marinade Labs primarily holds MNDE for expenses.

MNDE lacks liquidity compared to mSOL. Selling MNDE to fund operations would create significant selling pressure on the token, particularly under current market conditions.

## Proposal

Marinade Labs proposes transferring accumulated mSOL from the DAO treasury (2,279 mSOL, valued at $437,000) to the Council wallet. In exchange, the Council wallet would transfer 9,741,000 MNDE tokens ($437,000 value) back to the DAO Treasury.

Additionally, the proposal suggests redirecting protocol fees to the Council Wallet. Monthly, the Council wallet would transfer equivalent MNDE value back to the DAO treasury, maintaining notional treasury value as if revenues were accumulated normally. This monthly transfer would cease once fees redirect back to the DAO treasury.

## Rationale

This approach allows Marinade Labs to avoid selling MNDE while covering expenses and growing protocol TVL. mSOL's superior liquidity means selling it has no MNDE price impact, unlike MNDE sales.

Redirecting protocol fees prevents recurring similar proposals and reduces voting fatigue.

## Conclusion

Enabling MNDE-for-mSOL exchanges instead of market sales benefits both the MNDE token and the DAO, while allowing Marinade Labs to fund operations supporting protocol growth.

---

**Follow-up (February 3, 2026):** Additional mSOL accumulated over 12 days (1,071 mSOL, $149,932) would transfer to Council in exchange for 5,605,639 MNDE, with fee redirection implementation following shortly.
