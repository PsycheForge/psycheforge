#!/usr/bin/env ts-node
/**
 * finalize_prediction — Permissionless cranker. Scores a single prediction
 * against its resolved proposal, updating the agent's reputation aggregates.
 * Idempotent per (proposal, agent): a second call fails with `AlreadyFinalized`.
 *
 * Usage:
 *   ts-node clients/finalize_prediction.ts \
 *     --cranker-keypair ~/.config/solana/id.json \
 *     --proposal-id 01ee...00 \
 *     --agent-pubkey 6Fxm...xQ4 \
 *     [--rpc http://127.0.0.1:8899]
 *
 * The cranker just pays the transaction fee; it does NOT need to be the
 * resolver or the agent.
 */

import * as anchor from "@coral-xyz/anchor";
import { Program, AnchorProvider, Wallet } from "@coral-xyz/anchor";
import { Connection, Keypair, PublicKey } from "@solana/web3.js";
import * as fs from "fs";
import * as path from "path";

interface Args {
  crankerKeypair: string;
  proposalId: string;
  agentPubkey: string;
  rpc: string;
  programId: string;
  idl: string;
}

function parseArgs(argv: string[]): Args {
  const out: Record<string, string> = {
    rpc: "http://127.0.0.1:8899",
    programId: "85huMKVbSddkbZiSk4XUBUSxsZS39tbd3sLp17viJJqH",
    idl: path.resolve(__dirname, "..", "target", "idl", "reputation.json"),
  };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--cranker-keypair") out.crankerKeypair = argv[++i];
    else if (a === "--proposal-id") out.proposalId = argv[++i];
    else if (a === "--agent-pubkey") out.agentPubkey = argv[++i];
    else if (a === "--rpc") out.rpc = argv[++i];
    else if (a === "--program-id") out.programId = argv[++i];
    else if (a === "--idl") out.idl = argv[++i];
    else if (a === "--help" || a === "-h") {
      console.error("see file header for usage");
      process.exit(0);
    } else {
      console.error(`unknown argument: ${a}`);
      process.exit(2);
    }
  }
  for (const req of ["crankerKeypair", "proposalId", "agentPubkey"]) {
    if (!out[req]) {
      console.error(`missing required --${req.replace(/([A-Z])/g, "-$1").toLowerCase()}`);
      process.exit(2);
    }
  }
  return out as unknown as Args;
}

function loadKeypair(p: string): Keypair {
  const expanded = p.startsWith("~/") ? path.join(process.env.HOME || "", p.slice(2)) : p;
  return Keypair.fromSecretKey(Uint8Array.from(JSON.parse(fs.readFileSync(expanded, "utf8"))));
}

function hexToBytes(hex: string): Uint8Array {
  const clean = hex.replace(/^0x/, "");
  if (clean.length !== 64) throw new Error(`proposal-id must be 64 hex chars (got ${clean.length})`);
  const b = new Uint8Array(32);
  for (let i = 0; i < 32; i++) b[i] = parseInt(clean.slice(i * 2, i * 2 + 2), 16);
  return b;
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv);
  const cranker = loadKeypair(args.crankerKeypair);
  const proposalIdBytes = hexToBytes(args.proposalId);
  const agentPk = new PublicKey(args.agentPubkey);
  const programId = new PublicKey(args.programId);

  const connection = new Connection(args.rpc, "confirmed");
  const provider = new AnchorProvider(connection, new Wallet(cranker), { commitment: "confirmed" });
  anchor.setProvider(provider);
  const idl = JSON.parse(fs.readFileSync(args.idl, "utf8"));
  const program = new Program(idl, provider) as any;

  const [reputationPda] = PublicKey.findProgramAddressSync(
    [Buffer.from("reputation"), agentPk.toBuffer()],
    programId
  );
  const [proposalPda] = PublicKey.findProgramAddressSync(
    [Buffer.from("proposal"), Buffer.from(proposalIdBytes)],
    programId
  );
  const [predictionPda] = PublicKey.findProgramAddressSync(
    [Buffer.from("prediction"), Buffer.from(proposalIdBytes), agentPk.toBuffer()],
    programId
  );

  console.error(`rpc:             ${args.rpc}`);
  console.error(`cranker:         ${cranker.publicKey.toBase58()}`);
  console.error(`agent:           ${agentPk.toBase58()}`);
  console.error(`proposal_id:     ${args.proposalId}`);
  console.error(`proposalPda:    ${proposalPda.toBase58()}`);
  console.error(`predictionPda:   ${predictionPda.toBase58()}`);
  console.error(`reputationPda:   ${reputationPda.toBase58()}`);
  console.error("");

  try {
    const sig = await program.methods
      .finalizePrediction(Array.from(proposalIdBytes), agentPk)
      .accounts({
        cranker: cranker.publicKey,
        reputation: reputationPda,
        proposal: proposalPda,
        prediction: predictionPda,
      })
      .rpc();
    console.error(`[ok] finalize confirmed: ${sig}`);
  } catch (e) {
    console.error(`[x] finalize failed: ${e}`);
    process.exit(1);
  }

  const pred = await program.account.prediction.fetch(predictionPda);
  const rep = await program.account.agentReputation.fetch(reputationPda);
  console.error(`\non-chain Prediction (post-finalize):`);
  console.error(`  resolved:          ${pred.resolved}`);
  console.error(`  correctness_bps:   ${pred.correctnessBps}`);
  console.error(`  score_contribution: ${pred.scoreContribution.toString()}`);
  console.error(`\non-chain AgentReputation (updated aggregates):`);
  console.error(`  total_predictions:              ${rep.totalPredictions.toString()}`);
  console.error(`  total_resolved:                 ${rep.totalResolved.toString()}`);
  console.error(`  weighted_correct_numerator:     ${rep.weightedCorrectNumerator.toString()}`);
  console.error(`  weighted_difficulty_denominator: ${rep.weightedDifficultyDenominator.toString()}`);

  // Off-chain accuracy derivation
  const num = BigInt(rep.weightedCorrectNumerator.toString());
  const den = BigInt(rep.weightedDifficultyDenominator.toString());
  const accuracyBps = den === BigInt(0) ? null : Number(num / den);
  console.error(`  derived accuracy_bps:           ${accuracyBps === null ? "n/a (zero weighted denominator)" : accuracyBps}`);

  process.stdout.write(JSON.stringify({
    prediction_pda: predictionPda.toBase58(),
    correctness_bps: pred.correctnessBps,
    score_contribution: pred.scoreContribution.toString(),
    reputation_pda: reputationPda.toBase58(),
    weighted_correct_numerator: rep.weightedCorrectNumerator.toString(),
    weighted_difficulty_denominator: rep.weightedDifficultyDenominator.toString(),
    accuracy_bps: accuracyBps,
  }) + "\n");
}

main().catch((err) => { console.error(`fatal: ${err}`); process.exit(1); });
