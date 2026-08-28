# Lark Solutions Group — Claude Code plugin

Skills that Clad Forge builds and maintains for Lark Solutions Group. LSG adds
this repository once as a Claude Code marketplace; every skill published here
afterwards reaches them as an update.

- **Marketplace:** `lark-solutions-group`
- **Plugin:** `lsg` — its skills appear as `/lsg:<skill-name>`
- **Skills:** none yet

## For LSG — installing

```
/plugin marketplace add Clad-Forge/CF_lark-solutions-group-plugin
/plugin install lsg@lark-solutions-group
```

The repository is private, so this needs a GitHub account with read access and
git signed in on the machine. Full instructions, including updates and
troubleshooting, are in **[docs/client-setup.md](docs/client-setup.md)** — that
is the page to send to the client.

## For Clad Forge — adding a skill

```bash
./scripts/new-skill.sh receipt-check   # scaffold skills/receipt-check/
# write and test it — docs/authoring-skills.md
./scripts/validate.sh                  # check it
./scripts/release.sh minor             # bump, changelog, tag
git push -u origin main --follow-tags  # ship it
```

**Clients only receive an update when `version` in `.claude-plugin/plugin.json`
changes.** A push alone changes nothing on their machines. `release.sh` handles
the bump, and CI fails any pull request that skips it.

## Layout

```
.claude-plugin/
  plugin.json          the plugin: name, version, description
  marketplace.json     the marketplace clients add; lists this one plugin
skills/                one folder per skill — the folder name is the command
templates/skill/       the starting point new-skill.sh copies (not shipped)
scripts/               scaffold, validate, release
docs/                  setup, authoring and release guides
```

Only `skills/` ships as skills. `templates/` is a starting point for you and
never reaches a client's `/` menu.

## Documentation

| | |
| --- | --- |
| [docs/client-setup.md](docs/client-setup.md) | Install, update and troubleshooting — written for LSG. |
| [docs/authoring-skills.md](docs/authoring-skills.md) | How to write a skill that fires when it should and works when it runs. |
| [docs/releasing.md](docs/releasing.md) | Versioning and publishing. |
| [CHANGELOG.md](CHANGELOG.md) | What shipped in each version. |

## Checks

`./scripts/validate.sh` runs on every push and pull request. It checks that each
skill has a `SKILL.md` with a usable description, that the frontmatter name
matches its folder — in a plugin skill the name sets the command, so a mismatch
silently renames it — that no template placeholder text is left behind, and that
both manifests are valid. Pull requests are additionally checked for the version
bump.

---

Maintained by Clad Forge — cort@cladforge.com
