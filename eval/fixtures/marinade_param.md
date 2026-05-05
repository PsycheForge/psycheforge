---
name: marinade_parameter_change
source_url: https://forum.marinade.finance/t/sample-mip-param
dao_context: "Marinade Finance, MNDE token, SOL liquid staking protocol"
expected_behaviors:
  - "treasury_impact.direction=none"
  - "red_flags, if present, must be grounded in real verification gaps (missing PR links, missing audit artifacts, missing instruction hashes) — NOT fabricated systemic concerns"
  - "No red_flag with category=backdoor_permission, token_dilution, or unbounded_spend (none apply here)"
  - "confidence.overall is medium or high"
  - "summary accurately reflects quorum threshold reduction from 5% to 3%"
  - "questions_to_ask are technical/scoping, not financial"
---

# MIP-47: Lower quorum threshold for operational parameter votes

**Author:** Marinade core contributor (@mndeOps)
**Date:** 2026-04-12
**Type:** Parameter change

## Summary

Reduce the quorum requirement for operational-category votes from 5% to 3% of circulating MNDE. Strategic and treasury votes remain at 5%.

## Motivation

Operational votes have failed quorum 4 times in the last quarter despite >70% approval on counted votes. The 5% threshold was calibrated when MNDE circulation was lower; with current float it effectively blocks routine parameter maintenance.

## Spec

- `operational_quorum_bps`: 500 → 300
- Affected instructions (whitelisted by hash): `set_validator_commission_cap`, `adjust_emission_param`, `set_validator_score_cap`
- Non-operational vote categories unchanged.
- Change applies at the next epoch boundary after passage.

## Risks

- Slightly increased risk of narrow-participation operational changes. Mitigated by:
  (a) 7-day on-forum discussion window unchanged before any vote opens;
  (b) operational scope is explicitly enumerated by instruction hash — the new threshold cannot be used for treasury moves or code upgrades.

## Implementation

Already tested on devnet (epoch 512). PR: `marinade-finance/governance#841`. Audit diff: unchanged from previous quorum-parameter audit (2025-11).

## Treasury impact

None. This is a parameter-only change; no MNDE or SOL movement.
