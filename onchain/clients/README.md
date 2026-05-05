# onchain/clients/ — Off-chain clients for the reputation program

Standalone scripts that talk to the deployed program. Kept in TypeScript because `@coral-xyz/anchor` fully supports the Anchor 0.32.1 IDL spec (`spec: 0.1.0`); the equivalent Python library (`anchorpy` 0.21.0) does not yet parse it — we tried, see commit history.

## submit_prediction.ts

Commits a single prediction to the program. Reads a prediction JSON produced by the `prediction-writer` skill and submits it as a `submit_prediction` instruction signed by the agent keypair.

### Prereqs

Before running:

1. A Solana validator reachable at `--rpc` (default `http://127.0.0.1:8899`).
2. The reputation program is deployed at the configured program ID.
3. `initialize_config` has been called (one-time).
4. The agent has been `register_agent`'d.
5. The target `Proposal` PDA has been `create_proposal`'d by the resolver.

Steps 3-5 are currently wired through the Anchor test suite's `before` hooks. For a live flow, add bootstrap scripts or do them manually via `anchor` CLI.

### Usage

```bash
cd onchain
yarn submit \
  --prediction ../eval/outputs/sample_prediction.json \
  --keypair ~/.config/solana/id.json \
  --proposal-id 01ee000000000000000000000000000000000000000000000000000000000000 \
  --rpc http://127.0.0.1:8899
```

Or directly with ts-node:

```bash
./node_modules/.bin/ts-node clients/submit_prediction.ts --help
```

### Flags

| Flag | Required | Purpose |
|---|---|---|
| `--prediction <path>` | yes | Path to prediction JSON (from `prediction-writer`) |
| `--keypair <path>` | yes | Path to agent signer keypair JSON |
| `--proposal-id <hex>` | yes | 32-byte proposal id as 64 hex chars |
| `--rpc <url>` | no | Solana RPC (default: localnet) |
| `--program-id <pubkey>` | no | Override program id |
| `--idl <path>` | no | Override IDL path (default: `../target/idl/reputation.json`) |
| `--dry-run` | no | Build instruction only, no network calls |

### Output

- **stderr**: human-readable progress + PDAs + final on-chain state
- **stdout**: one line of structured JSON:
  ```json
  {"prediction_pda":"...","submitted_at_slot":"123","predicted_outcome":1}
  ```
  safe to pipe into another tool.

### Dry-run

Validates wiring without touching the network. Loads keypair, parses prediction, derives PDAs, builds the instruction, logs size + key count. Useful for:

- CI sanity (keypair readable, IDL parseable, PDA derivation correct)
- Debugging before paying tx fees
- Offline test of the submit path

### What this client does NOT do

- Does **not** call `register_agent` — the agent keypair must be pre-registered.
- Does **not** call `create_proposal` — that's a resolver authority operation.
- Does **not** call `resolve_proposal` or `finalize_prediction` — those are separate steps in the lifecycle.
- Does **not** know about skill outputs other than `predicted_outcome`. The `confidence_bps`, `reasoning_citation`, and `key_triage_signals` fields are preserved in the prediction JSON for off-chain dashboards / audit trails — the on-chain program only sees the outcome.

## Proposal ID convention

`proposal_id` is a 32-byte hash. Recommended derivation:

```
proposal_id = sha256(dao_id || proposal_url)
```

For reproducibility during tests, pick a deterministic hex value (our tests use `fixedId(n)` with a small seed). For production, hash the canonical proposal URL once and carry the hex around.

## Future clients (planned, not yet written)

- `register_agent.ts` — one-time agent registration helper
- `create_proposal.ts` — resolver authority helper to register a new proposal
- `resolve_proposal.ts` — resolver writes outcome + distribution + difficulty
- `finalize_prediction.ts` — permissionless cranker that scores a resolved prediction

These will arrive as the product loop extends past MVP. For now, `tests/reputation.ts` exercises these via Anchor directly; the pattern there transfers directly to standalone clients.
