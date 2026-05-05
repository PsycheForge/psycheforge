# Product Tiers — Scope Boundaries (v0.1 of tier model)

**Status:** Draft, post-customer-discovery (2026-04-22). Architecture is settled; specific prices are tracked privately and may shift with further interviews.

---

## Two tiers map to two skills

| Tier | Skill stack | On-chain commit | Audit trail | Target user |
|---|---|---|---|---|
| **Lite** | `governance-triage` only | No | No | Retail delegate triaging multiple DAOs weekly |
| **Premium** | `governance-triage` → `prediction-writer` → `submit_prediction` | Yes | Yes (Reputation PDA on Solana) | Whale, treasury manager, organized delegation operator |

The tier split is **packaging**, not new code. Both tiers run on the same skill chain documented in `skills/`. The difference is whether the agent commits a prediction on-chain and accumulates a verifiable accuracy history.

## What Lite is

- **Input:** proposal URL or pasted text + DAO context.
- **Output:** structured triage JSON (red flags with citations, stakeholders, treasury impact, open questions, confidence + unreadable sections).
- **Hard rules from `governance-triage` SKILL.md apply unchanged:** no vote recommendation, every claim cited, vagueness is itself a finding.
- **Delivery:** API call returning JSON, optional human-readable markdown formatter (similar to `eval/outputs/live_mip15_demo.md` style).
- **Cost basis:** LLM tokens + minimal infrastructure. Pricing reflects this.

Lite is for the user who says "I follow Marinade and Jupiter, every week there are 3-5 proposals I should read but rarely have time, I want a 30-second summary that flags what to look at."

## What Premium adds on top of Lite

- **`prediction-writer` skill** runs after triage, producing a falsifiable outcome prediction (`predicted_outcome`, `confidence_bps`, `reasoning_citation`).
- **On-chain commit** via `submit_prediction.ts` — the prediction is written to the Solana reputation program before the vote closes.
- **Reputation accrual** — after vote resolves, `resolve_proposal` + `finalize_prediction` score the prediction difficulty-weighted. The agent's `weighted_correct_numerator` / `weighted_difficulty_denominator` becomes a public, auditable accuracy history.
- **Visible track record** — anyone can inspect the agent's Reputation PDA on Solana Explorer and verify the accuracy claim.
- **No vote recommendation** — same hard rule as Lite. Premium delivers a prediction (epistemic claim), not advice.

Premium is for the user who says "I steward $X of governance tokens. If I delegate triage decisions to a tool, I need to verify the tool was right historically. Marketing claims aren't enough; I want the receipts."

## Pricing — held private

Specific monthly fees for each tier are not committed to this repo. They were derived from customer-discovery interviews (anonymous, completed 2026-04-22) and are tracked in private notes. Two structural points are public:

- The tiers are **roughly 3× apart** in monthly fee. Premium's higher price is justified by the on-chain rent + reputation infrastructure + accountability story.
- Both tiers are **monthly subscription**, not per-call. Per-call billing matches usage but creates friction for "should I use this for this proposal?" — which is exactly the decision the tool should remove.

Pricing may move as N grows past 20+ proposals and accuracy hardens (or changes). Risk A is closed at the structural level (two-tier model validated) but specific fee experiments are post-PoC sprint work.

## What this does NOT decide

- **Whether Lite users see Premium's accuracy data.** They probably should — the public Reputation PDA is intrinsic to the trust story even for Lite users who don't contribute to it. But surfacing that in the Lite UX is a separate design question.
- **Free / freemium tier.** Not adopted in v0.1 of the tier model. Possible later if outreach shows a meaningful population that wants to "try one proposal before subscribing."
- **Per-DAO pricing.** A delegate active in only one DAO may want a single-DAO subscription. Not adopted now; tier is platform-wide.
- **Enterprise / B2B treasury manager tier.** The premium tier serves treasury managers in v0.1 by virtue of pricing alone. A dedicated B2B contract surface (custom integrations, white-label, SLA) is post-N=20 work.

## Implications for the codebase

- **No new skill files needed.** Both tiers use the existing `governance-triage` and `prediction-writer` skills.
- **`prediction-writer` invocation becomes tier-gated** at the API/UX layer. Lite tier API does not call `prediction-writer`.
- **`submit_prediction` and on-chain pipeline** stay invoked only for Premium. A non-paying or Lite caller never produces an on-chain prediction PDA.
- **Single agent reputation per Premium customer**, derived from their keypair. Lite customers do not have a reputation PDA.
- **Agent reputation account is per-customer-keypair**, not global. The "I have 51% accuracy on 7 proposals" story applies to *each* Premium customer's individual track record — it grows with their usage.

## Decisions tracked here vs. in `docs/open-risks.md`

This file describes the product packaging decided after customer discovery closed Risk A. It is not a risk register — it is a scope statement. When a tier-related decision is reversible and not yet locked in (e.g., "should we add a free tier?"), it stays here as an open question. When a tier-related concern is something that could break the project (e.g., "what if the on-chain rent costs swamp Premium economics?"), that goes into `open-risks.md` as a tracked risk.

For now, no tier-derived risks rise to the open-risks register. The architecture is conservative: free = nothing, Lite = LLM only, Premium = LLM + on-chain. Each tier's economics are independent.
