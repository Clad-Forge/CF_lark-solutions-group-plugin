#!/usr/bin/env bash
# Fail when skills or templates changed but the plugin version did not.
#
# Clients receive an update only when the version string in plugin.json changes,
# so shipping skill changes without a bump silently leaves them on the old copy.
#
#   ./scripts/check_version_bump.sh <base-ref>
set -euo pipefail

base="${1:-}"
if [[ -z "$base" ]]; then
  echo "usage: $0 <base-ref>" >&2
  exit 64
fi

manifest=".claude-plugin/plugin.json"
read_version() { python3 -c 'import json,sys;print(json.load(sys.stdin)["version"])'; }

changed="$(git diff --name-only "$base"...HEAD -- skills templates || true)"
if [[ -z "$changed" ]]; then
  echo "No skill changes in this range — version bump not required."
  exit 0
fi

new="$(read_version < "$manifest")"
if ! old="$(git show "$base:$manifest" 2>/dev/null | read_version)"; then
  echo "No $manifest on the base ref — treating as the first release."
  exit 0
fi

echo "Changed:"
sed 's/^/  /' <<<"$changed"
echo
echo "Version: $old -> $new"

if [[ "$old" == "$new" ]]; then
  cat >&2 <<EOF

error: skills changed but the version is still $old.

Clients only receive an update when the version in $manifest changes, so
this would ship nothing. Run:

    ./scripts/release.sh minor    # new skill or new behaviour
    ./scripts/release.sh patch    # fix or wording change
EOF
  exit 1
fi

echo "ok"
