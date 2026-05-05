#!/usr/bin/env python3
"""Batch runner — run the skill chain on N fixtures; optionally commit each
prediction to Solana devnet.

Usage:
    # Skill chain only (no on-chain)
    python eval/batch_runner.py --fixtures 'eval/fixtures/live_*.md'

    # Full: skill chain + devnet submission
    python eval/batch_runner.py --fixtures 'eval/fixtures/live_*.md' \\
        --submit-devnet \\
        --agent-keypair ~/.config/solana/id.json \\
        --resolver-keypair ~/.config/solana/id.json

Produces:
    eval/outputs/batch_<utc_ts>.json                 — manifest (one entry per fixture)
    eval/outputs/batch_<utc_ts>_artifacts/<slug>_triage.json
    eval/outputs/batch_<utc_ts>_artifacts/<slug>_prediction.json

The manifest is written after every fixture so a crash mid-batch does not
lose completed work. Each entry tracks its own status field — rerun with the
same --manifest to resume (see --resume).

Proposal IDs are deterministic: sha256(source_url) → 32-byte hex. This means
re-running on the same fixture with the same source_url targets the same
Proposal PDA, which is useful for idempotent re-submission attempts but fails
if the PDA already exists (by design — one proposal per hash).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_VENV_PY = REPO_ROOT / ".hermes-agent" / "venv" / "bin" / "python"
if (
    _VENV_PY.exists()
    and Path(sys.executable).resolve() != _VENV_PY.resolve()
    and not os.environ.get("HERMES_NO_REEXEC")
):
    os.execv(str(_VENV_PY), [str(_VENV_PY), *sys.argv])

import argparse
import datetime
import glob
import hashlib
import json
import re
import subprocess
import traceback
from dataclasses import dataclass, field, asdict
from typing import Any

import yaml
from jsonschema import Draft202012Validator

# ─── Paths ────────────────────────────────────────────────────────────────────
ONCHAIN_DIR = REPO_ROOT / "onchain"
BOOTSTRAP_TS = ONCHAIN_DIR / "clients" / "bootstrap.ts"
SUBMIT_TS = ONCHAIN_DIR / "clients" / "submit_prediction.ts"
TS_NODE = ONCHAIN_DIR / "node_modules" / ".bin" / "ts-node"

TRIAGE_SKILL_DIR = REPO_ROOT / "skills" / "governance-triage"
PREDICTION_SKILL_DIR = REPO_ROOT / "skills" / "prediction-writer"
TRIAGE_SCHEMA = TRIAGE_SKILL_DIR / "references" / "output-schema.json"
PREDICTION_SCHEMA = PREDICTION_SKILL_DIR / "references" / "output-schema.json"

TRIAGE_HERMES_ID = "research/governance-triage"
PREDICTION_HERMES_ID = "research/prediction-writer"
PROGRAM_ID = "85huMKVbSddkbZiSk4XUBUSxsZS39tbd3sLp17viJJqH"

FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)\n```", re.DOTALL)


# ─── Parsing / JSON extraction ────────────────────────────────────────────────
def extract_json(response: str) -> dict[str, Any]:
    text = response.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    fenced = FENCE_RE.search(text)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass
    start = text.find("{")
    if start == -1:
        raise json.JSONDecodeError("No JSON object found in response", text, 0)
    obj, _ = json.JSONDecoder().raw_decode(text[start:])
    if not isinstance(obj, dict):
        raise json.JSONDecodeError("Top-level JSON value is not an object", text, start)
    return obj


def parse_fixture(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text()
    if not text.startswith("---\n"):
        return {}, text.strip()
    _, fm_raw, body = text.split("---\n", 2)
    return yaml.safe_load(fm_raw) or {}, body.strip()


# ─── Hermes + subprocess helpers ──────────────────────────────────────────────
def hermes_exec(skill_id: str, prompt: str, model: str | None = None, timeout: int = 300) -> str:
    venv_hermes = REPO_ROOT / ".hermes-agent" / "venv" / "bin" / "hermes"
    exe = str(venv_hermes) if venv_hermes.exists() else "hermes"
    cmd = [exe, "chat", "-q", prompt, "-s", skill_id, "-Q"]
    if model:
        cmd.extend(["-m", model])
    result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=timeout)
    return result.stdout


def run_ts(script: Path, args: list[str], timeout: int = 180) -> tuple[str, str, int]:
    cmd = [str(TS_NODE), str(script)] + args
    result = subprocess.run(
        cmd, cwd=str(ONCHAIN_DIR), capture_output=True, text=True, timeout=timeout
    )
    return result.stdout, result.stderr, result.returncode


# ─── Prompts ──────────────────────────────────────────────────────────────────
def build_triage_prompt(proposal_text: str, frontmatter: dict[str, Any]) -> str:
    source_url = frontmatter.get("source_url") or "(none provided)"
    dao_context = frontmatter.get("dao_context") or "(none provided)"
    return (
        "Analyze this Solana DAO proposal using the governance-triage skill. "
        "Return ONLY a single JSON object matching the skill's output schema.\n"
        f"\nDAO context: {dao_context}\n"
        f"Source URL: {source_url}\n"
        f"\nPROPOSAL TEXT:\n{proposal_text}\n"
    )


def build_prediction_prompt(triage_json: dict[str, Any], num_choices: int) -> str:
    return (
        "Apply the prediction-writer skill to the governance-triage output below. "
        "Return ONLY a single JSON object matching the skill's output schema.\n"
        f"\nProposal num_choices: {num_choices}\n"
        "Choice convention (pin this — do not infer):\n"
        "  index 0 = approve / yes / pass\n"
        "  index 1 = reject / no / fail\n"
        f"\nGOVERNANCE-TRIAGE OUTPUT:\n{json.dumps(triage_json, indent=2, ensure_ascii=False)}\n"
    )


# ─── IDs ──────────────────────────────────────────────────────────────────────
def deterministic_proposal_id(source_url: str, fallback: str) -> str:
    key = source_url or fallback
    return hashlib.sha256(key.encode()).hexdigest()


def deterministic_dao_id(dao_context: str) -> str:
    return hashlib.sha256((dao_context or "unknown-dao").encode()).hexdigest()


# ─── Manifest ─────────────────────────────────────────────────────────────────
@dataclass
class ManifestEntry:
    fixture: str
    slug: str
    source_url: str | None = None
    dao_context: str | None = None
    proposal_id_hex: str | None = None
    dao_id_hex: str | None = None
    triage_path: str | None = None
    prediction_path: str | None = None
    predicted_outcome: int | None = None
    confidence_bps: int | None = None
    red_flag_categories: list[str] = field(default_factory=list)
    triage_summary: str | None = None
    proposal_pda: str | None = None
    prediction_pda: str | None = None
    submit_tx_sig: str | None = None
    submitted_at_slot: str | None = None
    resolved: bool = False
    final_outcome: int | None = None
    correctness_bps: int | None = None
    resolve_tx_sig: str | None = None
    finalize_tx_sig: str | None = None
    status: str = "pending"
    error: str | None = None


# ─── Main processing ──────────────────────────────────────────────────────────
def process_fixture(
    fixture_path: Path,
    num_choices: int,
    model: str | None,
    artifacts_dir: Path,
    submit_devnet: bool,
    agent_keypair: str | None,
    resolver_keypair: str | None,
    rpc: str,
) -> ManifestEntry:
    slug = fixture_path.stem
    entry = ManifestEntry(fixture=fixture_path.name, slug=slug)

    try:
        frontmatter, body = parse_fixture(fixture_path)
    except Exception as e:
        entry.status = "parse_failed"
        entry.error = f"{type(e).__name__}: {e}"
        return entry

    entry.source_url = frontmatter.get("source_url")
    entry.dao_context = frontmatter.get("dao_context")
    entry.proposal_id_hex = deterministic_proposal_id(entry.source_url or "", slug)
    entry.dao_id_hex = deterministic_dao_id(entry.dao_context or "")

    # Stage 1: triage
    try:
        triage_raw = hermes_exec(TRIAGE_HERMES_ID, build_triage_prompt(body, frontmatter), model)
        triage_json = extract_json(triage_raw)
        triage_errors = list(
            Draft202012Validator(json.loads(TRIAGE_SCHEMA.read_text())).iter_errors(triage_json)
        )
        if triage_errors:
            raise ValueError(f"triage schema invalid ({len(triage_errors)} errors); first: {triage_errors[0].message}")
    except Exception as e:
        entry.status = "triage_failed"
        entry.error = f"{type(e).__name__}: {e}"
        return entry

    triage_path = artifacts_dir / f"{slug}_triage.json"
    triage_path.write_text(json.dumps(triage_json, indent=2, ensure_ascii=False))
    entry.triage_path = str(triage_path.relative_to(REPO_ROOT))
    entry.triage_summary = triage_json.get("summary")
    entry.red_flag_categories = [rf.get("category") for rf in (triage_json.get("red_flags") or [])]

    # Stage 2: prediction
    try:
        pred_raw = hermes_exec(
            PREDICTION_HERMES_ID, build_prediction_prompt(triage_json, num_choices), model
        )
        pred_json = extract_json(pred_raw)
        pred_errors = list(
            Draft202012Validator(json.loads(PREDICTION_SCHEMA.read_text())).iter_errors(pred_json)
        )
        if pred_errors:
            raise ValueError(f"prediction schema invalid ({len(pred_errors)} errors); first: {pred_errors[0].message}")
    except Exception as e:
        entry.status = "prediction_failed"
        entry.error = f"{type(e).__name__}: {e}"
        return entry

    prediction_path = artifacts_dir / f"{slug}_prediction.json"
    prediction_path.write_text(json.dumps(pred_json, indent=2, ensure_ascii=False))
    entry.prediction_path = str(prediction_path.relative_to(REPO_ROOT))
    entry.predicted_outcome = pred_json.get("predicted_outcome")
    entry.confidence_bps = pred_json.get("confidence_bps")

    entry.status = "triage+prediction_ok"
    if not submit_devnet:
        return entry

    # Stage 3 + 4: devnet bootstrap + submit
    return submit_entry_on_chain(entry, agent_keypair, resolver_keypair, rpc, num_choices)


def submit_entry_on_chain(
    entry: ManifestEntry,
    agent_keypair: str,
    resolver_keypair: str,
    rpc: str,
    num_choices: int,
) -> ManifestEntry:
    """Run bootstrap.ts + submit_prediction.ts for an entry whose
    prediction is already written to disk. Idempotent on bootstrap for
    config/agent; will fail if the proposal PDA already exists (by design).
    """
    if not entry.prediction_path or not entry.proposal_id_hex:
        entry.status = "submit_skipped"
        entry.error = "entry missing prediction_path or proposal_id_hex"
        return entry

    # Stage 3: bootstrap
    try:
        _, bstderr, brc = run_ts(BOOTSTRAP_TS, [
            "--resolver-keypair", resolver_keypair,
            "--agent-keypair", agent_keypair,
            "--proposal-id", entry.proposal_id_hex,
            "--dao-id", entry.dao_id_hex,
            "--num-choices", str(num_choices),
            "--rpc", rpc,
        ])
        if brc != 0:
            raise RuntimeError(f"bootstrap failed (rc={brc}): {bstderr[:600]}")
        pda_match = re.search(r"proposalPda:\s*(\S+)", bstderr)
        if pda_match:
            entry.proposal_pda = pda_match.group(1)
    except Exception as e:
        entry.status = "bootstrap_failed"
        entry.error = f"{type(e).__name__}: {e}"
        return entry

    # Stage 4: submit_prediction
    try:
        sstdout, sstderr, src = run_ts(SUBMIT_TS, [
            "--prediction", str((REPO_ROOT / entry.prediction_path).resolve()),
            "--keypair", agent_keypair,
            "--proposal-id", entry.proposal_id_hex,
            "--rpc", rpc,
        ])
        if src != 0:
            raise RuntimeError(f"submit failed (rc={src}): {sstderr[:600]}")
        json_lines = [l for l in sstdout.strip().splitlines() if l.strip().startswith("{")]
        if json_lines:
            data = json.loads(json_lines[-1])
            entry.prediction_pda = data.get("prediction_pda")
            entry.submitted_at_slot = data.get("submitted_at_slot")
        sig_match = re.search(r"\[ok\] submitted\. signature: (\S+)", sstderr)
        if sig_match:
            entry.submit_tx_sig = sig_match.group(1)
    except Exception as e:
        entry.status = "submit_failed"
        entry.error = f"{type(e).__name__}: {e}"
        return entry

    entry.status = "submitted"
    return entry


def run_from_manifest(args: argparse.Namespace) -> int:
    """Resume mode: skip skill chain, only do devnet submit for each entry
    that has a prediction but has not been submitted yet."""
    manifest_path = Path(args.from_manifest)
    if not manifest_path.exists():
        print(f"[x] manifest not found: {manifest_path}")
        return 2

    raw = json.loads(manifest_path.read_text())
    entries = [ManifestEntry(**e) for e in raw.get("entries", [])]

    eligible = [e for e in entries if e.status == "triage+prediction_ok" and not e.submit_tx_sig]
    already_done = [e for e in entries if e.submit_tx_sig]
    not_eligible = [e for e in entries if e.status != "triage+prediction_ok" and not e.submit_tx_sig]

    print(f"manifest:          {manifest_path}")
    print(f"entries total:     {len(entries)}")
    print(f"eligible (submit): {len(eligible)}")
    print(f"already submitted: {len(already_done)}")
    print(f"skipped (status):  {len(not_eligible)}")
    print(f"rpc:               {args.rpc}")
    print("=" * 60)

    for i, entry in enumerate(eligible, 1):
        print(f"\n[{i}/{len(eligible)}] {entry.slug}")
        entry = submit_entry_on_chain(
            entry, args.agent_keypair, args.resolver_keypair, args.rpc, args.num_choices,
        )
        print(f"   status: {entry.status}")
        if entry.submit_tx_sig:
            print(f"   submit sig: {entry.submit_tx_sig}")
        if entry.prediction_pda:
            print(f"   prediction PDA: {entry.prediction_pda}")
        if entry.error:
            print(f"   error: {entry.error[:300]}")

        # Merge back into the entries list by slug
        for j, e in enumerate(entries):
            if e.slug == entry.slug:
                entries[j] = entry
                break

        # Persist after each submit
        raw["entries"] = [asdict(e) for e in entries]
        raw["rpc"] = args.rpc
        raw["program_id"] = PROGRAM_ID
        manifest_path.write_text(json.dumps(raw, indent=2, ensure_ascii=False))

    # Summary
    by_status: dict[str, int] = {}
    for e in entries:
        by_status[e.status] = by_status.get(e.status, 0) + 1
    print("\n" + "=" * 60)
    print("SUMMARY")
    for status, n in sorted(by_status.items()):
        print(f"  {status}: {n}")
    print(f"\nmanifest updated: {manifest_path}")
    return 0 if all(e.status == "submitted" for e in eligible) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--fixtures", help="Glob for fixtures (e.g. 'eval/fixtures/live_*.md')")
    parser.add_argument(
        "--from-manifest",
        help="Existing manifest to resume from. Skips skill chain; only runs devnet submit "
             "for entries with status=triage+prediction_ok and no submit_tx_sig. Requires --submit-devnet.",
    )
    parser.add_argument("--manifest", help="Output manifest path (default: eval/outputs/batch_<utc_ts>.json)")
    parser.add_argument("--num-choices", type=int, default=2)
    parser.add_argument("--model", default=None, help="Override Hermes model for this batch")
    parser.add_argument("--submit-devnet", action="store_true")
    parser.add_argument("--agent-keypair", default=None)
    parser.add_argument("--resolver-keypair", default=None)
    parser.add_argument("--rpc", default="https://api.devnet.solana.com")
    parser.add_argument("--dry-run", action="store_true", help="List fixtures only; no LLM or chain calls")
    args = parser.parse_args()

    if args.from_manifest:
        if not args.submit_devnet:
            print("[x] --from-manifest requires --submit-devnet")
            return 2
        if not (args.agent_keypair and args.resolver_keypair):
            print("[x] --submit-devnet requires --agent-keypair and --resolver-keypair")
            return 2
        return run_from_manifest(args)

    if not args.fixtures:
        print("[x] --fixtures is required (unless --from-manifest is used)")
        return 2

    if args.submit_devnet and not (args.agent_keypair and args.resolver_keypair):
        print("[x] --submit-devnet requires --agent-keypair and --resolver-keypair")
        return 2

    fixtures = sorted(Path(p) for p in glob.glob(args.fixtures))
    if not fixtures:
        print(f"[x] no fixtures matched: {args.fixtures}")
        return 2

    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    manifest_path = Path(args.manifest).resolve() if args.manifest else REPO_ROOT / "eval" / "outputs" / f"batch_{ts}.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    artifacts_dir = manifest_path.with_name(manifest_path.stem + "_artifacts")
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    print(f"fixtures:  {len(fixtures)}")
    print(f"manifest:  {manifest_path}")
    print(f"artifacts: {artifacts_dir}")
    print(f"mode:      {'devnet submit' if args.submit_devnet else 'skill chain only'}")
    print("=" * 60)

    if args.dry_run:
        for f in fixtures:
            print(f"  - {f.name}")
        return 0

    entries: list[ManifestEntry] = []
    for i, f in enumerate(fixtures, 1):
        print(f"\n[{i}/{len(fixtures)}] {f.name}")
        try:
            entry = process_fixture(
                f, args.num_choices, args.model, artifacts_dir,
                args.submit_devnet, args.agent_keypair, args.resolver_keypair, args.rpc,
            )
        except Exception as e:
            entry = ManifestEntry(
                fixture=f.name, slug=f.stem,
                status="unexpected_error",
                error=f"{type(e).__name__}: {e}\n{traceback.format_exc()}",
            )
        entries.append(entry)

        print(f"   status: {entry.status}")
        if entry.predicted_outcome is not None:
            print(f"   prediction: outcome={entry.predicted_outcome}, confidence_bps={entry.confidence_bps}")
        if entry.red_flag_categories:
            print(f"   red_flags: {', '.join(entry.red_flag_categories)}")
        if entry.submit_tx_sig:
            print(f"   submit sig: {entry.submit_tx_sig}")
        if entry.error:
            print(f"   error: {entry.error[:300]}")

        # Persist after each entry so a crash mid-batch keeps completed work.
        manifest = {
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "rpc": args.rpc if args.submit_devnet else None,
            "program_id": PROGRAM_ID if args.submit_devnet else None,
            "num_choices": args.num_choices,
            "entries": [asdict(e) for e in entries],
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))

    # Summary
    by_status: dict[str, int] = {}
    for e in entries:
        by_status[e.status] = by_status.get(e.status, 0) + 1
    print("\n" + "=" * 60)
    print("SUMMARY")
    for status, n in sorted(by_status.items()):
        print(f"  {status}: {n}")
    print(f"\nmanifest written to: {manifest_path}")

    successful_states = {"submitted", "triage+prediction_ok"}
    return 0 if all(e.status in successful_states for e in entries) else 1


if __name__ == "__main__":
    sys.exit(main())
