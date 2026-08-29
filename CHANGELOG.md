# Changelog

What changed in each released version of the `lsg` plugin. Clients see a new
version only when `version` in `.claude-plugin/plugin.json` changes, so every
release gets an entry here.

Write what changed under `## [Unreleased]` as you work; `./scripts/release.sh`
moves it under the new version number and dates it.

## [Unreleased]

- `docs/client-setup.md`: added a second install route for clients who would
  rather click than type — register the marketplace with a `settings.json`
  file, then install from the **+ → Plugins** panel. Documented the updates
  panel alongside the update commands, and expanded troubleshooting to cover
  the two things that actually catch people out: `marketplace add` alone
  installing nothing, and Notepad saving `settings.json.txt`.

## [0.2.1] — 2026-08-29

- `process-vouchers`: the plugin repository is now the source of truth for the
  skill. The script and reference headers said they were generated copies that
  `build_plugin.py` and `build_skill.py` would overwrite; they now say to edit
  here and warn against running either builder against this repo. Comments
  only — no change to what the skill does.

## [0.2.0] — 2026-08-29

- Added `process-vouchers`, the West Run voucher pipeline: parse, reconcile
  receipts, file by category, build the Invoice Tracker and write the
  QuickBooks bill import. Run it with `/lsg:process-vouchers`.
- The skill resolves its bundled scripts through `${CLAUDE_SKILL_DIR}`, so it
  works wherever the plugin is installed.
- Needs Python with `openpyxl` on the machine; `pymupdf` is optional and saves
  reading PDF receipts by eye. The plugin does not bundle an interpreter.

## [0.1.0] — 2026-08-28

- Set the repository up as a Claude Code plugin and marketplace, so Lark
  Solutions Group can install it once and receive skill updates on publish.
- Added the skill template, scaffolding, validation and release scripts.
- No skills yet.
