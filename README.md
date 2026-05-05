# PsycheForge

> Structured governance triage for Solana DAO delegates: red flags with verbatim citations, stakeholders, treasury impact, and the questions a delegate should ask before voting.

PsycheForge produces a 30-second structured analysis of a Solana DAO governance proposal. Every claim is grounded in a verbatim citation from the proposal text. Vagueness is itself a finding. The skill **never** recommends how to vote — it surfaces what's worth questioning.

---

## Status: PoC, post-pivot to triage-only (2026-05-05)

The product is the **`governance-triage` skill output**: a JSON-or-markdown structured analysis a delegate can read in 30 seconds. Citation-grounded, no hallucination, no vote recommendation.

- **What works:**
  - `governance-triage` skill produces structured triage on real governance proposals. Citation-grounding 7/7 across the live test batch. Red flag categories: `vague_kpi`, `backdoor_permission`, `centralization`, `token_dilution`, `unbounded_spend`, `missing_milestone`, `team_track_record`, `technical_risk`, `other` (e.g. bundling anti-pattern).
  - [`format_triage.py`](eval/format_triage.py) renders the JSON output as a clean delegate-facing markdown summary. Sample: [`eval/outputs/lite_sample_jupiter_v02.md`](eval/outputs/lite_sample_jupiter_v02.md).
- **Internal research, not user-facing:**
  - `prediction-writer` skill — outputs vote-outcome predictions. At N=7 live proposals, weighted accuracy was coin-flip range (51%) — not yet a value-creating layer for users. Deferred until N=50+ validated. Skill remains in repo for calibration research; not surfaced in any user-facing tier.
  - On-chain reputation program (Anchor, 7 instructions, 31 tests, 6 red-team gaming-resistance scenarios proven). Deployed on devnet. Built but **not currently used as a marketing claim** until prediction quality improves.
- **What doesn't:**
  - Zero paying users. Next step: 5-delegate validation interviews using [`eval/outputs/b_validation_test_pack.md`](eval/outputs/b_validation_test_pack.md) — does triage-alone help a delegate make a decision? ≥4/5 yes → ship.

---

## Architecture

```
skills/
├── governance-triage/      # triage: stakeholders, red flags, treasury impact, questions
│   ├── SKILL.md
│   └── references/         # JSON schema + canonical test cases
└── prediction-writer/      # epistemic claim: predicted_outcome + confidence
    ├── SKILL.md
    └── references/

onchain/
├── programs/reputation/    # Anchor program (7 instructions)
│   └── src/lib.rs
├── tests/reputation.ts     # 31 tests including red-team scenarios
└── clients/                # TS CLIs: bootstrap, submit, resolve, finalize

eval/
├── fixtures/               # proposal markdowns (synthetic + live)
├── test_governance_triage.py
├── test_prediction_writer.py
├── setup_hermes_local.sh   # project-local Hermes install (no system changes)
└── outputs/                # example artifacts (e.g. live_mip15_demo.md)

docs/
├── reputation-program-design.md
├── infra-assumptions.md
└── open-risks.md
```

Skills follow the [agentskills.io](https://agentskills.io) open standard (Anthropic-originated, adopted by Hermes Agent, Claude Code, Cursor, and 40+ others) and run through the [Hermes Agent framework](https://github.com/NousResearch/hermes-agent) with any OpenAI-compatible LLM backend (Claude, OpenRouter, Nous, etc.).

---

## Quick start

Prereqs: Rust, Solana CLI 1.18+, Anchor CLI 0.30+, Node 20+ with Yarn, Python 3.11+.

```bash
# 1. Install Hermes Agent locally (no system changes, no PATH edits)
./eval/setup_hermes_local.sh

# 2. Configure a backend model (one-time)
echo 'OPENROUTER_API_KEY=sk-or-...' >> ~/.hermes/.env
.hermes-agent/venv/bin/hermes config set model anthropic/claude-sonnet-4.5

# 3. Run the skill chain on a live fixture (takes ~90s)
python eval/test_prediction_writer.py live_mip15_marinade_labs_grant.md --verbose

# 4. Build + test the on-chain program (localnet, ~60s)
cd onchain && yarn install && anchor test
```

**Full on-chain lifecycle demo** (in a fresh terminal):

```bash
# Start local validator
solana-test-validator --reset --quiet --ledger onchain/test-ledger &

# Deploy + bootstrap + submit + resolve + finalize
cd onchain
anchor deploy --provider.cluster localnet

yarn ts-node clients/bootstrap.ts \
  --resolver-keypair ~/.config/solana/id.json \
  --agent-keypair ~/.config/solana/id.json \
  --proposal-id 01ee000000000000000000000000000000000000000000000000000000000000 \
  --num-choices 2

yarn submit \
  --prediction ../eval/outputs/sample_prediction.json \
  --keypair ~/.config/solana/id.json \
  --proposal-id 01ee000000000000000000000000000000000000000000000000000000000000

yarn ts-node clients/resolve_proposal.ts \
  --resolver-keypair ~/.config/solana/id.json \
  --proposal-id 01ee000000000000000000000000000000000000000000000000000000000000 \
  --outcome 1 --distribution 4500,5500 --difficulty-bps 8000

yarn ts-node clients/finalize_prediction.ts \
  --cranker-keypair ~/.config/solana/id.json \
  --proposal-id 01ee000000000000000000000000000000000000000000000000000000000000 \
  --agent-pubkey <agent-pubkey>
```

When it's green: `accuracy_bps = 10_000` for the test agent because they predicted correctly on a difficulty-8000 vote.

---

## Key design decisions

- **Skills produce analysis and predictions. They never recommend how to vote.** This is a hard rule in both skill prompts — a distinction that matters for regulatory posture (see `docs/open-risks.md` Risk C) and for epistemic honesty (prediction is falsifiable; recommendation is advice).
- **Difficulty-weighted scoring.** Unanimous (easy-to-call) proposals contribute ~0 to both numerator and denominator. An agent that only predicts obvious outcomes gets mathematical accuracy ≈ `0/0` (undefined), not high accuracy. See `docs/reputation-program-design.md` §5 and §6.
- **Coverage is reported alongside accuracy.** Gaming by silence (skipping hard votes) is visible, not hidden.
- **Resolver is rotatable.** `ProgramConfig.resolver` controls who can create and resolve proposals; `transfer_resolver` lets you move it to a Squads multisig without redeploying the program.

See [`docs/reputation-program-design.md`](docs/reputation-program-design.md) for the full on-chain design.

---

## Verified artifact

[`eval/outputs/live_mip15_demo.md`](eval/outputs/live_mip15_demo.md) — a complete run on Marinade MIP-15 (a real 100M MNDE treasury proposal that passed on 2025-08-25). Includes:

- 5 red flags with verbatim citations
- 5 stakeholders identified
- 6 non-boilerplate delegate questions
- Prediction: `approve` at 65% confidence
- Outcome: passed — prediction correct
- Honest N=1 caveat

Open it as a sample of what the pipeline produces on real data.

---

## Contributing

This is a PoC. PRs welcome but please open an issue first — skill prompts and schemas are still being calibrated against live proposals.

Highest-value contributions right now:

- **New fixtures** from real Solana DAO proposals, especially **contested** ones (close vote distributions). Template: [`eval/fixtures/live_mip15_marinade_labs_grant.md`](eval/fixtures/live_mip15_marinade_labs_grant.md).
- **Red-team scenarios** that attack the reputation program's scoring math. Tests live in `onchain/tests/reputation.ts`.
- **Non-English governance** — Spanish, Turkish, Korean, Chinese DAO proposals to stress-test the skill's multilingual behavior.
- **Prompt tightening** for the specific failure modes you observe — please include the triage output that surfaced the issue.

Please do NOT submit PRs that turn the skill into a voting recommender. The "prediction, not recommendation" boundary is load-bearing.

---

## License

MIT — see [LICENSE](LICENSE).

---

*Not affiliated with Anthropic, Nous Research, Marinade Finance, or the Solana Foundation. Uses open-source components from each.*
