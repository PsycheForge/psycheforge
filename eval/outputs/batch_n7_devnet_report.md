> **Retraction note (2026-05-05):** Project pivoted to **triage-only** delivery. The 51.05% difficulty-weighted accuracy on this N=7 batch is coin-flip range — insufficient to claim "verifiable accuracy" as a user-facing moat. The on-chain reputation infrastructure remains built and tested, but is paused as a marketing claim until N=50+ calibrated accuracy is demonstrable. The 64.77% figure that includes the earlier hand-crafted demo is doubly misleading: that demo's prediction and resolve outcome were both authored by the same operator, so the 80M numerator contribution is not a real prediction win.
>
> **What this artifact retains:** evidence that the full skill-chain → on-chain pipeline works end-to-end (the engineering is sound), and a transparent calibration record showing the prediction layer's current limits. It is a PoC documentation artifact, not an accuracy claim. The product going forward is `governance-triage` skill output (Lite tier), which delivers value through citation-grounded structured analysis without a prediction layer. Track record below preserved for repo continuity.
>
> ---

# PsycheForge Devnet Batch N=7 — On-Chain Verifiable Performance

**Date:** 2026-04-21
**Agent pubkey:** [`6FxmgP46a8SBfuZdfR9G8iAKfBsRR9Xeg9CuQjFc5xQ4`](https://explorer.solana.com/address/6FxmgP46a8SBfuZdfR9G8iAKfBsRR9Xeg9CuQjFc5xQ4?cluster=devnet)
**Reputation program:** [`85huMKVbSddkbZiSk4XUBUSxsZS39tbd3sLp17viJJqH`](https://explorer.solana.com/address/85huMKVbSddkbZiSk4XUBUSxsZS39tbd3sLp17viJJqH?cluster=devnet) (Solana devnet)
**AgentReputation PDA:** [`3PDUJBj2LswT4fnUmGMMZrP3vriapUPRWUFJ66FRkoVS`](https://explorer.solana.com/address/3PDUJBj2LswT4fnUmGMMZrP3vriapUPRWUFJ66FRkoVS?cluster=devnet)

---

> An AI agent triaged 7 real Solana DAO proposals, committed its predictions on-chain **before** we knew the outcomes, and was scored difficulty-weighted after the votes closed. You can audit the score yourself in a browser.

---

## Current accuracy

**51.05%** — `accuracy_bps = 5105`, difficulty-weighted, batch-only, N=7.

```
weighted_correct_numerator:      104,960,000
weighted_difficulty_denominator:  20,558
accuracy_bps = numerator / denominator = 5105
```

Naive `correct / total` would be 4/7 = 57.1%. The difficulty weighting makes the real number **lower on purpose**: contested votes (near-50/50 split) contribute more weight, so getting those wrong hurts more than getting unanimous ones right. Easy calls cannot inflate the score. That's the anti-gaming property of the scoring math — full derivation in [`docs/reputation-program-design.md`](../../docs/reputation-program-design.md) §5-§6, red-team scenarios proven in [`onchain/tests/reputation.ts`](../../onchain/tests/reputation.ts).

## Per-proposal breakdown

Each row is one `Prediction` PDA on devnet. The "submit" column links to the transaction posted **before** the vote closed.

| # | Proposal | Difficulty | Predicted | Actual | Correct | Weight contribution |
|---|---|---:|---:|---:|:---:|---|
| 1 | [MIP-15 Marinade Labs grant](https://forum.marinade.finance/t/mip15-activate-protocol-fee-flows-to-foundation-and-grant-100m-mnde-to-labs/1922) | 812 | 0 approve | 0 approve | ✅ | num +8,120,000 · den +812 |
| 2 | [MIP-17 buybacks → liquidity](https://forum.marinade.finance/t/mip-17-refocusing-from-buybacks-to-building-liquidity/1960) | **0** (unanimous) | 0 approve | 0 approve | ✅ | 0 (weightless) |
| 3 | [MIP-18 fee structure revamp](https://forum.marinade.finance/t/mip-18-marinade-fee-structure-revamp-updated/1967) | **6,390** | 1 reject | 0 approve | ❌ | den +6,390 |
| 4 | [MIP-21 Council mSOL exchange](https://forum.marinade.finance/t/mip-21-exchange-msol-from-the-dao-treasury-with-the-council-wallet-and-redirect-fees-to-the-council-wallet/1975) | 812 | 1 reject | 0 approve | ❌ | den +812 |
| 5 | [Jupiter net-zero emissions](https://discuss.jup.ag/t/proposal-net-zero-emissions/39948) | **8,064** | 0 approve | 0 approve | ✅ | **num +80,640,000 · den +8,064** |
| 6 | [Jito JIP-26 CSD budget](https://forum.jito.network/t/jip-26-extend-the-budget-of-the-cryptoeconomics-subdao-csd/902) | 1,620 | 0 approve | 0 approve | ✅ | num +16,200,000 · den +1,620 |
| 7 | [Jito JIP-28 BAM adoption](https://forum.jito.network/t/jip-28-accelerate-bam-adoption/904) | 2,860 | 1 reject | 0 approve | ❌ | den +2,860 |

Prediction convention: `0` = approve/yes/pass, `1` = reject/no/fail. `Correct` column is the on-chain `correctness_bps` field (10000 if predicted == final, 0 otherwise).

## The highest-difficulty win: Jupiter net-zero emissions

This was the most contested proposal in the batch — entropy 0.81, a 75.3/24.7 split. **Difficulty: 8,064 bps**, the highest in the N=7.

The skill's triage flagged: `centralization` HIGH (Jupiter company becomes sole counterparty for team token absorption and Mercurial offset purchases), `other` medium (bundling three distinct emission sources into a single vote), `missing_milestone` medium (no defined criteria for revisiting the postponed 700M Jupuary allocation).

**Prediction:** `approve (0) @ 5500 bps confidence.` Close to coin-flip — reflecting genuine ambiguity, not conviction.

**Actual:** proposal passed. The prediction contributed **80,640,000** to the weighted numerator — **77% of the total weighted-correct signal on this batch comes from this one call on the hardest proposal**.

Remove Jupiter from the batch and the accuracy drops to ~19%. That's the point of difficulty weighting: the score remembers which calls mattered.

## The three honest losses

All three wrong predictions — MIP-18, MIP-21, JIP-28 — were `reject` calls on proposals the community then approved by wide margins (83.8/16.2, 99.6/0.4, 95/5).

| Wrong call | Why the skill rejected | Community's take |
|---|---|---|
| **MIP-18** (fee revamp) | `technical_risk` HIGH: conditional performance fee rate never specified in the proposal. | Approved 83.8/16.2 — community trusts the team to pin the rate post-vote. |
| **MIP-21** (Council mSOL) | `backdoor_permission` HIGH + `centralization` HIGH: fee redirect to Council wallet with no on-chain sunset mechanism. | Approved 99.6/0.4 — MNDE holders trust the Council relationship the skill flagged as concerning. |
| **JIP-28** (BAM adoption) | `unbounded_spend` HIGH + `backdoor_permission` medium: six-month Steward parameter control with silent-renewal semantics. | Approved 95/5 — Jito holders accept operational authority grants more than the skill weighted. |

Common pattern: the skill flagged technical and permission concerns, predicted reject, and the community approved anyway. **Communities tolerate technical red flags when `treasury_impact` is not a direct outflow and the beneficiary is a trusted, existing structure.** Skill v0.1's prior is too strong toward `reject` when the flag stack is technical rather than treasury-draining.

This is the most valuable signal from the batch. Not "our accuracy is bad" — "we now know exactly *where* our accuracy is bad and what to change about the prompt."

## Prompt v0.2 iteration roadmap

Concrete, testable changes drawn from the 3 wrong predictions + the patterns from the 4 correct ones.

1. **Relax the "flag stack → reject" prior when treasury is untouched.** When `treasury_impact.direction ∈ {none, internal_transfer}` and no `backdoor_permission` flag is at HIGH severity, the prediction default shifts toward approve. The three wrong predictions all had non-direct-outflow treasury impact; the skill over-weighted process concerns.

2. **Severity calibration for `backdoor_permission`.** Distinguish:
   - "authority grant to **existing, cited** party" — Marinade Council with fee redirect (MIP-21). Medium severity.
   - "authority grant to **new, unspecified** entity" — upgrade-authority rotation in the adversarial canary fixture. HIGH severity.
   Both are worth flagging; only the second should consistently trigger reject predictions.

3. **Strengthen the `token_dilution` trigger.** Jupiter net-zero is canonically a supply-trajectory proposal (700M JUP postponed, team vesting paused, Mercurial offset launched). The skill flagged `centralization` + bundling + `missing_milestone` but did not emit `token_dilution`. Fix: "any proposal that modifies supply trajectory — emissions, buybacks, burns, airdrops, vesting — must emit a `token_dilution` red flag regardless of net-positive or net-negative direction."

4. **Preserve what worked on Jupiter.** The highest-difficulty call was correct despite the skill identifying multiple high/medium red flags. The skill's reasoning acknowledged bundling AS a concern AND predicted approve based on outcome ambiguity — that's sophisticated. Any v0.2 changes must not regress this behavior. Add Jupiter net-zero as a stable test case in the red-team suite.

## Starting point, not finish line

N=7 is **existence proof that the full loop works** — skill reasons, commits on-chain, gets scored against real vote outcomes. It is **not accuracy validation**.

Every prediction on this page is visible at [the Reputation PDA](https://explorer.solana.com/address/3PDUJBj2LswT4fnUmGMMZrP3vriapUPRWUFJ66FRkoVS?cluster=devnet). The track record grows with each additional proposal. v0.2 of the skill — with the prompt iteration above — runs against the next batch. Accuracy numbers that compound across tens to hundreds of proposals are what make this tool useful or not.

If you're a Solana DAO delegate: we're curating the next batch of live fixtures now and would welcome your pick of a proposal you're currently weighing. The skill's output format is in [`eval/outputs/live_mip15_demo.md`](live_mip15_demo.md). The on-chain record will show exactly what the skill thought and why — you can check if it missed something that mattered to you.

## Verify — don't trust the numbers above

1. Open the [Reputation PDA on Solana Explorer](https://explorer.solana.com/address/3PDUJBj2LswT4fnUmGMMZrP3vriapUPRWUFJ66FRkoVS?cluster=devnet). Inspect the raw account data — `weighted_correct_numerator`, `weighted_difficulty_denominator`, `total_predictions`.
2. For each of the 7 Prediction PDAs (table below), follow the link. `correctness_bps` is `10000` if the call was right, `0` if wrong. `score_contribution` is the weight.
3. Compute the accuracy yourself: `weighted_correct_numerator / weighted_difficulty_denominator`. Should equal 5,105 for batch-only, 6,476 including the earlier N=1 demo — the account has 8 total predictions in its history.
4. The `resolver` field in [ProgramConfig](https://explorer.solana.com/address/9FWZdsySriPs3xgz5cVjYK6HJfgosrHbQYmP8XomTCHy?cluster=devnet) tells you who has authority to write outcomes. Single key for v0.1 devnet (publicly announced ahead of mainnet; will become multisig before mainnet deploy).

Source code + full fixtures + test harness: public repo pending release under MIT license.

---

## Appendix — All 21 transactions

Three transactions per proposal: `submit_prediction` (before vote closed, agent signed), `resolve_proposal` (after vote closed, resolver wrote outcome), `finalize_prediction` (permissionless crank applied score).

| Proposal | Prediction PDA | submit_prediction | resolve_proposal | finalize_prediction |
|---|---|---|---|---|
| MIP-15 | [`HE9quhgN...`](https://explorer.solana.com/address/HE9quhgNZQ1tMT6mn79HnTiFF6gNCbafbn9KqaUSwqU9?cluster=devnet) | [3ynARXv](https://explorer.solana.com/tx/3ynARXvaQXfGN5r8u8mgRr2sDct6r4sAKcDmBTQe9ppWcpVkG6gubcNgH7rxGxz1wFs3n1L8jM91uVcfE9pTq8mH?cluster=devnet) | [2pGcsjU](https://explorer.solana.com/tx/2pGcsjUat7wGQNJ5gRzuRnwzZSGdirahfSJqRGGKngCA4rNS8sAFkWxtX8fxUv1UGkoHh9wweJZihnUgK2fL4qaa?cluster=devnet) | [VZTgZNY](https://explorer.solana.com/tx/VZTgZNYWDiFQXh2cyDLBigg38ybkvrnaqVyWVvSsDa3cpwcdre9kHAfaPWMvkRzwkcZwZpKUzmUkFBqXrJVqEPR?cluster=devnet) |
| MIP-17 | [`F9YN5WX6...`](https://explorer.solana.com/address/F9YN5WX6KPB3kGPjCk9dc1Ap5kUrqbqXteGEiLm9YK8F?cluster=devnet) | [48XyqXR](https://explorer.solana.com/tx/48XyqXRacvrKqK3GwQGSDitfDjerGC6hu5vhHnuydFzHz4uX91AdwELFpweFKkUtsupteXLfJRYe1HXNBXh4XPGo?cluster=devnet) | [9fADEUH](https://explorer.solana.com/tx/9fADEUHfJH6UZybzUVjeahR26Aos1qdgtC4wBLL2dU8FdkijPTTEYk7hm35CXwZi3nNuSq7xKWS1uiJtuKRqehC?cluster=devnet) | [2LC74hp](https://explorer.solana.com/tx/2LC74hp6NYnNaH3ebrjf7dq67fGTXuZjfLCv1EEvsCb7b9KgEhQXv79R2SpPyvF9M8eKcf1aS9Gz4qGyshXvDQSz?cluster=devnet) |
| MIP-18 | [`GbYuErec...`](https://explorer.solana.com/address/GbYuErec58hWTbHBtVdCvrLzYfpkqUCvdspt6ET6nK1D?cluster=devnet) | [4Cz2Zct](https://explorer.solana.com/tx/4Cz2ZctYzZXfa3tUc9gyBeZRio8k7fu7uriD7TvNt4AGqpXUKQdcoBokmv5GctaGgwKt3YvMxeebFBDXbsd1YXcG?cluster=devnet) | [2XKYVXL](https://explorer.solana.com/tx/2XKYVXLckEi9geRVdCgVBqBb4rCELBzCa2SA7pMeLjmfr5ZtBtabrNwWvcSjdDbP7QxSzMSJistSqN6Yn4SViKsj?cluster=devnet) | [2wxSnxL](https://explorer.solana.com/tx/2wxSnxLUPn1wV61JeXuwaLo3jHfrDZqou9F9YMBiFBa2WjRXY6LPWeRMrKQca6gqaf4QSCHmomrDKk77tFDocByQ?cluster=devnet) |
| MIP-21 | [`3DijH383...`](https://explorer.solana.com/address/3DijH383pk5e4CdseNa4sMmELuRuwH7keiFJrUo8Y9ts?cluster=devnet) | [5gWH14b](https://explorer.solana.com/tx/5gWH14bnYa6ee8zfnpfkLZB4hTvjCUpUnVgLNWBLdZZZFPzCZLvtGDYHewKkmj4SeMxeMzZQ1AKFGjPKKeSLrS94?cluster=devnet) | [3mAjBLg](https://explorer.solana.com/tx/3mAjBLgnGrCcmEkUj6Go1p6Mq8ibcEAXbEkF8Cb9q7RHcZkCcv9dJq8SBPnW2hKYUgJ8sAW5n1MnixKsTRwNW8x5?cluster=devnet) | [2Sm3bbT](https://explorer.solana.com/tx/2Sm3bbTvR8u7JUiqfyLr4EkFKTnVVtKtbbba1Aj4Q64HxogRy8nb2Jk3yLUXEXo7TeyboWfgwy1C29PVUyL5soAS?cluster=devnet) |
| Jupiter | [`3jJDYCLt...`](https://explorer.solana.com/address/3jJDYCLt2HzzK7ugDR12m7BrPhMrDxLd6J8p8qsazFXz?cluster=devnet) | [3uAk2fX](https://explorer.solana.com/tx/3uAk2fXk53B8mi4HcuJpfg4UdmrTcwB5PUVD8bT9HGZd8355AuXwMBuKH9ZbRmM3SdUzYbw7Ss92FcdNFNE92F5b?cluster=devnet) | [2GBDJNF](https://explorer.solana.com/tx/2GBDJNFZprXpcuy3wjCLF6EEXfCmSQyR6rri6udTZWRtXqaqi1na8ur1F3ksJNyZSSXseWdebvEv3XyTRGGj3JoZ?cluster=devnet) | [eHNYTHB](https://explorer.solana.com/tx/eHNYTHBQt3umR4CE6dmki77h4teL4Dd8zpxoCQ8qUKLi1W4NLcogAtgskX8mKdDB4hLmrSjCV1eABHRNQ4tauKf?cluster=devnet) |
| JIP-26 | [`A6Y9azAK...`](https://explorer.solana.com/address/A6Y9azAKdMxSv4TwwNiF3ru1zZvGREvSjcky7wTekPuX?cluster=devnet) | [4QrY9ny](https://explorer.solana.com/tx/4QrY9nyuEDjf93bsezS1FuKejTzhSrh56DNXJSsEtcYDv97HbsXE7N6426vUB34Qn9389rR6N2GsXu7huGBR5G8q?cluster=devnet) | [48qLmct](https://explorer.solana.com/tx/48qLmctRHCwSdw5NiNuxpFtuGL8btr5kMb4GMV4vEvCfqJDsdv1mAHonXugJVYzpUJCUq9bNeoSAxdMMZ5Ev4x2h?cluster=devnet) | [4qX1JgY](https://explorer.solana.com/tx/4qX1JgYitbkroSwSyqPoc1PUY2ThX5TjFYYGKMgcumhsPVUWfygeMVbXfifFsSfAWXoo6tdYSr52oEiVXSBJZSXb?cluster=devnet) |
| JIP-28 | [`9PxLZqXF...`](https://explorer.solana.com/address/9PxLZqXFsPPf4nu1ncuH9i44BCeW3MViV8sAJBmAJyTF?cluster=devnet) | [2CtERuV](https://explorer.solana.com/tx/2CtERuVKSmiUSBZ6RaEJobhhfMWJ19kGbp397M86UbDMs9fW1bQea8E9tBmFZ7NrAjLFdqkrr35tXkSEZFcbZv5s?cluster=devnet) | [bUiJf5U](https://explorer.solana.com/tx/bUiJf5UjSqckvzhQhekVijfEKhJWarfLUQybopWzgUuEd5sfAiDEWxaCHAjLTXUh9ZnniRYM5cxBvcCrzvCaAgy?cluster=devnet) | [2a1BnkV](https://explorer.solana.com/tx/2a1BnkVYiSLq6MzJmYNhegaaS65unPzQEpbrHWTxF5GqVp8YnkhUYR365RZJFoLKKx2jWgo7hzPBViGhMQwxaGpq?cluster=devnet) |

---

_PsycheForge is a PoC. Nothing here is financial or voting advice. Predictions are epistemic claims about vote outcomes; the skill enforces a hard rule against vote recommendations. See [`docs/open-risks.md`](../../docs/open-risks.md) for the current risk register._
