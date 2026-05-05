#!/usr/bin/env ts-node
/**
 * submit_prediction — CLI that commits a single prediction to the reputation
 * program on-chain. Reads a prediction JSON produced by the `prediction-writer`
 * skill and submits it as a `submit_prediction` instruction.
 *
 * Assumes:
 *   - Hermes-agent's local venv is NOT needed (pure TS).
 *   - A validator is reachable at --rpc (default localnet).
 *   - The program is deployed.
 *   - The resolver has already `initialize_config`'d and created the target `Proposal`.
 *   - The signer (agent keypair) has SOL to pay for the Prediction PDA rent.
 *
 * This client deliberately does NOT do register_agent / create_proposal — those
 * are resolver-authority operations. For the demo flow, run them once via the
 * `tests/reputation.ts` suite or a separate bootstrap script.
 *
 * Usage:
 *   ts-node clients/submit_prediction.ts \
 *     --prediction ../eval/outputs/pred.json \
 *     --keypair ~/.config/solana/id.json \
 *     --proposal-id 01ee000000000000000000000000000000000000000000000000000000000000 \
 *     --rpc http://127.0.0.1:8899
 *
 *   # Dry-run: build but do not send the transaction
 *   ts-node clients/submit_prediction.ts ... --dry-run
 */

import * as anchor from "@coral-xyz/anchor";
import { Program, AnchorProvider, Wallet } from "@coral-xyz/anchor";
import { Connection, Keypair, PublicKey } from "@solana/web3.js";
import * as fs from "fs";
import * as path from "path";

interface PredictionJson {
  predicted_outcome: number;
  confidence_bps: number;
  reasoning_citation: string;
  key_triage_signals: string[];
}

interface CliArgs {
  prediction: string;
  keypair: string;
  proposalId: string;
  rpc: string;
  programId: string;
  idl: string;
  dryRun: boolean;
}

function parseArgs(argv: string[]): CliArgs {
  const defaults: Partial<CliArgs> = {
    rpc: "http://127.0.0.1:8899",
    programId: "85huMKVbSddkbZiSk4XUBUSxsZS39tbd3sLp17viJJqH",
    idl: path.resolve(__dirname, "..", "target", "idl", "reputation.json"),
    dryRun: false,
  };
  const args: Record<string, string | boolean> = { ...defaults };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--dry-run") args.dryRun = true;
    else if (a === "--prediction") args.prediction = argv[++i];
    else if (a === "--keypair") args.keypair = argv[++i];
    else if (a === "--proposal-id") args.proposalId = argv[++i];
    else if (a === "--rpc") args.rpc = argv[++i];
    else if (a === "--program-id") args.programId = argv[++i];
    else if (a === "--idl") args.idl = argv[++i];
    else if (a === "--help" || a === "-h") {
      printHelp();
      process.exit(0);
    } else {
      console.error(`unknown argument: ${a}`);
      process.exit(2);
    }
  }
  for (const required of ["prediction", "keypair", "proposalId"] as const) {
    if (!args[required]) {
      console.error(`missing required --${required.replace(/([A-Z])/g, "-$1").toLowerCase()}`);
      printHelp();
      process.exit(2);
    }
  }
  return args as unknown as CliArgs;
}

function printHelp(): void {
  console.error(`
Usage: submit_prediction.ts [options]

Required:
  --prediction <path>       Path to prediction JSON (from prediction-writer skill).
  --keypair <path>          Path to agent signer keypair JSON.
  --proposal-id <hex>       32-byte proposal id as 64 hex chars.

Optional:
  --rpc <url>               Solana RPC endpoint (default: http://127.0.0.1:8899).
  --program-id <pubkey>     Override reputation program id.
  --idl <path>              Path to IDL JSON (default: ../target/idl/reputation.json).
  --dry-run                 Build and log the transaction but do not send.
`);
}

function loadKeypair(p: string): Keypair {
  const expanded = p.startsWith("~/") ? path.join(process.env.HOME || "", p.slice(2)) : p;
  const raw = JSON.parse(fs.readFileSync(expanded, "utf8"));
  return Keypair.fromSecretKey(Uint8Array.from(raw));
}

function loadPrediction(p: string): PredictionJson {
  const raw = JSON.parse(fs.readFileSync(p, "utf8"));
  for (const field of ["predicted_outcome", "confidence_bps", "reasoning_citation", "key_triage_signals"]) {
    if (!(field in raw)) throw new Error(`prediction JSON missing required field: ${field}`);
  }
  return raw;
}

function hexToBytes(hex: string): Uint8Array {
  const clean = hex.replace(/^0x/, "");
  if (clean.length !== 64) {
    throw new Error(`proposal-id must be 64 hex chars (got ${clean.length})`);
  }
  const bytes = new Uint8Array(32);
  for (let i = 0; i < 32; i++) {
    bytes[i] = parseInt(clean.slice(i * 2, i * 2 + 2), 16);
  }
  return bytes;
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv);

  const agent = loadKeypair(args.keypair);
  const prediction = loadPrediction(args.prediction);
  const proposalIdBytes = hexToBytes(args.proposalId);
  const programId = new PublicKey(args.programId);

  const connection = new Connection(args.rpc, "confirmed");
  const wallet = new Wallet(agent);
  const provider = new AnchorProvider(connection, wallet, { commitment: "confirmed" });
  anchor.setProvider(provider);

  const idl = JSON.parse(fs.readFileSync(args.idl, "utf8"));
  const program = new Program(idl, provider) as any;

  const [reputationPda] = PublicKey.findProgramAddressSync(
    [Buffer.from("reputation"), agent.publicKey.toBuffer()],
    programId
  );
  const [proposalPda] = PublicKey.findProgramAddressSync(
    [Buffer.from("proposal"), Buffer.from(proposalIdBytes)],
    programId
  );
  const [predictionPda] = PublicKey.findProgramAddressSync(
    [Buffer.from("prediction"), Buffer.from(proposalIdBytes), agent.publicKey.toBuffer()],
    programId
  );

  console.error(`rpc:             ${args.rpc}`);
  console.error(`program:         ${programId.toBase58()}`);
  console.error(`agent:           ${agent.publicKey.toBase58()}`);
  console.error(`proposal_id:     ${args.proposalId}`);
  console.error(`proposal PDA:    ${proposalPda.toBase58()}`);
  console.error(`reputation PDA:  ${reputationPda.toBase58()}`);
  console.error(`prediction PDA:  ${predictionPda.toBase58()}`);
  console.error(`predicted_outcome (on-chain): ${prediction.predicted_outcome}`);
  console.error(`confidence_bps (off-chain, for display only): ${prediction.confidence_bps}`);
  console.error("");

  if (args.dryRun) {
    // No network calls — just build the instruction to prove wiring is correct.
    const ix = await program.methods
      .submitPrediction(Array.from(proposalIdBytes), prediction.predicted_outcome)
      .accounts({
        agent: agent.publicKey,
        reputation: reputationPda,
        proposal: proposalPda,
        prediction: predictionPda,
      })
      .instruction();
    console.error("[dry-run] instruction prepared (no network):");
    console.error(`  program: ${ix.programId.toBase58()}`);
    console.error(`  keys:    ${ix.keys.length}`);
    console.error(`  data:    ${ix.data.length} bytes (discriminator + proposal_id + predicted_outcome)`);
    return;
  }

  // Sanity: confirm the Proposal PDA exists (create_proposal must run first).
  const proposalInfo = await connection.getAccountInfo(proposalPda);
  if (!proposalInfo) {
    console.error(`[x] proposal account not found at ${proposalPda.toBase58()}`);
    console.error("    create_proposal must be called by the resolver before submit_prediction.");
    process.exit(1);
  }

  try {
    const sig = await program.methods
      .submitPrediction(Array.from(proposalIdBytes), prediction.predicted_outcome)
      .accounts({
        agent: agent.publicKey,
        reputation: reputationPda,
        proposal: proposalPda,
        prediction: predictionPda,
      })
      .rpc();
    console.error(`[ok] submitted. signature: ${sig}`);
  } catch (e) {
    console.error(`[x] submit failed: ${e}`);
    process.exit(1);
  }

  const predAccount = await program.account.prediction.fetch(predictionPda);
  console.error("\non-chain Prediction:");
  console.error(`  agent:             ${predAccount.agent.toBase58()}`);
  console.error(`  predicted_outcome: ${predAccount.predictedOutcome}`);
  console.error(`  submitted_at_slot: ${predAccount.submittedAtSlot.toString()}`);
  console.error(`  resolved:          ${predAccount.resolved}`);

  // Print a tiny structured result to stdout for machine consumption.
  process.stdout.write(JSON.stringify({
    prediction_pda: predictionPda.toBase58(),
    submitted_at_slot: predAccount.submittedAtSlot.toString(),
    predicted_outcome: predAccount.predictedOutcome,
  }) + "\n");
}

main().catch((err) => {
  console.error(`fatal: ${err}`);
  process.exit(1);
});
