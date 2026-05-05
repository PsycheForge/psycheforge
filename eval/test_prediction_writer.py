#!/usr/bin/env python3
"""Two-step skill chain test: governance-triage -> prediction-writer.

Usage:
    python eval/test_prediction_writer.py <fixture.md> [--num-choices N]

Pipeline:
    1. Run governance-triage on the fixture -> triage JSON.
    2. Feed the triage JSON into prediction-writer -> prediction JSON.
    3. Validate both outputs against their JSON schemas.
    4. Check Hard Rule #2 (confidence cap based on triage.confidence.overall).
    5. Print the prediction for manual review.

The runner auto-re-execs under .hermes-agent/venv/bin/python when that venv
exists. Set HERMES_NO_REEXEC=1 to debug with system Python.
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
import json
import re
import subprocess
from typing import Any

import yaml
from jsonschema import Draft202012Validator

TRIAGE_SKILL = REPO_ROOT / "skills" / "governance-triage"
PREDICTION_SKILL = REPO_ROOT / "skills" / "prediction-writer"
TRIAGE_SCHEMA = TRIAGE_SKILL / "references" / "output-schema.json"
PREDICTION_SCHEMA = PREDICTION_SKILL / "references" / "output-schema.json"
FIXTURES_DIR = REPO_ROOT / "eval" / "fixtures"

TRIAGE_HERMES_ID = "research/governance-triage"
PREDICTION_HERMES_ID = "research/prediction-writer"

_FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)\n```", re.DOTALL)


def extract_json(response: str) -> dict[str, Any]:
    text = response.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    fenced = _FENCE_RE.search(text)
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


def hermes_exec(skill_id: str, prompt: str, model: str | None = None, timeout: int = 300) -> str:
    venv_hermes = REPO_ROOT / ".hermes-agent" / "venv" / "bin" / "hermes"
    exe = str(venv_hermes) if venv_hermes.exists() else "hermes"
    cmd = [exe, "chat", "-q", prompt, "-s", skill_id, "-Q"]
    if model:
        cmd.extend(["-m", model])
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, timeout=timeout,
        )
    except FileNotFoundError as e:
        raise RuntimeError(
            "hermes CLI not found. Run ./eval/setup_hermes_local.sh first."
        ) from e
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"hermes chat ({skill_id}) exited {e.returncode}.\n"
            f"stderr: {e.stderr[:800]}\nstdout: {e.stdout[:200]}"
        ) from e
    return result.stdout


def build_triage_prompt(proposal_text: str, frontmatter: dict[str, Any]) -> str:
    source_url = frontmatter.get("source_url") or "(none provided)"
    dao_context = frontmatter.get("dao_context") or "(none provided)"
    return (
        "Analyze this Solana DAO proposal using the governance-triage skill. "
        "Return ONLY a single JSON object matching the skill's output schema.\n"
        "\n"
        f"DAO context: {dao_context}\n"
        f"Source URL: {source_url}\n"
        "\n"
        "PROPOSAL TEXT:\n"
        f"{proposal_text}\n"
    )


def build_prediction_prompt(triage_json: dict[str, Any], num_choices: int) -> str:
    return (
        "Apply the prediction-writer skill to the governance-triage output below. "
        "Return ONLY a single JSON object matching the skill's output schema.\n"
        "\n"
        f"Proposal num_choices: {num_choices}\n"
        "Choice convention (pin this — do not infer a different one):\n"
        "  index 0 = approve / yes / pass (the proposal is adopted)\n"
        "  index 1 = reject / no / fail (the proposal is rejected)\n"
        "  This matches Solana SPL Governance default choice ordering.\n"
        "\n"
        "GOVERNANCE-TRIAGE OUTPUT:\n"
        f"{json.dumps(triage_json, indent=2, ensure_ascii=False)}\n"
    )


def validate_schema(output: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema)
    return [
        f"{'.'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
        for e in validator.iter_errors(output)
    ]


def check_confidence_cap(prediction: dict[str, Any], triage_conf_overall: str | None) -> tuple[bool, int, int]:
    """Hard Rule #2: confidence_bps capped by triage.confidence.overall."""
    caps = {"low": 6000, "medium": 8000, "high": 9500}
    cap = caps.get(triage_conf_overall or "", 10000)
    got = int(prediction.get("confidence_bps", 0))
    return got <= cap, cap, got


def main() -> int:
    parser = argparse.ArgumentParser(description="Run governance-triage -> prediction-writer chain.")
    parser.add_argument("fixture", help="Filename in eval/fixtures/ (e.g. adversarial_permission.md)")
    parser.add_argument("--num-choices", type=int, default=2, help="Proposal choice count (default 2)")
    parser.add_argument("--model", default=None, help="Override Hermes model")
    parser.add_argument("--verbose", action="store_true", help="Dump full JSON for both stages")
    args = parser.parse_args()

    fixture_path = FIXTURES_DIR / args.fixture
    if not fixture_path.exists():
        print(f"[x] Fixture not found: {fixture_path}")
        return 2

    for path in [TRIAGE_SCHEMA, PREDICTION_SCHEMA]:
        if not path.exists():
            print(f"[x] Schema missing: {path}")
            return 2

    frontmatter, body = parse_fixture(fixture_path)

    print(f"fixture:           {fixture_path.name}")
    print(f"triage skill:      {TRIAGE_HERMES_ID}")
    print(f"prediction skill:  {PREDICTION_HERMES_ID}")
    print(f"num_choices:       {args.num_choices}")
    print("=" * 60)

    # ── Step 1: governance-triage ──────────────────────────────────────
    print("[1/2] Running governance-triage...")
    try:
        triage_raw = hermes_exec(TRIAGE_HERMES_ID, build_triage_prompt(body, frontmatter), args.model)
    except RuntimeError as e:
        print(f"[x] triage invocation failed:\n{e}")
        return 1

    try:
        triage_json = extract_json(triage_raw)
    except json.JSONDecodeError as e:
        print(f"[x] triage returned non-JSON: {e}")
        print(f"    first 500 chars: {triage_raw[:500]!r}")
        return 1

    triage_errors = validate_schema(triage_json, json.loads(TRIAGE_SCHEMA.read_text()))
    if triage_errors:
        print(f"[x] triage schema errors ({len(triage_errors)}):")
        for err in triage_errors[:5]:
            print(f"    - {err}")
        return 1

    tri_conf = (triage_json.get("confidence") or {}).get("overall")
    print("    schema: valid")
    print(f"    red_flags: {len(triage_json.get('red_flags') or [])}")
    print(f"    treasury_impact: {(triage_json.get('treasury_impact') or {}).get('direction')}")
    print(f"    triage.confidence.overall: {tri_conf}")

    # ── Step 2: prediction-writer ──────────────────────────────────────
    print("\n[2/2] Running prediction-writer...")
    try:
        pred_raw = hermes_exec(
            PREDICTION_HERMES_ID,
            build_prediction_prompt(triage_json, args.num_choices),
            args.model,
        )
    except RuntimeError as e:
        print(f"[x] prediction invocation failed:\n{e}")
        return 1

    try:
        pred_json = extract_json(pred_raw)
    except json.JSONDecodeError as e:
        print(f"[x] prediction returned non-JSON: {e}")
        print(f"    first 500 chars: {pred_raw[:500]!r}")
        return 1

    pred_errors = validate_schema(pred_json, json.loads(PREDICTION_SCHEMA.read_text()))
    if pred_errors:
        print(f"[x] prediction schema errors ({len(pred_errors)}):")
        for err in pred_errors[:5]:
            print(f"    - {err}")
        schema_ok = False
    else:
        print("    schema: valid")
        schema_ok = True

    # Hard Rule #2: confidence cap
    cap_ok, cap, got = check_confidence_cap(pred_json, tri_conf)
    mark = "[ok]" if cap_ok else "[x] "
    print(f"    {mark} Hard Rule #2: confidence_bps={got}, cap={cap} (triage_conf={tri_conf})")

    # ── Report ─────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("PREDICTION")
    print("-" * 60)
    print(f"  predicted_outcome:  {pred_json.get('predicted_outcome')}")
    print(f"  confidence_bps:     {pred_json.get('confidence_bps')}")
    print(f"  reasoning_citation: {pred_json.get('reasoning_citation')}")
    print(f"  key_triage_signals:")
    for sig in pred_json.get("key_triage_signals") or []:
        print(f"    - {sig}")

    if args.verbose:
        print("\n" + "=" * 60)
        print("FULL TRIAGE JSON")
        print(json.dumps(triage_json, indent=2, ensure_ascii=False))
        print("\n" + "=" * 60)
        print("FULL PREDICTION JSON")
        print(json.dumps(pred_json, indent=2, ensure_ascii=False))

    print("\n" + "=" * 60)
    summary = "PASS" if (schema_ok and cap_ok) else "FAIL"
    print(f"Summary: {summary}")
    return 0 if (schema_ok and cap_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
