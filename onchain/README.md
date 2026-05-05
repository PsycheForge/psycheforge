# onchain/ — Reputation Anchor Program

On-chain accountability layer for PsycheForge: tracks predictions made by governance-triage agents and computes a gaming-resistant accuracy score.

Design: [`docs/reputation-program-design.md`](../docs/reputation-program-design.md). Risk mapping: [`docs/open-risks.md`](../docs/open-risks.md) Risk B.

## Layout

```
onchain/
├── Anchor.toml                          # Anchor workspace config
├── Cargo.toml                           # Rust workspace
├── programs/
│   └── reputation/
│       ├── Cargo.toml
│       └── src/
│           └── lib.rs                   # 7 instructions, 4 accounts, 8 error codes
├── tests/
│   └── reputation.ts                    # 31 tests — happy paths, error paths, red-team
├── target/                              # build artifacts (gitignored)
│   └── deploy/reputation-keypair.json   # program keypair (LOCAL ONLY — do not commit)
├── package.json                         # JS test deps
└── tsconfig.json
```

## Prereqs

- Rust (tested on 1.94 nightly)
- Solana CLI (tested on 4.1.0-alpha)
- Anchor CLI (tested on 0.32.1)
- Node ≥ 20 + Yarn

No shell profile edits needed — the toolchain is discovered via `PATH` set by the user's existing Solana install.

## Install deps

```bash
cd onchain
yarn install
```

## Build

```bash
cd onchain
anchor build
```

Produces:
- `target/deploy/reputation.so` — BPF binary
- `target/idl/reputation.json` — IDL for off-chain clients
- `target/types/reputation.ts` — TypeScript bindings used by the test suite

## Test

```bash
cd onchain
anchor test
```

Spins up a local validator, deploys, runs the full 31-test mocha suite. Typical total runtime: ~60–80 seconds.

Expected output:
```
  31 passing (1m)
```

## Program ID

`85huMKVbSddkbZiSk4XUBUSxsZS39tbd3sLp17viJJqH`

- **Devnet:** deployed and live — [view program account on Solana Explorer](https://explorer.solana.com/address/85huMKVbSddkbZiSk4XUBUSxsZS39tbd3sLp17viJJqH?cluster=devnet).
- **Localnet:** same ID (used by `anchor test`).
- **Mainnet:** not yet deployed.

The keypair lives at `target/deploy/reputation-keypair.json` and is **not** committed. Do not share it — it is the program's upgrade authority. To regenerate across machines, generate a new keypair and run `anchor keys sync` to update `declare_id!` and `Anchor.toml`, then redeploy.

## Instruction quick-ref

| Instruction | Signer | Purpose |
|---|---|---|
| `initialize_config(resolver)` | deployer | One-time setup: writes resolver key into ProgramConfig PDA |
| `register_agent()` | agent | Creates AgentReputation PDA, zeroes counters |
| `create_proposal(id, dao_id, voting_closes_at_slot, num_choices)` | resolver | Registers a predictable proposal |
| `submit_prediction(id, predicted_outcome)` | agent | Commits a prediction before voting closes |
| `resolve_proposal(id, vote_distribution_bps, final_outcome, difficulty_bps)` | resolver | Writes outcome + difficulty after voting closes |
| `finalize_prediction(id, agent_pubkey)` | anyone | Scores a prediction, updates agent's aggregates |
| `transfer_resolver(new_resolver)` | current resolver | Rotates the resolver authority |

See [`docs/reputation-program-design.md`](../docs/reputation-program-design.md) §4 for the full account layout, seed schemes, and check semantics.

## Devnet deploy (done — 2026-04-22)

Deployed and exercised end-to-end. One agent currently has a verifiable on-chain accuracy record (100% on N=1).

**Live devnet addresses:**

| Account | Pubkey | Explorer |
|---|---|---|
| Program | `85huMKVbSddkbZiSk4XUBUSxsZS39tbd3sLp17viJJqH` | [link](https://explorer.solana.com/address/85huMKVbSddkbZiSk4XUBUSxsZS39tbd3sLp17viJJqH?cluster=devnet) |
| ProgramConfig | `9FWZdsySriPs3xgz5cVjYK6HJfgosrHbQYmP8XomTCHy` | [link](https://explorer.solana.com/address/9FWZdsySriPs3xgz5cVjYK6HJfgosrHbQYmP8XomTCHy?cluster=devnet) |
| AgentReputation (demo) | `3PDUJBj2LswT4fnUmGMMZrP3vriapUPRWUFJ66FRkoVS` | [link](https://explorer.solana.com/address/3PDUJBj2LswT4fnUmGMMZrP3vriapUPRWUFJ66FRkoVS?cluster=devnet) |
| Demo Proposal | `3cBKqyfZ6NWukofts8wExngfYtxSFyNXXCEUZeAf5H65` | [link](https://explorer.solana.com/address/3cBKqyfZ6NWukofts8wExngfYtxSFyNXXCEUZeAf5H65?cluster=devnet) |
| Demo Prediction | `57PVW9HHthoXZuVDE6KD8F7EiRJLVZhPxYTcF2ytWaXf` | [link](https://explorer.solana.com/address/57PVW9HHthoXZuVDE6KD8F7EiRJLVZhPxYTcF2ytWaXf?cluster=devnet) |

To redeploy or deploy a new fork:

```bash
solana config set --url devnet
solana airdrop 5                           # or top up via a devnet faucet
anchor build
anchor deploy --provider.cluster devnet
yarn ts-node clients/bootstrap.ts --rpc https://api.devnet.solana.com ...
```

## Mainnet deploy (future)

Gated on:

1. **Multisig resolver.** Single-key resolver is acceptable for devnet PoC only. Before mainnet, set `ProgramConfig.resolver` to a Squads vault or equivalent multisig via `transfer_resolver`.
2. **Public red-team exercise.** The 6 scenarios in `tests/reputation.ts` prove the scoring math against unit-test attacks. A public invitation to adversarial testers, ideally with a cash bounty, is the last credibility step before mainnet.
3. **Audit.** At least informal review by one independent Anchor-fluent engineer. Formal audit desirable but not strictly required at v0.1 volume.
4. **Atomic deploy + init.** Known v0.1 hole (see design doc §2): `initialize_config` can be front-run between deploy and init. Mainnet deploy must bundle the two instructions into a single transaction or script with no observable gap.

## Removing everything

```bash
rm -rf onchain/target/ onchain/node_modules/ onchain/yarn.lock onchain/test-ledger/
```

The source (`programs/`, `tests/`, `Anchor.toml`, `Cargo.toml`, etc.) stays.
