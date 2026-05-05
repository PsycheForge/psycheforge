---
name: live_marinade_mip20_buy_and_distribute
source_url: https://forum.marinade.finance/t/mip-20-stopping-burning-mnde-and-starting-buy-and-distribute-mechanism/1970
dao_context: "Marinade Finance DAO, MNDE token, replace burn mechanism with buy-and-distribute (fetched 2026-05-04). VERY SHORT proposal — minimal text, expected to surface as 'unreadable_sections' / low confidence."
is_live: true
expected_behaviors:
  - "Skill should classify confidence.overall as LOW given how minimal the proposal text is"
  - "Multiple unreadable_sections expected — buyback amount, frequency, claim mechanism details, VeMNDE power weighting formula, all unspecified"
  - "treasury_impact.direction is internal_transfer or unknown — protocol revenue used for buybacks then distributed"
  - "Red flag token_dilution expected (v0.2 trigger) — supply trajectory change: replacing burn (deflationary) with buy-and-distribute (rewards holders, not deflationary in same way)"
  - "Red flag vague_kpi expected — 'maybe weekly', 'significantly bring more value' qualitative without thresholds"
  - "Red flag missing_milestone expected — no implementation timeline, no first-buyback date"
  - "Red flag unbounded_spend possible — no cap on buyback budget per cycle"
  - "stakeholders should include berkantsc (proposer), VeMNDE holders (beneficiary), MNDE holders broadly (affected_group)"
  - "questions_to_ask should probe: exact buyback amount per cycle, claim mechanism, gas/keeper architecture, transition from current burn"
  - "Prediction is genuinely uncertain — short proposals with light specifics often go to discussion phase rather than directly to vote. Confidence should be ≤ 5500 bps."
---

# MIP-20: Stopping Burning MNDE and Starting Buy and Distribute Mechanism

**Author:** berkantsc
**Date:** December 21, 2025, 5:41am

---

## Proposal

For MNDE, According to VeMNDE power, Every end of the months Protocol revenue will buy back MNDE on open market maybe weekly, and there will be claim rewards option for VeMNDE holders.

This proposes that instead of burning MNDE tokens, Marinade should implement a buyback and distribution model where:

- Protocol revenue purchases MNDE tokens from the open market (potentially weekly)
- VeMNDE holders gain the ability to claim proportional rewards
- Distributions would be allocated based on each participant's VeMNDE power
- Stakers can reinvest claimed tokens

## Rationale

Many projects apply Buy and Distribute projects instead of burning mechanism. This approach will significantly bring more value to MNDE ecosystem.

---

*Note: This proposal as posted is brief and lacks formal abstract / motivation / specification / accountability sections common in other MIPs. Specifics — exact buyback budget, frequency, claim cadence, transition timeline, VeMNDE power formula — are not included in the post.*
