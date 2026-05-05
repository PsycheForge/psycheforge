# Infrastructure Assumptions

This document records every external infrastructure claim the PsycheForge architecture depends on. Every row has a source URL, a verification date, and an invalidation trigger. If something breaks during build, find the matching row and check whether the assumption still holds.

**Last full review:** 2026-04-21
**Reviewed by:** Mike (user-verified, pre-build check)
**Verification method:** Manual web research against official sources. Claims are reviewer-attested, not AI-attested — the coding assistant has not independently verified the URLs below.

---

## 1. Hermes 4.3 was post-trained on Psyche network

- **Claim:** Hermes 4.3 is the first production model fully post-trained on the Psyche network, using Solana-secured decentralized compute with the DisTrO optimizer. Announced December 2025 (release ~December 3, 2025). The Psyche-trained version outperformed centralized training.
- **Why it matters:** Justifies building on the Hermes agent framework as a Solana/DePIN-native model rather than a bolt-on.
- **Source:** https://nousresearch.com/introducing-hermes-4-3/ (official blog)
  Additional: https://huggingface.co/NousResearch/Hermes-4.3-36B
- **Last checked:** 2026-04-21
- **Invalidation triggers:**
  - Nous deprecates 4.3 without a 4.4 successor on the same stack
  - Psyche post-training moves off Solana
  - DisTrO optimizer replaced with a closed-source alternative

## 2. Solana Agent Registry is live and writable

- **Claim:** Solana Agent Registry launched March 2026 (approximately March 2–3, 2026). Provides on-chain verifiable identity, portable reputation, and third-party attestations. Solana implementation of the ERC-8004 protocol, developed with Quantu AI (SATI/SAID integration). SATI dashboard is active.
- **Why it matters:** Our entire "verifiable accuracy" moat depends on this registry being live, writable from our reputation program, and readable by third-party dashboards.
- **Source:** https://solana.com/agent-registry (official page)
  Additional: https://solana.com/news/solana-ecosystem-roundup-march-2026
- **Last checked:** 2026-04-21
- **Invalidation triggers:**
  - Registry goes read-only or permissioned
  - Schema changes in an incompatible way
  - Per-write fees make per-prediction writes uneconomical
  - Major dashboard integrations drop support

## 3. io.net H100 pricing

- **Claim:** On-demand H100 GPU-hour is in the approximate $1.00–$2.50 range (April 2026). io.net promotions show a $1/hr floor; the broader DePIN/spot market is $1.38–$2.69. Significantly cheaper than AWS.
- **Why it matters:** Break-even math (2–3 paying delegates covers skill-evolution compute) assumes this price band. A sustained +50% price move kills unit economics.
- **Source:** https://io.net/p/h100-gpu-for-discount/ (io.net official pricing)
  Additional comparison: https://www.thundercompute.com/blog/nvidia-h100-pricing (April 2026 snapshot)
- **Last checked:** 2026-04-21
- **Invalidation triggers:**
  - H100 availability drops and sustained price >$3/hr
  - Hermes inference workload size changes such that per-delegate cost crosses $2/month
  - io.net deprecates Ray-based workflow in favor of something our client doesn't support

## 4. io.net IDE (Incentive Dynamic Engine) rollout

- **Claim:** Full IDE implementation is planned for Q2 2026. Litepaper December 2025, community feedback closed end of Feb 2026, final design end of March 2026. Currently in the transition phase; will go live in Q2 2026.
- **Why it matters:** Changes how we pay for compute — token-denominated incentives vs. USDC. Affects the billing abstraction in `compute/io_net_client.py` and may change unit economics.
- **Source:** https://io.net/blog/the-quick-guide-to-the-incentive-dynamic-engine
  Additional: https://io.net/tokenomics and the litepaper
- **Last checked:** 2026-04-21
- **Invalidation triggers:**
  - IDE delayed past Q3 2026 (our compute client needs to handle transition indefinitely)
  - Final design changes payment flow such that USDC rails no longer work
  - Incentive structure rewards running nodes rather than renting compute, shifting our role

## 5. Skill format: agentskills.io SKILL.md standard

- **Claim:** Hermes Agent uses the agentskills.io open standard (originally developed by Anthropic, adopted by 40+ agent products including Claude Code, Cursor, GitHub Copilot, Hermes Agent). Skills are directories containing a `SKILL.md` (YAML frontmatter + Markdown body), plus optional `scripts/`, `references/`, `assets/` subdirectories. Required frontmatter: `name`, `description`. Optional: `license`, `compatibility`, `metadata`, `allowed-tools`.
- **Why it matters:** Every skill we ship binds to this format. Spec changes (new required fields, deprecation of `allowed-tools`, changes to body-loading semantics) would force a migration across every skill.
- **Source:** https://agentskills.io/specification
  Additional: https://github.com/agentskills/agentskills (reference library, validator)
- **Last checked:** 2026-04-21
- **Invalidation triggers:**
  - Spec changes `name` or `description` constraints incompatibly
  - Spec adds required fields we do not currently populate
  - Hermes Agent diverges from the open standard
  - The standard loses critical ecosystem adoption (e.g. Anthropic withdraws stewardship)

---

## How to use this file

1. Before any architecture change that depends on one of these claims, re-check the source URL.
2. If a claim is invalidated, open an issue tagged `infra-drift` and block related PRs until resolved.
3. Do a full re-review every 60 days, or before any mainnet deploy.
4. Add new claims here as the codebase depends on new external infra — never let an unreviewed assumption get buried in code.
5. When adding a claim, always include: statement, why-it-matters, source URL, date, and at least one concrete invalidation trigger. If you can't name an invalidation trigger, you don't understand the dependency well enough yet.
