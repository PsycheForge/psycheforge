---
name: live_jito_jip28_bam_adoption
source_url: https://forum.jito.network/t/jip-28-accelerate-bam-adoption/904
dao_context: "Jito DAO, JTO + JitoSOL tokens, BAM (Block Assembly Marketplace) adoption via tiered directed-staking. Depends on JIP-27. Fetched 2026-04-22."
is_live: true
expected_behaviors:
  - "treasury_impact.direction is 'none' — proposal states 'no direct DAO expenditure'"
  - "Red flag backdoor_permission EXPECTED and HIGH severity — 'six-month temporary control of Steward parameters' granted, with 'automatic revocation unless renewed' is a delegated-authority transfer of exactly the kind that reverses via silent renewal"
  - "Red flag technical_risk likely — BAM software is new (censorship-resistance / privacy / execution efficiency claims), validators run it at 'early-adoption risk'"
  - "Red flag centralization possible — directed staking concentrates JitoSOL stake at BAM-running validators, reducing validator-selection neutrality"
  - "Red flag missing_milestone likely — tier activation thresholds are described as 'BAM stakeweight reaching specified thresholds for two consecutive epochs' but the actual threshold numbers are not given"
  - "Skill should notice the JIP-27 dependency — this proposal is conditional on JIP-27 passing"
  - "stakeholders include drnick (proposer), BAM-running validators (beneficiary), non-BAM validators (affected_group losing stake share), Jito Foundation (resolver of BAM reporting)"
  - "questions_to_ask probes: exact stakeweight thresholds per tier, Steward-parameter control revocation mechanism, BAM software audit status"
---

# JIP-28: Accelerate BAM Adoption

**Author:** drnick
**Date:** October 28, 2025
**Category:** Treasury

## Abstract

This proposal establishes "a structured, tiered delegation model that rewards early adopters" of the Block Assembly Marketplace by allocating JitoSOL stake to validators running BAM software. It extends the Directed Staking framework (JIP-27) with BAM-specific eligibility criteria and tiered delegation triggers scaling with adoption metrics.

## Motivation

BAM enhances Solana block production through improved privacy, censorship resistance, and execution efficiency. The proposal aims to recognize validators absorbing early-adoption risk while ensuring predictable rewards and phased, safe BAM implementation.

## Key Specifications

**Delegation Criteria:**
- Eligible validators must operate BAM continuously for minimum three epochs
- Must maintain uptime within 3% of chain maximums
- Must meet JIP-27 criteria: 0% inflation fee, ≤10% Jito MEV commission, non-superminority status
- Distributions allocated pro rata to qualifying validators

**Tiered Activation Schedule:**
Each tier activates upon BAM stakeweight reaching specified thresholds for two consecutive epochs. The initial tier activates immediately upon JIP passage.

**Governance:**
- BAM adoption verified via StakeNet and Jito Foundation reporting
- Administered through Directed Staking infrastructure
- Epoch snapshots determine eligible validators and distributions
- Parameters remain governable via future JIPs

**Temporary Pool Management Control:**
The proposal requests six-month temporary control of Steward parameters enabling responsive stake cap management during the JIP-27/JIP-28 transition period, with automatic revocation unless renewed.

## Benefits

- Accelerates BAM network adoption
- Strengthens decentralization through phased onboarding
- Aligns JitoSOL strategy with Solana's technical roadmap

## Risks & Mitigation

Operational complexity addressed through JIP-27 infrastructure leverage.

**Cost:** No direct DAO expenditure.

**Contingency:** This JIP depends on JIP-27 passage.
