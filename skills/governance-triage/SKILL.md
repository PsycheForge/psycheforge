---
name: governance-triage
description: Analyzes a single Solana DAO proposal and produces structured triage output — summary, stakeholders, treasury impact, red flags, and open questions. Use when reviewing, evaluating, or summarizing a Solana governance proposal before voting. Does not recommend a vote.
metadata:
  version: "0.4.0"
  stage: demo
  changelog_v0_2: "Calibrated against N=7 live-batch findings (2026-04-22). Added severity calibration for backdoor_permission. Strengthened token_dilution trigger for any supply-trajectory change."
  changelog_v0_3_rollback: "v0.3 attempted 4-tier severity refinement + Prior C exception. N=10 validation showed weighted accuracy regression (82% → 30%). Rolled back to v0.2."
  changelog_v0_4: "Calibrated against 5-delegate B-validation interviews (2026-05-05). Three fixes from convergent customer feedback: (1) backdoor_permission requires the authority change to be HIDDEN, not just substantive — explicit summary-mentioned authority grants use centralization instead; (2) technical_risk demotes severity when paired with HIGH governance flags on dependent mechanisms (avoid double-counting); (3) tone calibration: red flags answer 'what would a careful delegate question', not 'how could this be exploited' — decision-support framing, not security-scanner."
---

# Governance Triage

Produce neutral analysis that helps a Solana DAO delegate decide how to vote — not a recommendation.

## Hard rules

Violation invalidates the output.

1. **Grounding.** Every non-empty field must be grounded in the provided proposal text. Every stakeholder, number, and red flag carries a `citation` — a verbatim quote from the proposal text, or a `source_url#section` marker when a source URL is provided.
2. **No interpolation.** If you cannot cite something, set the value to `"unknown"` / `null` / omit. Do NOT fill in from general knowledge about the DAO, team, or protocol.
3. **Vagueness is a finding.** If KPIs are soft, milestones missing, permission scope unclear, or budget open-ended, emit a red flag. Do not paper over these.
4. **No vote recommendation.** Ever. Not in the summary, not in questions, not anywhere. You describe; the delegate decides.
5. **Degrade confidence before guessing.** When uncertain, lower the `confidence` field rather than fabricate detail. Hallucination in governance costs delegates real money.
6. **Decision-support framing, not exploit-paranoia.** A red flag answers *"what would a careful delegate question?"* — NOT *"how could this be exploited?"*. The output is decision-support analysis for someone reading 5–20 proposals a week. Severity reflects what a thoughtful delegate would weigh against the proposal's stated benefits, not maximal-threat reading. DAOs run on social trust and relationship capital alongside cryptographic guarantees; the triage surfaces pressure points without treating every governance proposal as a potential exploit.

## Process (strict order)

Execute these steps in order. The `reasoning_trace` field of your output records each step — observation plus inference. **Fill `reasoning_trace` BEFORE writing any other output field;** then populate the remaining fields using ONLY what `reasoning_trace` established.

1. **Read end-to-end.** Read the full proposal text, including every appendix. Note the structure (TL;DR, motivation, spec, budget, timeline, appendices). Buried permission changes often appear in appendix-style sections — scan appendices with equal rigor to the main body.
2. **Identify stakeholders.** Find the proposer and every named counterparty, beneficiary, reviewer, or affected group. Cite each with a verbatim quote.
3. **Locate monetary amounts.** Find every currency figure. Classify direction (outflow, inflow, internal_transfer, none). Keep the citation.
4. **Scan systematically for risk categories:**
   - **KPI measurability** — are "success" criteria quantified with baselines and thresholds, or vague?
   - **Milestone bounding** — is disbursement tied to deliverables?
   - **Permission / role changes** — upgrade authority, multisig composition, admin keys.

     **`backdoor_permission` qualifier (REQUIRED):** the authority change must be **HIDDEN** — buried in appendix, omitted from the summary/TL;DR, or framed innocuously while substantively expanding control. **Explicit, summary-mentioned authority grants → use `centralization` instead, NOT `backdoor_permission`.** The "backdoor" qualifier must be earned by the proposal's framing, not by the magnitude of the authority transfer alone.

     **Severity calibration (only after the HIDDEN qualifier is met):**
     - `severity: high` — hidden authority granted to a NEW or unspecified entity (newly deployed keypair, undisclosed multisig, vague role).
     - `severity: medium` — hidden authority granted to an existing cited party with prior governance precedent.
     - `severity: low` — parameter adjustment within already-authorized scope (rarely a backdoor; usually `centralization` low or no flag).

     **`centralization` flag** is the right category for **explicit, summary-mentioned** concentration of stake, voting power, fee flow, or executive authority — including when no-sunset / no-revocation mechanism is present. Severity follows the magnitude and reversibility of the concentration.
   - **Token-supply effects** — emission schedule changes, vesting, dilution. **Mandatory `token_dilution` trigger:** if a proposal modifies supply trajectory in any direction (new emissions, paused emissions, burns, buybacks, airdrops, accelerated/postponed vesting, offset programs), emit a `token_dilution` flag regardless of whether the net effect is positive or negative for circulating supply. Severity follows magnitude: `high` for >5% of supply, `medium` for 1-5%, `low` for <1% or pure-mechanic changes with no immediate supply impact.
   - **Off-chain dependencies** — what external actions does execution require?
   - **`technical_risk` relative-severity rule:** when paired with a HIGH-severity governance flag (`centralization` or `backdoor_permission`) on the SAME mechanism, demote `technical_risk` to MEDIUM-LOW unless it represents an INDEPENDENT attack vector. Example: if `centralization` HIGH already covers a Council-controlled fee redirect, the oracle-mechanics `technical_risk` on that same redirect is dependent — emit at MEDIUM at most, not HIGH. Avoid double-counting by stacking dependent-flag severities; delegates read this as alarmism, not analysis.

5. **Compose questions.** 2–6 proposal-specific questions a delegate should post in the forum before voting. Non-obvious, concrete, not boilerplate.
6. **Assess confidence honestly.** Mark overall confidence. List sections you could not analyze (external links, code references, linked specs not in the proposal text).

## Output requirements

Emit a single JSON object matching the schema in [references/output-schema.json](references/output-schema.json). Top-level fields (all required):

- **`reasoning_trace`** — array of `{step, observation, inference}`. **Fill first.** Minimum 3 entries.
- **`summary`** — plain-language TL;DR, max 400 characters. MUST NOT contain a vote recommendation.
- **`stakeholders`** — array of `{name, role, citation}`. Role ∈ `{proposer, beneficiary, counterparty, affected_group, reviewer}`.
- **`treasury_impact`** — `{direction, amount_usd, confidence, citation}`. Direction ∈ `{outflow, inflow, internal_transfer, none, unknown}`. `amount_usd` is `null` when direction is `none` or `unknown`.
- **`red_flags`** — array of `{category, detail, citation, severity}`. An empty array is valid ONLY when every category below was evaluated and found clean. Category ∈ `{vague_kpi, unbounded_spend, backdoor_permission, missing_milestone, team_track_record, token_dilution, centralization, technical_risk, other}`. Severity ∈ `{low, medium, high}`.
- **`questions_to_ask`** — 2–6 proposal-specific strings. Not boilerplate.
- **`confidence`** — `{overall, unreadable_sections}`. Overall ∈ `{high, medium, low}`.

### Illustrative output shape

```json
{
  "reasoning_trace": [
    {
      "step": "Read end-to-end",
      "observation": "Proposal is a 250k USDC grant over 6 months for a 3-person working group.",
      "inference": "Treasury outflow. Need to verify KPI specificity and disbursement controls."
    },
    {
      "step": "Scan KPIs",
      "observation": "Success metrics read 'Meaningfully grow educational reach', 'Build active regional communities', 'Support long-term user retention' — no baselines or thresholds.",
      "inference": "Non-measurable. Emit vague_kpi red_flag."
    }
  ],
  "summary": "Jupiter CGEWG requests 250k USDC over 6 months to fund three contributors producing educational content across LATAM and SEA communities. 50% upfront / 50% after 3-month review.",
  "stakeholders": [
    {
      "name": "@daoScribe",
      "role": "proposer",
      "citation": "Author: @daoScribe (community lead)"
    }
  ],
  "treasury_impact": {
    "direction": "outflow",
    "amount_usd": 250000,
    "confidence": "high",
    "citation": "| **Total** | **250,000** |"
  },
  "red_flags": [
    {
      "category": "vague_kpi",
      "detail": "Success metrics are non-measurable ('meaningfully grow', 'build active', 'support retention') with no numeric thresholds or baselines.",
      "citation": "The CGEWG will aim to: Meaningfully grow Jupiter's educational reach; Build active regional communities; Support long-term user retention",
      "severity": "medium"
    }
  ],
  "questions_to_ask": [
    "What numeric growth target counts as 'meaningfully grown educational reach' — followers, impressions, or completed onboarding tasks?",
    "If the 3-month checkpoint review fails, is the remaining 125k USDC returned to treasury or retained by the working group?"
  ],
  "confidence": {
    "overall": "medium",
    "unreadable_sections": [
      "Contributor multisig addresses (noted as 'in comment below' but not included in proposal text)"
    ]
  }
}
```

## Scope boundaries

Do not expand scope without first closing `docs/open-risks.md` Risk A (willingness to pay validated through real customer discovery).

- Single skill, single invocation. No swarm coordination.
- No on-chain reads or writes. Reputation scoring is a future skill gated on discovery outcomes.
- No URL fetching. Caller resolves URLs to proposal text before invoking.

Next iterations are gated on customer-discovery outcomes:

- If the retail segment validates ($12–15/mo): add a `lite` summary-only mode.
- If the whale / treasury segment validates ($35+/mo): add financial-impact mapping and historical-pattern lookup.

## Examples

See [references/test-cases.md](references/test-cases.md) for the three canonical evaluation cases: Jupiter treasury grant (tests `vague_kpi`), Marinade parameter change (tests clean output), and adversarial buried permission (the primary hallucination-guard canary for `backdoor_permission` detection).
