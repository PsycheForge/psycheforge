# Governance Triage — Test Cases

Canonical evaluation cases for the `governance-triage` skill. These are used by the eval harness (`eval/`) and should be rerun whenever the skill is revised. Each case maps to a fixture file whose YAML frontmatter encodes the expected behaviors.

## 1. Jupiter treasury grant (vague KPIs)

**Fixture:** `eval/fixtures/jupiter_grant.md`

**What it tests:** `vague_kpi` detection and treasury outflow classification on a realistic community-growth grant with soft success metrics.

**Expected behaviors:**

- At least one `red_flag` with `category: vague_kpi` — the Success Metrics section is non-measurable.
- `treasury_impact.direction = "outflow"`, `amount_usd ≈ 250000`.
- `stakeholders` includes `@daoScribe` as `proposer`.
- `questions_to_ask` probes concrete KPI definitions or disbursement controls.

**Failure meaning:** If `vague_kpi` is not flagged, the skill over-trusts well-formatted proposals. This is the most common production failure mode for generic LLMs and must be caught.

## 2. Marinade parameter change (low-risk with verification gaps)

**Fixture:** `eval/fixtures/marinade_param.md`

**What it tests:** Calibration on a low-risk parameter change that still contains legitimate verification gaps (unlinked PR, un-included audit, unenumerated instruction hashes). Ensures the skill neither fabricates systemic concerns (over-flagging) nor ignores real gaps (under-flagging).

**Expected behaviors:**

- `treasury_impact.direction = "none"`.
- `red_flags`, if present, must be grounded in real verification gaps — e.g. `technical_risk` for missing PR links, audit artifacts, or instruction hashes. NOT fabricated systemic concerns (no `backdoor_permission`, `token_dilution`, or `unbounded_spend` — none apply here).
- `confidence.overall` is `medium` or `high`.
- `summary` accurately reflects the quorum threshold reduction from 5% to 3%.
- `questions_to_ask` are technical / scoping, not financial.

**Failure meaning:** Either direction is bad. Fabricating red flags on clean proposals erodes trust ("over-cautious skill"); missing the real verification gaps means the skill is just rubber-stamping. The model should find what a careful delegate would find — no more, no less.

## 3. Adversarial buried permission (canary)

**Fixture:** `eval/fixtures/adversarial_permission.md`

**What it tests:** The primary hallucination guard. A proposal framed as a UX + documentation refresh that buries an upgrade-authority rotation in Appendix A item 3.

**Expected behaviors:**

- At least one `red_flag` with `category: backdoor_permission`.
- That `red_flag` has `severity: "high"`.
- The flag's `citation` quotes or references Appendix A item 3 (upgrade authority rotation to `ops_v2` keypair).
- `questions_to_ask` includes a question about the upgrade authority, multisig rotation, or the `ops_v2` keypair.
- `summary` does NOT describe the proposal as purely a UX or docs change.

**Failure meaning:** If the model misses this case, the skill is not production-trustworthy for any customer segment. Before shipping, tighten instructions (emphasize equal-rigor appendix scanning) or add a few-shot example that demonstrates appendix-threat detection.

## Adding a new test case

Each test case is a Markdown fixture in `eval/fixtures/` with YAML frontmatter:

```yaml
---
name: short_slug
source_url: https://...
dao_context: "DAO name, token, treasury context"
expected_behaviors:
  - "Human-readable expectation 1"
  - "Human-readable expectation 2"
---
```

The eval harness reads the body as `proposal_text` and prints `expected_behaviors` alongside model output for manual review. Document the new case here under a numbered section so the canonical set stays discoverable.
