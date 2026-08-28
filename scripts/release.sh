#!/usr/bin/env bash
# Publish a new version to the client.
#
#   ./scripts/release.sh patch     # 0.1.0 -> 0.1.1   fix or wording change
#   ./scripts/release.sh minor     # 0.1.0 -> 0.2.0   new skill, or new behaviour
#   ./scripts/release.sh major     # 0.1.0 -> 1.0.0   breaking change
#   ./scripts/release.sh 1.4.2     # set it explicitly
#
# Clients only receive an update when the version in plugin.json changes, so
# this is the step that actually ships work. Pushing is left to you.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

bump="${1:-}"
if [[ -z "$bump" ]]; then
  echo "usage: $0 <major|minor|patch|X.Y.Z>" >&2
  exit 64
fi

current="$(python3 -c 'import json;print(json.load(open(".claude-plugin/plugin.json"))["version"])')"

case "$bump" in
  major|minor|patch)
    new="$(python3 - "$current" "$bump" <<'PY'
import sys
major, minor, patch = (int(p) for p in sys.argv[1].split("+")[0].split("-")[0].split("."))
part = sys.argv[2]
if part == "major":
    major, minor, patch = major + 1, 0, 0
elif part == "minor":
    minor, patch = minor + 1, 0
else:
    patch += 1
print(f"{major}.{minor}.{patch}")
PY
)" ;;
  *)
    if [[ ! "$bump" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
      echo "error: '$bump' is not major, minor, patch or a X.Y.Z version." >&2
      exit 65
    fi
    new="$bump" ;;
esac

echo "Releasing $current -> $new"
echo

./scripts/validate.sh
echo

if [[ -n "$(git status --porcelain -- . ':!CHANGELOG.md')" ]]; then
  echo "error: working tree has uncommitted changes. Commit the skill work first," >&2
  echo "       so the release commit contains only the version bump." >&2
  git status --short >&2
  exit 1
fi

# Update the changelog first: it is the step most likely to stop the release,
# and stopping before the version is bumped leaves nothing half-done.
python3 - "$new" <<'PY'
import datetime, pathlib, sys

new = sys.argv[1]
path = pathlib.Path("CHANGELOG.md")
lines = path.read_text(encoding="utf-8").splitlines()

# Match the heading as a whole line. The file's own prose mentions
# "## [Unreleased]" inline, and a substring search would hit that first.
heading = "## [Unreleased]"
start = next((i for i, line in enumerate(lines) if line.strip() == heading), None)
if start is None:
    sys.exit("CHANGELOG.md has no '## [Unreleased]' heading to release from.")

end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")),
           len(lines))
if not [line for line in lines[start + 1:end] if line.strip()]:
    sys.exit("Nothing under '## [Unreleased]' — write what changed before releasing.")

released = [heading, "", f"## [{new}] — {datetime.date.today().isoformat()}", ""]
released += [line for line in lines[start + 1:end] if line.strip()]
released += [""]
path.write_text("\n".join(lines[:start] + released + lines[end:]).rstrip() + "\n",
                encoding="utf-8")
PY

python3 - "$new" <<'PY'
import collections, json, sys
new = sys.argv[1]
path = ".claude-plugin/plugin.json"
data = json.load(open(path), object_pairs_hook=collections.OrderedDict)
data["version"] = new
json.dump(data, open(path, "w"), indent=2, ensure_ascii=False)
open(path, "a").write("\n")
PY

git add .claude-plugin/plugin.json CHANGELOG.md
git commit -m "release: lsg v$new"
git tag -a "v$new" -m "lsg v$new"

branch="$(git rev-parse --abbrev-ref HEAD)"
cat <<EOF

Tagged v$new on '$branch'.

Clients pick this up from the repository's default branch, so push it there:

    git push -u origin $branch --follow-tags

Then in their session: /plugin update lsg@lark-solutions-group
EOF
