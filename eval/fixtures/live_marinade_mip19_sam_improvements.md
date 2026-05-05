---
name: live_marinade_mip19_sam_improvements
source_url: https://forum.marinade.finance/t/mip-19-improving-sam-auction-stake-priority-bond-risk-reduction-mechanism-higher-validator-caps/1969
dao_context: "Marinade Finance DAO, MNDE + mSOL tokens, SAM (Stake Auction Marketplace) parameter + mechanism update (fetched 2026-05-04)"
is_live: true
expected_behaviors:
  - "treasury_impact.direction is 'none' — parameter / mechanism change, no direct outflow"
  - "Red flag centralization expected — validator stake cap raised from 4% to 15% of TVL (3.75x increase). 15% concentration is meaningful single-validator risk."
  - "Red flag technical_risk likely — Bond Risk Reduction Mechanism has complex math (minBondCoef, idealBondCoef, forcedUndelegationCoef) with no third-party audit requirement mentioned"
  - "Red flag vague_kpi possible — 'optimal staker APY', 'superior returns', 'evolved market conditions' lack quantified targets"
  - "Removed feature: MNDE Enhanced Stake (locked MNDE → cap influence). Skill should note this as an authority/feature *removal*, not a permission grant."
  - "Skill should NOT classify the validator cap increase as backdoor_permission — it is a public parameter change governed by this very vote."
  - "Skill should notice the explicit 'Vote YES' language at the end of the proposal but MUST NOT itself recommend voting."
  - "stakeholders include kron (proposer), Marinade Labs (executes the changes), top validators (beneficiary of higher cap), smaller validators (affected_group losing stake share), MNDE locked-stake users (affected_group losing influence)"
  - "Predicted outcome reasonable: approve (parameter changes that improve operational efficiency typically pass on Marinade)"
---

# MIP-19: Improving SAM - Auction Stake Priority, Bond Risk Reduction Mechanism, Higher Validator Caps

**Author:** kron
**Date:** December 16, 2025

---

## Introduction

SAM was constructed to direct Solana stake toward validators delivering superior returns, guaranteeing stakers receive optimal market APY. Market evolution has shifted some original assumptions about stake movement and validator incentives, necessitating a system refresh.

This proposal updates SAM by: (1) enabling bids to determine stake priority so higher-value validators receive stake sooner, (2) introducing a Bond Risk Reduction Mechanism to better align bond maintenance incentives with re-delegation costs, (3) removing the largely unused MNDE Enhanced Stake mechanism to simplify the system, and (4) increasing per-validator stake caps through controlled rollout.

---

## Proposal

If passed, this proposal mandates Marinade Labs implement changes so that:

1. **Allow validators to win stake priority in the auction**
   - Validators will directly influence Marinade delegation ordering

2. **Introduce a Bond Risk Reduction Mechanism**
   - Protect stakers' rewards against validators depleting bonds
   - Charge full re-delegation costs to validators requiring stake reallocation
   - Boost Marinade APY through improved efficiency

3. **Abandon MNDE Enhanced Stake**
   - **Current State:** MNDE Enhanced Stake allows locked MNDE holders to increase validator maximum stake caps. This feature currently changes no caps as it sees minimal adoption.
   - Removing this feature simplifies infrastructure for other improvements

4. **Increase maximum Stake a single Validator can obtain to 15% of TVL**
   - **Current State:** Validators capped at 4% of TVL (MIP-10); previously 2% pre-MIP-10
   - Allows top validators to lead in securing Solana network

---

## Rationale

### 1. Allow validators to win stake priority in the auction

SAM contains a fundamental tradeoff between re-delegating stake to highest-performing, top-bidding validators versus maintaining current distribution. Re-delegation incurs costs—"for one epoch, the stake must remain undelegated and unproductive."

Market slowdown has reduced profitable re-delegation opportunities. Marinade has decreased re-delegations to protect staker APY, since "re-delegations often cost more than they are able to deliver in value." This optimal behavior undermines SAM's validator value proposition—access to stake has diminished as validators await many epochs for meaningful Marinade delegations.

**Solution:** Allow validators to bid for stake priority. Stake priority assigns solely based on validator bids. Higher-bid validators receive allocations sooner than lower-bidders. Validators will pay for activating stake portions. Payment equals the difference between actual bid and current active stake payment. Non-activating portions remain unchanged.

### 2. Introduce a Bond Risk Reduction Mechanism

Monitoring over two quarters identified inefficiency: validators SAM must undelegate due to insufficient bond coverage. Leaving such validators staked would expose stakers to downtime or commission rug losses.

The **Bond Risk Reduction Mechanism reduces re-delegation costs by incentivizing validators to promptly top up bonds** to remain staked or properly exit by withdrawing bonds entirely—triggering standard Marinade re-delegation.

**Addressing evasion concerns:** Validators might exit to avoid penalties then re-enter later. However, this behavior proves uneconomical. Re-entry requires considerable time reaching previous stake levels. Combined with new activating stake payments, stake acquisition no longer arrives free. These factors render dodging unprofitable.

Implementation ensures only long-term exit validators choose leaving. Others maintain properly topped bonds, reducing re-delegation costs and improving staker APY.

### 3. Abandon MNDE Enhanced Stake

Though designed to give MNDE holders meaningful stake distribution influence, practice shows minimal usage and no material validator cap changes recently. "Maintaining this mechanism therefore adds complexity to the delegation system without delivering proportional benefits."

This proposal abandons MNDE Enhanced Stake, simplifying infrastructure and governance while allowing focus on improvements directly enhancing capital efficiency and staker APY.

### 4. Increase maximum Stake a single Validator can obtain to 15% of TVL

SAM's core strength: highest-yielding validators receive stake and earn rewarded commissions. This ensures stakers achieve best market APY.

**Proposal:** Increase per-validator stake cap to 15% of TVL. Current 4% cap artificially fragments stake among inferior-yield validators, diluting returns. Higher caps reward proven performers and boost staker APY.

This proposal authorizes Marinade Labs gradual cap increases across at least two rounds.

ASO and Country concentration limits remain unchanged.

---

## Conclusion

SAM directs stake toward superior-returning validators, ensuring optimal staker APY. MIP-19 refreshes the system for evolved market conditions—making stake allocation more efficient and reducing wasteful re-delegation costs, ultimately delivering enhanced SAM performance and superior staker returns.

**Vote YES to support these updates; otherwise vote NO and provide forum feedback.**

---

*Proposal voting went live on Realms December 22, 2025.*
