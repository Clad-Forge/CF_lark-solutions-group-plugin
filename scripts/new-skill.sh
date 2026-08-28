#!/usr/bin/env bash
# Scaffold a new skill from templates/skill/ into skills/<name>/.
#
#   ./scripts/new-skill.sh receipt-check
#
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
name="${1:-}"

if [[ -z "$name" ]]; then
  echo "usage: $0 <skill-name>" >&2
  echo "       skill-name must be kebab-case, e.g. receipt-check" >&2
  exit 64
fi

if [[ ! "$name" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
  echo "error: '$name' is not kebab-case (lowercase letters, digits and single hyphens)." >&2
  exit 65
fi

dest="$repo_root/skills/$name"
if [[ -e "$dest" ]]; then
  echo "error: $dest already exists — edit it, or pick another name." >&2
  exit 73
fi

cp -R "$repo_root/templates/skill" "$dest"

# The template ships a placeholder name; the directory name is the real one.
if sed --version >/dev/null 2>&1; then
  sed -i "s/^name: SKILL_NAME$/name: $name/" "$dest/SKILL.md"      # GNU sed
else
  sed -i '' "s/^name: SKILL_NAME$/name: $name/" "$dest/SKILL.md"   # BSD/macOS sed
fi

cat <<EOF
Created skills/$name/

Next:
  1. Edit skills/$name/SKILL.md — the description decides when Claude reaches
     for it, so write that first and be specific about the trigger phrases.
  2. Delete the AUTHORING NOTES comment block at the bottom.
  3. Drop anything long into skills/$name/references/ and link it from SKILL.md,
     or delete that folder if you do not need it.
  4. Test it, then ship it:
       ./scripts/validate.sh
       ./scripts/release.sh minor
EOF
