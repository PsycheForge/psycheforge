# Open Risks

Risks that are not blockers for the PoC but MUST be tracked and closed before mainnet. Each risk has a resolution criterion — specific evidence that lets it close.

This is the public version of the risks doc. Internal strategy notes (specific price assumptions, competitive positioning, pivot scenarios) are tracked separately and not part of this repo.

---

## Risk A — Market validation is unvalidated

**Status:** **Resolved (2026-04-22)** — see closure note below
**Owner:** Mike
**Severity:** Was High — now historical

**Description:** The assumption that Solana DAO participants (delegates, treasury managers, or similar users) will pay for structured governance analysis was a PoC-stage hypothesis. Target segment, pricing, and value proposition were working assumptions.

**Resolution criteria (all met):**

- ✅ ≥5 real interviews with active Solana DAO participants (anonymous / pseudonymous, common in Web3 governance)
- ✅ ≥3 interviewees showed clear interest (strong-yes or soft-yes with specific feedback)
- ✅ ≥2 described governance pain points in their own words unprompted
- ✅ At least 1 written expression of beta intent (received via pseudonymous channel)

**Closure note (2026-04-22):**

Findings broadly match the patterns identified pre-interview:

- **Fragmentation pain** (forum + Discord + Realms + X dispersion) is the dominant unprompted concern.
- **Hallucination resistance** and **verifiable accuracy** are the trust prerequisites — the skill's grounding-citation requirement and the on-chain reputation program directly address both.
- **Pricing tolerance maps to a two-tier model** (entry-level retail tier + premium tier) rather than a single-tier $35-45 retail assumption. The whale / treasury-manager segment carries the higher willingness to pay; retail tolerates only a much smaller monthly fee. **Specific price bands are tracked privately** — not committed to this repo because it is competitive information that may shift with further interviews.

**Open follow-on work** (now in the active sprint, not a risk):

- Adapt skill scope and product packaging to a two-tier model (lite vs premium).
- v0.2 prompt iteration based on the N=7 batch findings (see `eval/outputs/batch_n7_devnet_report.md` §"Prompt v0.2 roadmap").
- Grow on-chain track record toward N=20+ for accuracy validation.

Detailed interview notes are kept private (anonymity commitment to interviewees). This closure record is intentionally generic so the public repo does not leak strategic detail.

---

## Risk B — Accuracy metric is game-able

**Status:** Partially resolved at the program layer; public red-team exercise pending devnet deploy
**Owner:** Mike + agent dev
**Severity:** Medium (down from High — mathematical foundation is proven)

**Description:** A naive "% correct predictions" metric can be gamed by avoiding difficult proposals. An agent that only predicts obvious outcomes could claim 95% accuracy without producing real delegate value.

**Mitigation:** Difficulty-weighted scoring + coverage metric, implemented in the reputation Anchor program. The core math:

- Each prediction's contribution to the agent's score is `correctness_bps × difficulty_bps`.
- Difficulty for a unanimous proposal is ~0 → the prediction contributes ~0 to both numerator and denominator.
- An agent predicting only unanimous proposals has `numerator / denominator ≈ 0 / 0` — undefined, shown as "insufficient data", not a high score.
- Coverage (`total_predictions / eligible_proposals_seen`) is surfaced alongside accuracy so gaming by silence is visible.

Full derivation in `docs/reputation-program-design.md` §5. Unit tests proving each gaming scenario in `onchain/tests/reputation.ts` under `red-team scenarios`.

**Resolution criteria progress:**

- ✅ Formula implemented in `onchain/programs/reputation/src/lib.rs` (v0.1).
- ✅ Unit tests show gaming yields near-zero score — 6 canonical red-team scenarios, all green.
- ✅ Devnet deployment live (2026-04-22) — [`85huMKVbSddkbZiSk4XUBUSxsZS39tbd3sLp17viJJqH`](https://explorer.solana.com/address/85huMKVbSddkbZiSk4XUBUSxsZS39tbd3sLp17viJJqH?cluster=devnet). Full lifecycle exercised; anyone can audit.
- 🚧 Public red-team invitation (external adversarial testers attempting to game a live scoreboard, not just unit tests) — outstanding.

---

## Risk C — Regulatory / investment-advisor exposure

**Status:** Open (launch blocker, not build blocker)
**Owner:** Mike
**Severity:** Medium — unlikely to kill the project, could force jurisdictional changes

**Description:** Paid "governance recommendations" on token-denominated DAOs could trigger investment-advisor rules in some jurisdictions — particularly US (SEC), UK (FCA), and EU (MiCA). Risk is higher for DAOs where votes directly affect token economics.

**Mitigation (phased):**

*PoC / devnet phase:*

- Both skills (`governance-triage` and `prediction-writer`) enforce a hard rule in their system prompts: **no vote recommendation, ever**. Output is analysis and outcome prediction only. This is load-bearing for the regulatory posture and is asserted in prompt text and in fixture expected-behaviors.
- Prominent disclaimer on any user-facing output: "PsycheForge provides analysis and outcome predictions, not investment or voting advice. All governance decisions are the user's responsibility."
- No US onboarding for paid tiers until a legal opinion is obtained.

*Before mainnet launch:*

- Consultation with a crypto-savvy firm (Wilson Sonsini, Anderson Kill, or equivalent) — classification memo + jurisdictional allow/block list.

**Resolution criteria:**

- Disclaimer copy reviewed and deployed on any user-facing surface.
- Legal consultation completed; summary committed to `docs/legal-opinion-summary.md`.
- Jurisdiction policy documented (served countries, blocked countries, gating mechanism).

---

## How to use this file

1. Update status when progress is made — do not let stale status entries accumulate.
2. Weekly review of aging risks.
3. Closing a risk requires all resolution criteria met + a short closure note committed here.
4. New risks get added here immediately, not in scattered issues.

**Note (2026-04-21):** Development is running in parallel with customer discovery. The core skill chain has reached demo-ready state (all canonical fixtures pass + one correct prediction on a real proposal). Risk A remains the dominant open risk and will be addressed through real user interviews using the working demo.

**Update (2026-04-22):** Risk A closed — interviews completed, two-tier pricing model adopted. Active sprint now focuses on v0.2 prompt iteration + lite-vs-premium tier scoping + N=20 accuracy validation. Risk B's "public red-team invitation" is the next-largest open item.
