# Prediction Writer — Test Cases

The three canonical evaluation cases pair a governance-triage output pattern with the expected prediction direction + confidence band. These map to the same fixtures used by `governance-triage`.

## 1. Adversarial buried permission (expect: fail prediction)

**Triage shape:** ≥2 high-severity `red_flags` including `backdoor_permission`, summary names the buried authority rotation explicitly, `confidence.overall = medium` with unreadable ops_v2 keypair details.

**Expected prediction:**

- `predicted_outcome`: 1 (fail / no) for a binary vote where 0=pass, 1=fail. Caller supplies vote semantics; this case assumes standard DAO convention.
- `confidence_bps`: 6500-8000 (capped by medium triage confidence at 8000; high conviction but imperfect information about downstream vote behavior)
- `key_triage_signals`: should include `backdoor_permission:high`, `centralization:high` (or equivalent), bundling flag if present.
- `reasoning_citation`: must NOT use recommendation language. Should reference specific red_flags and the summary's framing.

**Failure meaning:** If the prediction inverts (predicts pass with high confidence), the skill is not weighting high-severity governance-key flags. If confidence exceeds 8000 despite medium triage confidence, Hard Rule #2 is violated.

## 2. Jupiter treasury grant with vague KPIs (expect: mixed-signal, moderate confidence)

**Triage shape:** One `vague_kpi` red_flag (medium severity), `treasury_impact.direction = "outflow"` ~$250k, questions_to_ask probes KPI definitions and disbursement controls, `confidence.overall = medium`.

**Expected prediction:**

- `predicted_outcome`: either 0 or 1 is defensible — this is a genuinely contested call.
- `confidence_bps`: 5000-6500. Should NOT exceed 7000 — single-flag proposals with mid-level concerns are coin-flips.
- `key_triage_signals`: should include `vague_kpi`, `treasury_impact:outflow:250000`, at least one stakeholder or question reference.
- `reasoning_citation`: acknowledge the ambiguity. Explicit language like "contested", "insufficient signal", or "moderate conviction" is healthy.

**Failure meaning:** High confidence in either direction (>7500) indicates the skill is over-extrapolating from a single-flag proposal.

## 3. Marinade parameter change (expect: pass, moderate-to-high confidence)

**Triage shape:** 0-2 `technical_risk` red_flags (medium severity at most), `treasury_impact.direction = "none"`, `confidence.overall = medium` or `high`, summary accurately describes the mechanical change.

**Expected prediction:**

- `predicted_outcome`: 0 (pass) for a binary vote.
- `confidence_bps`: 6500-8500. Marinade-style operational tweaks pass at high rates in DAOs with engaged operators; only genuine blocker red_flags should drop this below 6500.
- `key_triage_signals`: should include `treasury_impact:none` (positive signal), may include the technical_risk flags with a note that they are verification gaps, not blockers.
- `reasoning_citation`: should acknowledge that verification-gap flags reduce confidence but do not flip direction.

**Failure meaning:** Predicting fail on a clean parameter change is over-flagging — exactly the Marinade false-positive mode we calibrated against in the governance-triage test-cases. If the skill does this, add a prompt-level instruction that `technical_risk` flags on parameter-only changes with `treasury_impact.none` are NOT typically outcome-flipping.

## Adding a new test case

Pair a canned triage output JSON (saved as `eval/fixtures/triage-outputs/<slug>.json`) with a block here describing expected prediction behavior. The harness in `eval/test_prediction_writer.py` reads canned triage JSONs and feeds them into this skill — decouples prediction-writer testing from governance-triage stochasticity.
