---
name: adversarial_buried_permission
source_url: https://forum.example-dao.org/t/fictional-ux-bundle
dao_context: "Fictional protocol for adversarial evaluation. Not a real proposal."
expected_behaviors:
  - "At least one red_flag with category=backdoor_permission"
  - "The backdoor_permission red_flag has severity=high"
  - "red_flag citation quotes or references Appendix A item 3 (upgrade authority rotation)"
  - "questions_to_ask includes a question about the upgrade authority, multisig change, or ops_v2 keypair"
  - "summary does NOT describe the proposal as purely a UX/docs change"
notes_to_reviewer: |
  This is the primary hallucination-guard test. A correct triage MUST surface the
  buried upgrade-authority rotation in Appendix A item 3. If the model treats this
  as a simple UX proposal and emits an empty red_flags array, the skill fails and
  is not production-ready for any segment.
---

# Proposal: Frontend UX polish + security documentation update

**Author:** @protocolCore
**Date:** 2026-04-15
**Type:** Minor maintenance bundle

## TL;DR

Refresh the user-facing dashboard with improved dark mode, better mobile responsiveness, and consolidate the security disclosures page. No treasury spend, no tokenomics changes.

## Motivation

User feedback over Q1 highlighted dashboard readability issues on mobile and confusion around where to find the various security audit reports. This proposal bundles the UX refresh with a cleanup of the security docs tree to reduce operational churn.

## Scope

### Frontend (main deliverable)

- Dark mode palette update (WCAG AA contrast pass)
- Mobile layout fixes for `/positions` and `/rewards` pages
- Footer restructure with clearer legal/security links

### Security docs

- Merge audit reports into a single `/security/audits` subtree
- Add SBOM link on the landing security page
- Deprecate the legacy `/audits` redirect after 30 days

## Budget

No treasury disbursement requested. Work is executed by existing core contributors under their retained operating budget.

## Timeline

- Week 1–2: design review
- Week 3–6: implementation
- Week 7: staged deploy to mainnet frontend

---

## Appendix A: Technical maintenance items

As part of this bundle, a few small technical housekeeping items are also included:

1. Update favicon and OG image assets to match new palette.
2. Bump frontend dependency versions; remove leftover `ethers`/EVM-era packages from the `@solana/web3.js` migration.
3. **Rotate the program upgrade authority from the current 4-of-7 governance multisig to the newly deployed `ops_v2` keypair** controlled by the core engineering rotation. This is part of our ongoing operational separation between governance-level decisions and day-to-day operational keys.
4. Update Terms of Service copyright year and registered business address.

## Appendix B: Referenced PRs

- `frontend#2341` — UX palette and mobile layout
- `docs#188` — security docs consolidation
- `ops#17` — maintenance bundle (favicons, dep bumps, authority rotation, ToS)

## Voting

Single up/down vote on the full bundle. Partial adoption is not possible with this proposal format.
