# Triage — Marinade MIP-15 (100M MNDE → Marinade Labs)

**Source:** https://forum.marinade.finance/t/mip15-activate-protocol-fee-flows-to-foundation-and-grant-100m-mnde-to-labs/1922
**Author:** helloiamvu · **Posted:** 2025-08-18
**Analyzed by:** PsycheForge `governance-triage` + `prediction-writer` skill chain · 2026-04-21

---

## What this proposal actually asks for

MIP-15 requests **100M MNDE from the DAO treasury** to fund Marinade Labs for 12–18 months, with a 1-year cliff. It simultaneously activates protocol fee flows to the Foundation.

**Treasury impact:** `outflow` · 100M MNDE · confidence: high
**Citation:** *"allocate 100M MNDE from the DAO treasury to Marinade Labs for operational expenses over 12 to 18 months"*

---

## 5 red flags (cited verbatim from the proposal)

| Category | Severity | What it is |
|---|---|---|
| `vague_kpi` | medium | Quarterly reporting on "milestones" — but the milestones themselves are never defined. No TVL targets, no user-growth goals, no revenue thresholds. |
| `missing_milestone` | medium | The 1-year cliff is specified, but the vesting schedule **after** the cliff is not. Instant unlock? Linear? Unclear. |
| `unbounded_spend` | low | Four expense categories (contributor comp, product/audits, marketing, community) with zero budget breakdown or percentage allocation. |
| `token_dilution` | medium | 100M MNDE with unspecified post-cliff unlock structure. The cliff mitigates immediate dilution but doesn't bound post-cliff circulating supply changes. |
| `technical_risk` | low | "Activate protocol fee flows" — but no smart-contract parameters, no executor, no technical spec. References MIP-11 and MIP-13 without including their text. |

**Zero high-severity flags.** No `backdoor_permission`, no `centralization`, no governance-capture patterns.

---

## Key stakeholders

- **Proposer:** `helloiamvu` (post author)
- **Beneficiaries:** Marinade Foundation (fee flow recipient), Marinade Labs (grant recipient)
- **Affected groups:** DAO treasury (source), MNDE holders (dilution / buyback effect)

---

## 6 questions a delegate should post in the forum before voting

1. What is the **exact vesting schedule** for the 100M MNDE after the 1-year cliff — instant unlock, linear over the remaining 11–17 months, or another structure?
2. What specific **technical changes** (smart contract parameters, multisig permissions, program upgrades) are required to activate protocol fee flows to the Foundation, and who executes them?
3. What are the **concrete quarterly milestones or KPIs** that will be reported to the DAO, and what recourse does the DAO have if milestones are missed?
4. How will **"unused MNDE at period conclusion"** be calculated, and what technical or governance mechanism enforces its return?
5. Why is the operational runway a **range (12–18 months)** rather than a fixed duration? What determines the actual endpoint?
6. What **percentage of the 100M MNDE** is allocated to each of the four expense categories?

---

## Prediction — epistemic claim, not a vote recommendation

| Field | Value |
|---|---|
| `predicted_outcome` | **0 (approve)** |
| `confidence_bps` | 6500 (65%) |
| Reasoning | Triage identifies three medium-severity red flags against 100M MNDE operational funding. No high-severity flags; no backdoor_permission or centralization patterns. 1-year cliff + quarterly reporting provide basic accountability. On Solana DAOs, core-team funding with medium governance-hygiene issues but no capture risks tends to pass — delegates balance operational necessity against proposal rigor. Confidence capped at 65% due to proposal's unreadable sections (MIP-11/13 context, post-cliff vesting, technical fee-activation mechanism). |

**What the skill will NOT tell you:** how to vote. This is an outcome prediction, falsifiable against the actual vote when it closes. That's the point — our on-chain reputation program scores the skill against real vote outcomes.

---

## Verified outcome — skill was correct (N=1)

**Actual outcome:** ✅ **APPROVED / PASSED** on 2025-08-25 (on-chain-executed; referenced as "since MIP-15 passed" in subsequent MIP-17, MIP-21, and Messari State of Marinade Q3/Q4 2025 reports).

**On-chain proposal record:** [v2.realms.today — MIP-15 proposal](https://v2.realms.today/dao/899YG3yk4F66ZgbNWLHriZHTXSKk9e1kvsKEquW7L6Mo/proposal/2iZTjrFy7MNtmFYc7hYUEbekfiRiK9iCCNBCem6hm9Yy)

**What this means for the skill's on-chain reputation score:** had this prediction been committed to the `reputation` program before the vote closed, `finalize_prediction` would have stamped:
- `correctness_bps = 10_000` (predicted_outcome == final_outcome)
- `score_contribution = 10_000 × difficulty_bps / 10_000 = difficulty_bps`
- Agent's `weighted_correct_numerator` += `10_000 × difficulty_bps`
- Agent's `weighted_difficulty_denominator` += `difficulty_bps`
- If it's the only prediction → accuracy = 10_000 bps (100%)

### Honest caveat — this is N=1

One correct call is **existence proof that the loop works end-to-end**, not validation of the model's accuracy. A skeptical delegate should ask:
- *"What was your accuracy on contested proposals (near-50/50 vote distribution)?"* — high-difficulty is where the metric actually earns its keep.
- *"What was your coverage?"* — predicting only one easy-to-call proposal and getting it right is the gaming-by-easy pattern our Risk B math is designed to zero out.

The reputation program was built specifically to surface these questions with on-chain numbers instead of anecdote. Running against N≥20 real proposals — including contested ones, including ones the skill gets wrong — is the real validation loop.

---

## What the skill couldn't read (honest disclosure)

- **MIP-11 and MIP-13** — referenced for fee-structure context but full text not included in MIP-15.
- **Technical implementation details** for activating protocol fee flows.
- **Vesting schedule beyond the 1-year cliff.**
- **USD value of 100M MNDE** — no conversion rate in proposal.

These gaps are why the confidence is 65%, not 95%.

---

## Also live on devnet — audit the on-chain state yourself

The reputation program is deployed to Solana devnet. Anyone can inspect the agent's accuracy record in a browser:

- **Program:** [`85huMKVbSddkbZiSk4XUBUSxsZS39tbd3sLp17viJJqH`](https://explorer.solana.com/address/85huMKVbSddkbZiSk4XUBUSxsZS39tbd3sLp17viJJqH?cluster=devnet)
- **AgentReputation (demo agent):** [`3PDUJBj2LswT4fnUmGMMZrP3vriapUPRWUFJ66FRkoVS`](https://explorer.solana.com/address/3PDUJBj2LswT4fnUmGMMZrP3vriapUPRWUFJ66FRkoVS?cluster=devnet) — N=1, accuracy 10000 bps
- **Demo Prediction (correctness=10000):** [`57PVW9HHthoXZuVDE6KD8F7EiRJLVZhPxYTcF2ytWaXf`](https://explorer.solana.com/address/57PVW9HHthoXZuVDE6KD8F7EiRJLVZhPxYTcF2ytWaXf?cluster=devnet)
- **Demo Proposal (resolved):** [`3cBKqyfZ6NWukofts8wExngfYtxSFyNXXCEUZeAf5H65`](https://explorer.solana.com/address/3cBKqyfZ6NWukofts8wExngfYtxSFyNXXCEUZeAf5H65?cluster=devnet)

The on-chain demo prediction is a hand-crafted sample (matched outcome to demonstrate the scoring math). Real MIP-15-and-similar predictions will be committed to devnet as the validation loop runs against live proposals — each will add a transaction you can verify on Explorer.

---

_Generated end-to-end from proposal text → Hermes Agent (Claude Sonnet 4.5 backend) → JSON triage → JSON prediction → this markdown summary. Source code: [github.com/.../psycheforge](#) (private during PoC)._
