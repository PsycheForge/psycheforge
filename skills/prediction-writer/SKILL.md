---
name: prediction-writer
description: Converts a governance-triage analysis into a falsifiable prediction about a Solana DAO proposal's vote outcome. Use AFTER governance-triage when you have the structured triage JSON and need a commit-ready prediction (predicted_outcome + confidence) for the on-chain reputation program. Produces an epistemic claim, NOT a voting recommendation.
metadata:
  version: "0.2.0"
  stage: internal-research-only
  status: "Deprecated for user-facing tier (2026-05-05). The product pivoted to triage-only delivery (B+E pivot) — prediction quality at N=7 was coin-flip range and the on-chain reputation moat is paused until N=50+ calibrated accuracy is demonstrable. Skill remains in repo for internal calibration research; prompts and on-chain pipeline are not exposed in the user-facing tier."
  changelog_v0_2: "Calibrated against N=7 live-batch findings (2026-04-22). Added base-rate prior: when treasury_impact ∈ {none, internal_transfer} and no backdoor_permission HIGH is present, default toward approve — process-only flags do not flip predictions alone."
  changelog_v0_3_rollback: "v0.3 attempted Prior C exception for delegated execution; validation against N=10 showed weighted accuracy regression (82% → 30%). Rolled back to v0.2."
---

# Prediction Writer

Turn a governance-triage analysis into a committable prediction about how the vote will resolve.

## What this skill is — and what it is NOT

**This skill predicts the outcome of a governance vote.** You produce a falsifiable claim: "This proposal will pass / fail / resolve to outcome N", with a self-reported confidence. After the vote closes, the claim can be scored on-chain against the actual result.

**This skill does NOT recommend how the user should vote.** The distinction is load-bearing:

- *Recommendation*: "You should vote YES on this" — potentially regulated as investment advice (see `docs/open-risks.md` Risk C).
- *Prediction*: "Based on the triage signals, this proposal will likely FAIL with ~70% confidence" — epistemic claim, verifiable, commit-able to the reputation program.

When in doubt between the two framings, always choose prediction.

## Hard rules

Violation invalidates the output.

1. **Ground every claim in the provided triage JSON.** The triage output is your only trusted input. Do NOT use general knowledge about the DAO, team, or historical patterns outside what the triage surfaces. Cite triage fields by name (e.g. `red_flags[0].category`, `treasury_impact.direction`).
2. **Your confidence is capped by the triage's confidence.** If `triage.confidence.overall == "low"`, your `confidence_bps` MUST be ≤ 6000. If `triage.confidence.overall == "medium"`, cap is 8000. Only `"high"` triage confidence permits values up to 9500. Nothing ever exceeds 9500 — true certainty does not exist in governance.
3. **Confidence reflects epistemic humility, not conviction.** 5000 bps is a reasonable default. Values above 8000 require strong convergent signals from multiple triage fields.
4. **No vote recommendation. Ever.** Not in `reasoning_citation`, not in `key_triage_signals`. Describe your prediction and why — that is all.
5. **predicted_outcome must match the proposal's num_choices space.** For binary votes (yes/no), use 0 or 1. Do not emit values outside [0, num_choices-1].
6. **Honor the choice convention the caller pins.** The caller MUST provide a mapping (e.g. "index 0 = approve, index 1 = reject"). When pinned, use it verbatim — do not infer a different mapping. If no convention is pinned, state this explicitly in `reasoning_citation` and set `confidence_bps` to 0 — refuse to guess.

## Process (strict order)

1. **Parse the triage JSON fully.** Read `reasoning_trace`, `summary`, `stakeholders`, `treasury_impact`, `red_flags`, `questions_to_ask`, and `confidence`.

2. **Identify swing signals.** Which triage fields correlate with outcome? Apply these priors in order:

   **Prior A — Treasury-untouched proposals tend to pass.** When `treasury_impact.direction ∈ {none, internal_transfer}` AND no `backdoor_permission` flag is at `high` severity, default toward **approve**. Solana DAO communities — calibrated against N=7 live batch (2026-04-22) — tolerate process-only red flags (`vague_kpi`, `missing_milestone`, `technical_risk`, `unbounded_spend`) when no direct treasury drain is at stake. A `reject` prediction in this zone requires either (a) a `high`-severity `backdoor_permission` flag, OR (b) ≥3 stacked `high`-severity flags across distinct categories. Process-only `medium`-severity flags should NOT flip a prediction to reject on their own.

   **Prior B — Direct outflow + soft KPIs is mixed.** `treasury_impact.direction == "outflow"` with `vague_kpi` or `missing_milestone` flags → mixed prior. Outcome correlates with size (small grants pass; large grants with weak accountability fail) and team track-record signals when present in triage. Honest answer here is often `confidence_bps ≤ 5500` — coin-flip-acknowledging.

   **Prior C — Buried permission changes are the canary.** A `backdoor_permission` `high` red flag with a verbatim citation pointing to an appendix-section authority change → predict **reject** with `confidence_bps ≥ 7000` if triage confidence allows. This is the silent-governance-capture pattern; communities that read appendices reject these.

   **Prior D — Bundling anti-pattern.** When `red_flags` contains an `other` entry whose detail describes bundling unrelated decisions into a single vote, the bundling alone is rarely fatal. Combine with substance flags before predicting reject.

   **Prior E — Genuinely contested votes cap confidence.** If triage's reasoning_trace or summary signals broad community division (multi-option vote, near-even forum discussion, two factions surfaced as stakeholders), cap `confidence_bps` at 6500 regardless of how much you "want" to predict.

3. **Weight the triage's own confidence.** Apply the cap from Hard Rule #2. If the triage itself says "unreadable_sections" included critical artifacts (audit links, linked specs, keypair addresses), your prediction cannot be more confident than the triage — you're inheriting its blind spots.

4. **Pick the outcome and assign confidence.** Be honest. 5500 bps on a contested call is an acceptable and informative answer.

5. **Cite 2-6 specific triage fields in `key_triage_signals`.** Use the format `field.path:value` so downstream auditing is mechanical. Examples: `red_flag:backdoor_permission:high`, `treasury_impact:outflow:250000`, `stakeholders[0].role:proposer`.

6. **Write the reasoning citation.** 1-4 sentences grounded in the key signals. No general knowledge. No recommendation language.

## Output requirements

Emit a single JSON object matching [references/output-schema.json](references/output-schema.json):

```json
{
  "predicted_outcome": 0,
  "confidence_bps": 7500,
  "reasoning_citation": "Triage surfaces three high-severity red_flags (backdoor_permission, centralization, bundling anti-pattern) against a proposal framed as UX polish. The bundling flag forces delegates into all-or-nothing acceptance of an upgrade-authority rotation. When multiple governance-key flags are at high severity and the summary explicitly highlights the buried permission change, contested rejection is the base-rate outcome on Solana DAOs with active triage culture. Confidence capped at triage.confidence.overall=medium.",
  "key_triage_signals": [
    "red_flag:backdoor_permission:high",
    "red_flag:centralization:high",
    "red_flag:other:high (bundling)",
    "treasury_impact:none",
    "triage.confidence.overall:medium"
  ]
}
```

Required top-level fields:

- **`predicted_outcome`** — integer, 0..7. Must match the proposal's `num_choices - 1` upper bound (caller enforces this; skill assumes valid index).
- **`confidence_bps`** — integer, 0-10000. Respect the Hard Rule #2 cap.
- **`reasoning_citation`** — 50-800 chars. Cites specific triage fields.
- **`key_triage_signals`** — array of 2-6 strings. Format `<field_path>:<value>`. Not boilerplate.

## Scope boundaries

- Single-pass inference. No tool calls. No on-chain writes — the off-chain submitter handles commit.
- No external fetches. If triage lists `unreadable_sections`, those stay unreadable.
- Does not modify state anywhere.
- Does NOT decide `num_choices` — it comes from the proposal registry. The caller provides it.

## Examples

See [references/test-cases.md](references/test-cases.md) for the three canonical triage patterns and expected prediction direction + confidence range.
