#!/usr/bin/env bash
# Set up Hermes Agent in a project-local venv.
#
# Creates .hermes-agent/ at the repo root with its own venv/.
# Touches only the project directory — no system PATH changes, no .zshrc /
# .bashrc edits, no global installs. To remove everything: rm -rf .hermes-agent/
#
# Re-run is safe: existing clone is fast-forwarded, existing venv is reused.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HERMES_DIR="$REPO_ROOT/.hermes-agent"
VENV_DIR="$HERMES_DIR/venv"
HARNESS_REQS="$REPO_ROOT/requirements.txt"
REPO_URL="https://github.com/NousResearch/hermes-agent.git"

# Hermes discovers skills under ~/.hermes/skills/<category>/<name>/ and expects
# the identifier in the form <category>/<name>. We symlink each local skill
# there so the project directory remains the single source of truth.
HERMES_SKILL_ROOT="$HOME/.hermes/skills"
SKILL_CATEGORY="research"

# List of skill directories to register. Each becomes
# ~/.hermes/skills/$SKILL_CATEGORY/<dirname>.
SKILL_DIRS=(
    "governance-triage"
    "prediction-writer"
)

log() { printf '[%s] %s\n' "$1" "$2"; }

# --- 1. Clone or update hermes-agent ---
if [ -d "$HERMES_DIR/.git" ]; then
    log "1/5" "Updating existing clone at .hermes-agent/"
    git -C "$HERMES_DIR" fetch --depth 1 origin main
    git -C "$HERMES_DIR" reset --hard origin/main
else
    log "1/5" "Cloning hermes-agent into .hermes-agent/"
    git clone --depth 1 "$REPO_URL" "$HERMES_DIR"
fi

# --- 2. Create venv ---
if [ ! -d "$VENV_DIR" ]; then
    log "2/5" "Creating Python venv at .hermes-agent/venv/"
    python3 -m venv "$VENV_DIR"
else
    log "2/5" "Reusing existing venv at .hermes-agent/venv/"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip >/dev/null

# --- 3. Install hermes-agent (editable) ---
log "3/5" "Installing hermes-agent (editable) into the venv"
(cd "$HERMES_DIR" && pip install -e .)

# --- 4. Install eval harness deps in the same venv ---
if [ -f "$HARNESS_REQS" ]; then
    log "4/5" "Installing eval harness deps (requirements.txt) in the same venv"
    pip install -r "$HARNESS_REQS"
else
    log "4/5" "No requirements.txt found at repo root — skipping harness deps"
fi

# --- 5. Register all local skills with Hermes via symlink ---
mkdir -p "$HERMES_SKILL_ROOT/$SKILL_CATEGORY"
for dirname in "${SKILL_DIRS[@]}"; do
    src="$REPO_ROOT/skills/$dirname"
    dst="$HERMES_SKILL_ROOT/$SKILL_CATEGORY/$dirname"
    if [ -d "$src" ]; then
        log "5/5" "Registering skill: $SKILL_CATEGORY/$dirname"
        ln -sfn "$src" "$dst"
    else
        log "5/5" "Skipping $dirname (source not found at $src)"
    fi
done

cat <<EOF

================================================================
 Hermes Agent installed locally.
================================================================
 Location       : $HERMES_DIR
 Venv           : $VENV_DIR
 Skill registry : $HERMES_SKILL_ROOT/$SKILL_CATEGORY/
                  (one symlink per skill in skills/)

 Next steps:

   1. Configure a backend model + API key (one-time). Two options:

      a) Interactive:
         source .hermes-agent/venv/bin/activate
         hermes model
         deactivate

      b) API key in ~/.hermes/.env (faster):
         echo "OPENROUTER_API_KEY=sk-or-..." >> ~/.hermes/.env
         # or OPENAI_API_KEY=... / ANTHROPIC_API_KEY=... / etc.

   2. Run the harness. The test runner auto-uses the local venv;
      you do NOT need to activate it each time:

      python eval/test_governance_triage.py --dry-run   # no model needed
      python eval/test_governance_triage.py             # real invocation

   To remove everything:
      rm -rf .hermes-agent/ $HERMES_SKILL_ROOT/$SKILL_CATEGORY/
================================================================
EOF
