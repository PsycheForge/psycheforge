---
name: live_marinade_mip14_burn_supply
source_url: https://forum.marinade.finance/t/mip-14-burn-5-50-of-mnde-total-supply
dao_context: "Marinade Finance DAO, MNDE token, two-stage opinion-then-execute vote on burning 5-50% of MNDE total supply (fetched 2026-05-04)"
is_live: true
multi_option: true
expected_behaviors:
  - "treasury_impact.direction is internal_transfer or none — burn removes supply but does not transfer to a counterparty (tokens destroyed)"
  - "Red flag token_dilution expected at HIGH severity (v0.2 trigger) — proposal explicitly modifies supply trajectory; magnitude is HIGH (5-50% of total supply, ~50M-500M MNDE)"
  - "Red flag missing_milestone possible — opinion vote is described but timing of follow-up burn instruction proposal is not specified ('After the opinion vote concludes, another DAO proposal will introduce an onchain burn instruction')"
  - "Red flag other expected — the **two-stage vote structure** itself is unusual: opinion vote selects %, separate binary vote executes. Skill should note this in red_flags or in summary as a structural observation."
  - "Skill should note num_choices ≠ 2 in proposal text — opinion vote has 7 options (No Burn, 5%, 10%, 20%, 30%, 40%, 50%). The binary vote that executes is downstream."
  - "Skill should NOT classify Marinade Foundation Council multisig as backdoor_permission HIGH — it is an existing cited multisig executing a vote-determined action. v0.3 4-tier severity: medium (existing cited multisig)."
  - "stakeholders include fisiroky (proposer), MNDE holders (affected_group via supply reduction), Marinade Foundation Council multisig (executor)"
  - "Outcome update is part of the proposal text: '30% of total MNDE supply was selected for burning' — skill should capture this in summary"
  - "Predicted outcome: this proposal is the OPINION VOTE. We treat 'approve' (0) as 'opinion vote concluded with a non-zero burn selected and executed'. Reality: the 30% burn was approved and submitted for execution, so outcome=0."
---

# MIP-14: Burn 5–50% of MNDE Total Supply

**Author:** fisiroky
**Date:** August 8, 2025

---

## Abstract

The proposal suggests conducting an opinion vote on burning **5–50% of the total MNDE supply** held in the DAO treasury. The selected burn amount would then be executed through the Realms-controlled treasury based on voting outcomes.

---

## Background and Context

* **Fixed supply:** MNDE operates with a hard cap of **1 billion tokens** and minting is permanently disabled.
* **Treasury overhang:** The DAO treasury holds approximately **564 million MNDE** (≈56.4% of supply), while circulating supply stands at roughly **430 million**.
* **Prior initiatives:** Recent proposals have explored buybacks, fee burns, and other deflationary mechanisms to strengthen token economics.

Burning between 50 million and 500 million MNDE would reduce the total supply to **950 million–500 million** and decrease treasury holdings to **593 million–143 million**, introducing immediate deflationary pressure aligned with DAO objectives.

---

## Rationale

**Overhang reduction:** With approximately 56.4% of supply sitting idle in the treasury, much of it will likely never be deployed. This excessive balance inflates fully diluted valuation relative to circulating market cap, dampening price performance. Burning a portion improves the market cap to FDV ratio and removes sentiment-suppressing overhang.

**Treasury capacity:** Even a 50% burn leaves at least 143 million MNDE available for future grants and liquidity incentives.

**Market confidence:** A transparent, onchain reduction demonstrates the DAO's commitment to sustainable tokenomics.

---

## Implementation

* **Opinion Vote:** A DAO proposal will initiate a multi-choice poll with seven options: **No Burn, 5%, 10%, 20%, 30%, 40%, 50%** of total MNDE supply.

* **Burn Tokens Instruction:** After the opinion vote concludes, another DAO proposal will introduce an onchain burn instruction for the amount receiving the most votes.

* **Execution:** Upon burn instruction proposal approval, the Marinade Foundation Council multisig follows the vote and executes the transaction and burn hash on official channels.

---

## Risks and Considerations

* **Irreversibility:** Burned tokens cannot be re-minted; excessive burning constrains future flexibility.
* **Opportunity Cost:** Burned tokens become unavailable for ecosystem growth grants or partnerships.
* **Informed Decision-Making:** The opinion vote requires thorough discourse and educational materials so participants understand tradeoffs across percentage options.

---

## Outcome

The community voted, and **30% of total MNDE supply** was selected for burning. A subsequent proposal was submitted to execute this burn on Realms.
