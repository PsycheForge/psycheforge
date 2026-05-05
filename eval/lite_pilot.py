#!/usr/bin/env python3
"""Lite-tier pilot wrapper — single command from proposal text → delegate-facing
Lite-tier markdown analysis.

Usage:
    # Read proposal from a markdown file (optionally with YAML frontmatter
    # carrying source_url + dao_context):
    python eval/lite_pilot.py --proposal path/to/proposal.md

    # Paste proposal text via stdin:
    cat proposal.md | python eval/lite_pilot.py --paste \\
        --source-url https://forum.marinade.finance/t/... \\
        --dao-context "Marinade Finance DAO"

    # Publish output as a public GitHub gist (requires `gh` CLI authenticated):
    python eval/lite_pilot.py --proposal proposal.md --gist

Pipeline:
    proposal text → governance-triage skill (Hermes) → triage JSON → Lite-tier
    markdown via the format_triage.py renderers.

This is the customer-facing entry point for the Lite tier. No prediction layer,
no on-chain submission. Just structured triage with verbatim citations.
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
from datetime import datetime, timezone
from typing import Any

import yaml
from jsonschema import Draft202012Validator

# Reuse the Lite-tier renderers from format_triage.py
sys.path.insert(0, str(REPO_ROOT / "eval"))
from format_triage import (  # noqa: E402
    render_header, render_tldr, render_treasury, render_red_flags,
    render_stakeholders, render_questions, render_confidence, render_footer,
)

TRIAGE_SKILL = REPO_ROOT / "skills" / "governance-triage"
TRIAGE_SCHEMA = TRIAGE_SKILL / "references" / "output-schema.json"
TRIAGE_HERMES_ID = "research/governance-triage"
FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)\n```", re.DOTALL)


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


def hermes_exec(skill_id: str, prompt: str, model: str | None = None, timeout: int = 300) -> str:
    venv_hermes = REPO_ROOT / ".hermes-agent" / "venv" / "bin" / "hermes"
    exe = str(venv_hermes) if venv_hermes.exists() else "hermes"
    cmd = [exe, "chat", "-q", prompt, "-s", skill_id, "-Q"]
    if model:
        cmd.extend(["-m", model])
    result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=timeout)
    return result.stdout


def parse_input_markdown(md_path: Path) -> tuple[dict[str, Any], str]:
    text = md_path.read_text()
    if text.startswith("---\n"):
        _, fm_raw, body = text.split("---\n", 2)
        return yaml.safe_load(fm_raw) or {}, body.strip()
    return {}, text.strip()


def build_prompt(proposal_text: str, source_url: str | None, dao_context: str | None) -> str:
    return (
        "Analyze this Solana DAO proposal using the governance-triage skill. "
        "Return ONLY a single JSON object matching the skill's output schema.\n"
        "\n"
        f"DAO context: {dao_context or '(none provided)'}\n"
        f"Source URL: {source_url or '(none provided)'}\n"
        "\n"
        "PROPOSAL TEXT:\n"
        f"{proposal_text}\n"
    )


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    return s.strip("-")[:60]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--proposal", type=Path, help="Markdown file (optional YAML frontmatter for source_url + dao_context)")
    parser.add_argument("--paste", action="store_true", help="Read proposal text from stdin")
    parser.add_argument("--source-url", help="Source URL (overrides frontmatter)")
    parser.add_argument("--dao-context", help="DAO context (overrides frontmatter)")
    parser.add_argument("--output", type=Path, help="Output markdown path (default: eval/outputs/pilot/<slug>_triage.md)")
    parser.add_argument("--model", help="Override Hermes model")
    parser.add_argument("--gist", action="store_true", help="Publish output as a public GitHub gist (requires `gh` CLI)")
    parser.add_argument("--validate", action="store_true", help="Schema-validate triage output before formatting (default: skip for speed)")
    args = parser.parse_args()

    if not args.proposal and not args.paste:
        parser.error("Provide --proposal <path> or --paste (read stdin)")

    # Read input
    if args.paste:
        proposal_text = sys.stdin.read().strip()
        frontmatter: dict[str, Any] = {}
        slug = "pasted-proposal"
        if not proposal_text:
            print("[x] no text on stdin", file=sys.stderr)
            return 2
    else:
        if not args.proposal.exists():
            print(f"[x] file not found: {args.proposal}", file=sys.stderr)
            return 2
        frontmatter, proposal_text = parse_input_markdown(args.proposal)
        slug = args.proposal.stem.lstrip("live_")

    source_url = args.source_url or frontmatter.get("source_url")
    dao_context = args.dao_context or frontmatter.get("dao_context")

    if not source_url:
        print("[!] no source_url provided — output will not link back to the proposal", file=sys.stderr)
    if not dao_context:
        print("[!] no dao_context provided — skill will see '(none provided)'", file=sys.stderr)

    output_path = args.output or REPO_ROOT / "eval" / "outputs" / "pilot" / f"{slugify(slug)}_triage.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Run triage
    print(f"[1/2] Running governance-triage skill...", file=sys.stderr)
    prompt = build_prompt(proposal_text, source_url, dao_context)
    try:
        raw = hermes_exec(TRIAGE_HERMES_ID, prompt, args.model)
    except subprocess.CalledProcessError as e:
        print(f"[x] hermes invocation failed:\n  stderr: {e.stderr[:500]}", file=sys.stderr)
        return 1
    except FileNotFoundError:
        print("[x] `hermes` CLI not found. Run ./eval/setup_hermes_local.sh first.", file=sys.stderr)
        return 1

    try:
        triage = extract_json(raw)
    except json.JSONDecodeError as e:
        print(f"[x] could not extract JSON from skill output: {e}", file=sys.stderr)
        print(f"  first 500 chars: {raw[:500]!r}", file=sys.stderr)
        return 1

    if args.validate:
        schema = json.loads(TRIAGE_SCHEMA.read_text())
        errors = list(Draft202012Validator(schema).iter_errors(triage))
        if errors:
            print(f"[x] triage schema invalid ({len(errors)} errors):", file=sys.stderr)
            for err in errors[:5]:
                path = ".".join(str(p) for p in err.absolute_path) or "<root>"
                print(f"  {path}: {err.message}", file=sys.stderr)
            return 1

    # Save raw triage JSON next to the markdown for archival / debugging
    json_path = output_path.with_suffix(".json")
    json_path.write_text(json.dumps(triage, indent=2, ensure_ascii=False))

    # Format Lite tier markdown
    print(f"[2/2] Formatting Lite tier markdown...", file=sys.stderr)
    parts = [
        render_header(triage, source_url),
        render_tldr(triage),
        render_treasury(triage),
        render_red_flags(triage),
        render_stakeholders(triage),
        render_questions(triage),
        render_confidence(triage),
        render_footer("Lite"),
    ]
    md = "\n".join(parts)
    output_path.write_text(md)

    print(f"[ok] wrote {output_path}", file=sys.stderr)
    print(f"[ok] raw json:  {json_path}", file=sys.stderr)

    # Optional gist publish
    if args.gist:
        print(f"[3/3] Publishing to GitHub gist...", file=sys.stderr)
        try:
            result = subprocess.run(
                ["gh", "gist", "create", str(output_path), "--public",
                 "--desc", f"PsycheForge Lite triage — {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"],
                capture_output=True, text=True, check=True, timeout=30,
            )
            gist_url = result.stdout.strip()
            print(f"[ok] gist: {gist_url}", file=sys.stderr)
            sys.stdout.write(gist_url + "\n")
        except FileNotFoundError:
            print("[x] `gh` CLI not found — install GitHub CLI to use --gist", file=sys.stderr)
            return 1
        except subprocess.CalledProcessError as e:
            print(f"[x] gist publish failed: {e.stderr[:300]}", file=sys.stderr)
            return 1
    else:
        sys.stdout.write(str(output_path) + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
