# PsycheForge — Landing Copy (v1, post-customer-discovery)

This is copy ready to paste into a landing page, a Twitter thread, an outreach DM, or a one-pager PDF. Structure is layered: hero first, deeper sections below. Every claim with a number maps back to the validation work in `eval/outputs/`.

---

## Hero

**Structured triage for Solana DAO delegates.**

Red flags with verbatim citations, stakeholders, treasury impact, and the questions worth asking — for any governance proposal, in 30 seconds.

PsycheForge surfaces what speed-readers miss. It does not tell you how to vote.

---

## Subhead (~80 words)

Solana governance moves fast. Marinade, Jupiter, Jito, Sanctum, Kamino — every week brings 5–20 proposals, each with forum threads, on-chain mechanics, and economic implications buried under operational language. PsycheForge runs a calibrated, citation-grounded analysis of any proposal text and returns a structured triage: what the proposal actually does, who benefits, what's vague, what's missing, and what a careful delegate should question before voting. The skill is hard-ruled to never recommend a vote — only to make the analysis explicit.

---

## What you get (Lite tier)

For any proposal you paste in, PsycheForge returns a structured analysis in under a minute:

- **TL;DR** — what the proposal actually does (not what it claims to do)
- **Treasury impact** — direction, amount, with verbatim citation from the proposal
- **Red flags** — categorized, severity-rated, each with a verbatim citation. No fabrication: if the skill cannot point to a specific quote in the proposal, the flag does not exist.
- **Stakeholders** — proposer, beneficiaries, affected groups, counterparties — each cited
- **Open questions** — 2–6 proposal-specific questions worth posting in the forum before the vote closes
- **Honest gaps** — what the skill could not analyze (external links, undisclosed addresses, linked specs)

Output is markdown, shareable, auditable. Sample analysis on Marinade MIP-21: [view sample →](../eval/outputs/lite_sample_jupiter_v02.md)

---

## Why this is different

We deliberately do not include vote-outcome predictions in the user-facing tier. Predictions sound impressive in a demo and degrade trust in production — coin-flip accuracy on contested votes does more damage than missing predictions entirely. The on-chain reputation infrastructure that scores predictions exists, runs on Solana devnet, and is in active calibration. It will return as a public-facing claim only after N≥50 calibrated accuracy is demonstrable. Until then: triage only.

The output is **decision-support**, not a security scanner. A red flag answers *"what would a careful delegate question?"* — not *"how could this be exploited?"*. DAOs run on social trust and relationship capital alongside cryptographic guarantees; the triage surfaces pressure points without treating every governance proposal as a potential attack.

---

## Voices from delegate validation (anonymized)

Five active Solana DAO delegates ran a real PsycheForge triage of Marinade MIP-21 (a recent treasury-authority proposal that passed 99.6/0.4) and answered four questions about whether the structured format actually helps decision-making. All five reported strong-yes value. Quotes below are verbatim, names withheld at delegates' request.

> *"The strongest part of the triage is surfacing hidden implementation assumptions that are easy to gloss over. The ambiguity around 'equivalent MNDE value' would have slipped past me on a quick read."*
> — **Builder-perspective delegate, governance-conscious**

> *"Governance proposals often sound economically reasonable while quietly weakening enforcement guarantees. The analysis did a good job exposing the implicit power transfer."*
> — **Trust-architecture delegate**

> *"The hard part isn't reading proposals — it's quickly spotting economic downside and incentive shifts. If the tool reliably surfaces that, it saves real time. I'd use it several times a week."*
> — **Tokenomics-focused delegate**

> *"Most delegates skim the majority of proposals. If the tool can consistently surface the actual decision-critical risks, that's valuable. Probably daily during active governance cycles."*
> — **Multi-DAO active delegate**

> *"During heavy governance cycles, helping people quickly understand 'why this proposal is controversial' is genuinely useful — community sensemaking, not raw analysis."*
> — **Community-builder delegate**

5/5 reported strong-yes on Q2 ("did this catch something you wouldn't have"). 5/5 priced subscription positively in the $20–150/month range conditional on calibration discipline (low false-positive rate). Aggregate report: [`eval/outputs/b_validation_test_pack.md`](../eval/outputs/b_validation_test_pack.md).

---

## Pricing — three tiers

Pricing is calibrated to delegate workflow intensity, not feature gates. Every tier returns the same triage quality on every proposal it covers.

| Tier | Monthly | DAO coverage | Best for |
|---|---|---|---|
| **Lite** | $25 | 1–2 DAOs of your choice | Retail delegate weekly-reading governance, sensemaking-leaning |
| **Standard** | $50 | Multi-DAO across active Solana governance | Active delegate, treasury / authority / fee proposal focus, weekly+ |
| **Premium** | $100 | Comprehensive coverage + alpha-grade insights | Whale, treasury manager, yield researcher, daily during cycles |

What is **not** different across tiers: hard rule against vote recommendations, citation-grounding requirement, decision-support framing. The skill is the same; the breadth of coverage and depth of context differ.

What is **not** in any tier yet: vote-outcome predictions (deferred until N≥50 calibration). On-chain reputation history (built, paused as a marketing claim until accuracy is demonstrable).

A 14-day pilot is available for early users — no charge, no credit card, in exchange for one written interview at the end about whether the tool actually changed how you read proposals.

---

## FAQ

**Why no vote recommendation?**
Two reasons. First, regulatory: paid governance recommendations on token-denominated DAOs may trigger investment-advisor rules in some jurisdictions. Second, epistemic: the skill cannot know your portfolio context, your DAO history, or your tolerance for governance-mechanic vs token-economic concerns. Telling you how to vote would be theater. Surfacing what's worth questioning is real.

**How do you prevent hallucination?**
Every claim in the output carries a verbatim citation from the proposal text. If the skill cannot quote the source, the claim does not appear. Vagueness in the source is itself surfaced as a finding (`vague_kpi`, `missing_milestone`, etc.) — the skill does not paper over it. We track citation-grounding rate as a calibration KPI; current rate is 100% across N=10 live proposals tested.

**What about prediction accuracy?**
A previous iteration of the product included on-chain vote-outcome predictions. At N=7 live Solana DAO proposals, weighted accuracy was coin-flip range (51%). That layer is paused as a user-facing feature until N≥50 calibrated accuracy is demonstrable. The reputation program infrastructure remains built and live on Solana devnet. Honest disclosure here: [`eval/outputs/batch_n7_devnet_report.md`](../eval/outputs/batch_n7_devnet_report.md).

**What proposals can it analyze?**
Any proposal where you can paste the text. Currently: Marinade (Discourse forum), Jupiter (research forum), Jito (Discourse forum), Sanctum (Discourse, partial), generic Realms-anchored DAOs. URL-fetching for known DAO forums is on the roadmap; for now, paste the proposal body.

**How fast is it?**
~30–60 seconds per proposal, depending on length. The skill runs through the Hermes Agent framework with a Claude Sonnet 4.5 backend by default. Self-hosted backends (Nous Portal, OpenRouter, etc.) are supported via a single `.env` config.

---

## Open source

Everything described above is in a public repository under MIT license. The skill prompts, the Anchor program, the test fixtures, the validation reports — all open. Pricing and customer discovery interview notes are kept private.

If you can read the prompt, you can audit the skill. If you can compute `weighted_correct_numerator / weighted_difficulty_denominator`, you can audit the on-chain reputation. The trust model is "verify, don't trust."

---

## Beta sign-up CTA

> Two minutes to a working triage on a proposal you actually care about.
>
> **Send a DM with:** the URL of a Solana DAO proposal you're currently weighing. We'll reply within 4 hours with a Lite-tier triage of that proposal, free, no commitment. If it changes how you read the proposal, the 14-day pilot is on us in exchange for one short interview at the end.
>
> If it doesn't change anything, no follow-up. We are not interested in selling tools that do not earn delegate trust.

DM target: `@psycheforge` on X, or via the GitHub repo issues.

---

*Calibration disclosure: PsycheForge is a PoC. Customer discovery completed 2026-05-05 (5 anonymized interviews; aggregate signal in repo). Risk register: [`docs/open-risks.md`](open-risks.md). PoC stage means: real value confirmed in interviews, but no paying users yet, and the public Lite tier is not generally available — beta only. We expect to learn things in the beta that change the copy above. Honest version-control over confident claims.*
