# Reputation Program — Design Document (v0.1.0)

**Status:** Implemented + deployed to Solana devnet (2026-04-22) at [`85huMKVbSddkbZiSk4XUBUSxsZS39tbd3sLp17viJJqH`](https://explorer.solana.com/address/85huMKVbSddkbZiSk4XUBUSxsZS39tbd3sLp17viJJqH?cluster=devnet). All 7 instructions live in `onchain/programs/reputation/src/lib.rs`; 31 tests passing on localnet (including 6 red-team gaming-resistance scenarios); full lifecycle exercised on devnet.
**Last updated:** 2026-04-22
**Purpose:** Design contract for the on-chain reputation program. Frozen for v0.1. Changes to account layout or scoring math from this point forward require a versioned migration plan.

---

## 1. Goals

1. **Verifiable Accuracy** — Every prediction is recorded on-chain and can be independently verified.
2. **Gaming Resistance** — Make it mathematically hard to achieve high accuracy by only predicting easy proposals (Risk B).
3. **Difficulty-Weighted Scoring** — Correct predictions on contested proposals are worth significantly more.
4. **Coverage Transparency** — Display both accuracy and coverage so "gaming by silence" is obvious.

**Out of scope for v0.1:**
- Solana Agent Registry / SATI integration
- Commit-reveal or prediction privacy
- Direct CPI into SPL-Governance / Realms
- Slashing or economic incentives

---

## 2. Key Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| Outcome Resolution | Trusted resolver writes final outcome | Simplest and sufficient for v0.1 |
| Prediction Storage | Public at submission time | Commit-reveal adds too much complexity for PoC |
| Score Math | Basis points (u64 / u128) | No floats on-chain |
| Agent Identity | Simple Pubkey | Full identity belongs to Agent Registry (future) |
| Proposal Identification | 32-byte hash (proposal_id) | DAO-agnostic — works across Jupiter, Marinade, etc. |
| Difficulty Calculation | Off-chain by resolver | Keeps on-chain code simple and auditable |
| Resolver Rotation | `ProgramConfig` PDA + `transfer_resolver` instruction | Path to multisig/Squads without program redeploy |

---

## 3. Account Layout

Every struct ends with a `_reserved` padding field so later field additions don't require a breaking migration. Anchor handles the 8-byte discriminator implicitly.

### 3.1 Proposal PDA

**Seeds:** `["proposal", proposal_id]`

```rust
pub struct Proposal {
    pub proposal_id: [u8; 32],
    pub dao_id: [u8; 32],
    pub voting_closes_at_slot: u64,
    pub num_choices: u8,
    pub resolved: bool,
    pub final_outcome: u8,                    // 0..num_choices-1
    pub vote_distribution_bps: [u16; 8],      // sum must = 10_000
    pub difficulty_bps: u16,                  // 0 = unanimous, 10000 = max entropy
    pub resolver: Pubkey,
    pub resolved_at_slot: u64,
    pub _reserved: [u8; 32],
}
```

### 3.2 AgentReputation PDA

**Seeds:** `["reputation", agent_pubkey]`

```rust
pub struct AgentReputation {
    pub agent_pubkey: Pubkey,
    pub total_predictions: u64,
    pub total_resolved: u64,
    pub weighted_correct_numerator: u128,      // Σ (correctness * difficulty)
    pub weighted_difficulty_denominator: u128, // Σ difficulty
    pub eligible_proposals_seen: u64,
    pub _reserved: [u8; 64],
}
```

### 3.3 Prediction PDA

**Seeds:** `["prediction", proposal_id, agent_pubkey]`

```rust
pub struct Prediction {
    pub agent: Pubkey,
    pub proposal_id: [u8; 32],
    pub predicted_outcome: u8,
    pub submitted_at_slot: u64,
    pub resolved: bool,
    pub correctness_bps: u16,        // 10000 = correct, 0 = wrong
    pub score_contribution: u64,
    pub _reserved: [u8; 32],
}
```

### 3.4 ProgramConfig PDA

**Seeds:** `["config"]`

Set once at program deploy time by the upgrade authority. Mutated only by `transfer_resolver`. To move to a multisig, set `resolver` to a Squads vault PDA — no program change required.

```rust
pub struct ProgramConfig {
    pub resolver: Pubkey,
    pub _reserved: [u8; 64],
}
```

---

## 4. Instruction Surface

Six instructions. The `resolve_proposal` / `finalize_prediction` split is deliberate: the resolver posts an outcome once per proposal (O(proposals)), then `finalize_prediction` can be cranked permissionlessly per-agent in parallel (O(predictions)). A combined instruction would force the resolver to scale with total predictions.

| Instruction | Signer | What it does | Key checks |
|---|---|---|---|
| `register_agent()` | agent | Creates `AgentReputation` PDA, zeroes counters | PDA must not exist |
| `create_proposal(proposal_id, dao_id, voting_closes_at_slot, num_choices)` | resolver | Creates `Proposal` PDA | `num_choices ∈ [2..8]`, `voting_closes_at_slot > current_slot` |
| `submit_prediction(proposal_id, predicted_outcome)` | agent | Creates `Prediction` PDA, increments `AgentReputation.total_predictions` | `current_slot < voting_closes_at_slot`, `predicted_outcome < num_choices`, PDA must not exist |
| `resolve_proposal(proposal_id, vote_distribution_bps, final_outcome, difficulty_bps)` | resolver | Writes outcome + difficulty onto `Proposal`, sets `resolved = true` | `sum(vote_distribution_bps) == 10_000`, `difficulty_bps ≤ 10_000`, `!resolved` |
| `finalize_prediction(proposal_id, agent_pubkey)` | permissionless | Reads resolved `Proposal`, computes `correctness_bps` + `score_contribution`, updates `AgentReputation` numerator / denominator / `total_resolved` | `Proposal.resolved`, `!Prediction.resolved` |
| `transfer_resolver(new_resolver)` | current resolver | Rotates resolver in `ProgramConfig` | signer == current resolver |

---

## 5. Scoring Math (v0.1)

**Difficulty** (computed off-chain by resolver, validated on-chain):

```
difficulty_bps = (entropy / log2(num_choices)) * 10000
```

**Correctness:**
- `10000` if prediction matches final outcome
- `0` otherwise

**Agent Accuracy:**

```
accuracy_bps = weighted_correct_numerator / weighted_difficulty_denominator
```

**Coverage:**

```
coverage_bps = (total_predictions * 10000) / eligible_proposals_seen
```

**Gaming Resistance:** If an agent only predicts unanimous proposals, `difficulty_bps ≈ 0`, so contributions to both numerator and denominator approach 0 — the predictions are score-neutral. Coverage drops visibly. Scenarios in §6 prove the math works in both directions.

---

## 6. Red-Team Scenarios (must pass as unit tests)

Risk B resolution requires that all six pass before mainnet:

| # | Strategy | Expected accuracy | Expected coverage |
|---|---|---|---|
| 1 | Predict everything correctly | ~10000 | 10000 |
| 2 | Predict everything wrong | 0 | 10000 |
| 3 | Only predict unanimous proposals, always correct | undefined / near-zero | very low |
| 4 | Only easy proposals correctly + one hard proposal correctly | high accuracy, low coverage (visible weakness) | low |
| 5 | Contested correct, unanimous wrong | ~10000 — unanimous errors weighted 0, contested correct weighted high | 10000 |
| 6 | Contested wrong, unanimous right | ~0 — contested errors drag; unanimous right contributes 0 | 10000 |

Scenarios 5 and 6 are the **positive direction** of the proof — they show that difficulty weighting actually differentiates, not just that easy proposals get zeroed out. A skeptical reviewer will look for these explicitly.

---

## 7. Decisions Carried Forward

Defaults locked in for v0.1. Revisit if customer-discovery or adversarial signal warrants.

1. **Coverage indexing: off-chain.** On-chain iteration over all registered agents at resolve time is infeasible. Coverage is computed by an off-chain indexer reading `Proposal` creation + `Prediction` submission events. The on-chain `eligible_proposals_seen` counter is advisory; the authoritative value comes from the indexer. Documented as a known v0.1 limitation.
2. **Resolver authority: single key, rotatable.** A single key for devnet, transferable to a multisig or Squads vault via `transfer_resolver`. Multisig is mandatory before mainnet — tracked in the deploy checklist rather than re-litigated here.
3. **Proposal creation: resolver-only.** Permissionless creation opens spam vectors with no corresponding incentive model in v0.1. Resolver-only is the safer default. Re-evaluate once we have economic incentives (staking, fees) designed.
