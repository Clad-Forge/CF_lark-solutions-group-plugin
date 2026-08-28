#!/usr/bin/env bash
# Check every skill and both manifests. Run before you push.
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 "$repo_root/scripts/validate_skills.py" "$repo_root"

# The Claude Code CLI is the authority on manifest shape; use it when it is here.
if command -v claude >/dev/null 2>&1; then
  echo
  claude plugin validate "$repo_root" --strict
  claude plugin validate "$repo_root/.claude-plugin/plugin.json" --strict
else
  echo
  echo "note: 'claude' CLI not found — skipped manifest schema validation."
  echo "      Install it to run the full check: npm i -g @anthropic-ai/claude-code"
fi
