#!/usr/bin/env python3
"""Check the plugin's manifests and skills before they reach a client.

Dependency-free on purpose: it runs anywhere python3 does, including CI, with
nothing installed. Errors fail the run; warnings fail it only under --strict.

    python3 scripts/validate_skills.py [repo_root] [--strict]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Claude Code truncates description + when_to_use at this many characters in the
# skill listing, so anything past it is invisible when Claude picks a skill.
DESCRIPTION_CAP = 1536
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
PLACEHOLDERS = ("SKILL_NAME", "AUTHORING NOTES", "TODO —", "TODO:")

errors: list[str] = []
warnings: list[str] = []


def error(where: str, msg: str) -> None:
    errors.append(f"{where}: {msg}")


def warn(where: str, msg: str) -> None:
    warnings.append(f"{where}: {msg}")


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """Pull top-level scalar keys out of YAML frontmatter.

    Deliberately small: it only needs the handful of scalar fields we check, and
    folded values (a key whose value continues on indented lines below it).
    Returns None when the file has no frontmatter block at all.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return None

    fields: dict[str, str] = {}
    key: str | None = None
    for raw in lines[1:end]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw[:1] in (" ", "\t") and key:          # continuation of a folded value
            fields[key] = f"{fields[key]} {raw.strip()}".strip()
            continue
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", raw)
        if match:
            key = match.group(1)
            fields[key] = match.group(2).strip()
        else:
            key = None
    return fields


def check_manifests(root: Path) -> tuple[str | None, str | None]:
    plugin_path = root / ".claude-plugin" / "plugin.json"
    market_path = root / ".claude-plugin" / "marketplace.json"
    plugin_name = version = None

    for path in (plugin_path, market_path):
        if not path.exists():
            error(path.name, "missing — the plugin cannot be installed without it.")

    if plugin_path.exists():
        try:
            plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            error("plugin.json", f"is not valid JSON ({exc}).")
        else:
            plugin_name = plugin.get("name")
            version = plugin.get("version")
            if not plugin_name:
                error("plugin.json", "has no 'name'.")
            elif not KEBAB.match(plugin_name):
                error("plugin.json", f"name '{plugin_name}' must be kebab-case.")
            if not version:
                error(
                    "plugin.json",
                    "has no 'version'. Clients only receive updates when it changes.",
                )
            elif not SEMVER.match(version):
                error("plugin.json", f"version '{version}' is not semver (e.g. 1.2.0).")
            if not plugin.get("description"):
                warn("plugin.json", "has no 'description'.")

    if market_path.exists():
        try:
            market = json.loads(market_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            error("marketplace.json", f"is not valid JSON ({exc}).")
        else:
            if not market.get("name"):
                error("marketplace.json", "has no 'name'.")
            if not market.get("owner", {}).get("name"):
                error("marketplace.json", "has no 'owner.name'.")
            entries = market.get("plugins") or []
            if not entries:
                error("marketplace.json", "lists no plugins.")
            names = [e.get("name") for e in entries]
            if plugin_name and plugin_name not in names:
                error(
                    "marketplace.json",
                    f"does not list the plugin '{plugin_name}' — clients would not see it.",
                )
            for entry in entries:
                if "version" in entry:
                    error(
                        "marketplace.json",
                        f"plugin '{entry.get('name')}' sets a version. Keep the version in "
                        "plugin.json only, so the two can never disagree.",
                    )
    return plugin_name, version


def check_skill(skill_dir: Path, root: Path) -> None:
    where = f"skills/{skill_dir.name}"
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.exists():
        error(where, "has no SKILL.md — Claude Code will not load it.")
        return
    if not KEBAB.match(skill_dir.name):
        error(where, "directory name must be kebab-case — it becomes the /command.")

    text = skill_md.read_text(encoding="utf-8")
    fields = parse_frontmatter(text)
    if fields is None:
        error(where, "SKILL.md has no YAML frontmatter block (--- ... ---).")
        return

    name = fields.get("name")
    if name and name != skill_dir.name:
        error(
            where,
            f"frontmatter name '{name}' does not match the directory. In a plugin skill "
            f"the name sets the command, so this ships as /{name} rather than "
            f"/{skill_dir.name}. Rename one of them.",
        )

    description = fields.get("description", "").strip()
    if not description:
        error(where, "has no 'description'. Claude uses it to decide when to run the skill.")
    else:
        total = len(description) + len(fields.get("when_to_use", ""))
        if total > DESCRIPTION_CAP:
            error(
                where,
                f"description + when_to_use is {total} characters; anything past "
                f"{DESCRIPTION_CAP} is cut from the skill listing.",
            )
        elif len(description) < 40:
            warn(where, "description is very short — say when to use the skill, not just what it is.")

    for placeholder in PLACEHOLDERS:
        if placeholder in text:
            error(where, f"still contains template text ({placeholder!r}). Finish or delete it.")

    body = text.split("---", 2)[-1].strip()
    if len(body) < 200:
        warn(where, "body is very thin — a skill this short is usually better as a CLAUDE.md note.")

    for link in re.findall(r"`(references/[^`]+|scripts/[^`]+|assets/[^`]+)`", body):
        if not (skill_dir / link).exists():
            warn(where, f"links to '{link}', which does not exist.")


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--strict"]
    strict = "--strict" in sys.argv[1:]
    root = Path(args[0]).resolve() if args else Path(__file__).resolve().parent.parent

    plugin_name, version = check_manifests(root)

    skills_root = root / "skills"
    skills: list[Path] = []
    if not skills_root.is_dir():
        error("skills/", "is missing.")
    else:
        for child in sorted(skills_root.iterdir()):
            if child.name.startswith(".") or child.name == ".gitkeep":
                continue
            if child.is_file():
                warn("skills/", f"'{child.name}' is a loose file; each skill needs its own directory.")
                continue
            skills.append(child)
            check_skill(child, root)

    for line in warnings:
        print(f"  warning  {line}")
    for line in errors:
        print(f"  error    {line}")

    count = len(skills)
    noun = "skill" if count == 1 else "skills"
    print(f"\n{plugin_name or 'plugin'} {version or '?'} — {count} {noun}, "
          f"{len(errors)} error(s), {len(warnings)} warning(s)")

    if errors:
        return 1
    if warnings and strict:
        print("failing: --strict treats warnings as errors")
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
