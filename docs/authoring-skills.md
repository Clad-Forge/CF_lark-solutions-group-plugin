# Writing a skill

A skill is a folder under `skills/` with a `SKILL.md` inside it. The folder name
becomes the command: `skills/receipt-check/` ships as `/lsg:receipt-check`.

## Start it

```bash
./scripts/new-skill.sh receipt-check
```

That copies `templates/skill/` into `skills/receipt-check/` and fills in the
name. Everything below is about filling it in well.

## The description is the most important line

Claude never reads a skill's body until it has already decided to use it. That
decision is made against the `description` alone, so the description is what
makes a skill fire at the right moment — or sit unused.

Write what it does, then the phrases people actually type:

```yaml
description: Reconcile a project's receipts against the Invoice Tracker, rename
  them to the West Run convention, and file them by category. Use when the user
  says "check the receipts", "run step 4", or "organise the receipts".
```

Not this — it says what the skill is about, but never when to reach for it:

```yaml
description: Receipt utilities.
```

Rules of thumb:

- Lead with the concrete job, not the category.
- Name real trigger phrases, in the words LSG staff use.
- Keep `description` plus `when_to_use` under 1,536 characters. Past that it is
  cut from the listing Claude reads, so the tail is wasted.

## Write the body for someone who will not ask questions

Claude follows the body literally and cannot check back mid-run. So:

- **Number the steps** in the order they run.
- **Give exact commands**, not descriptions of commands.
- **Say what done looks like** for each step — the file that appears, the value
  that matches.
- **End every branch in an action or a stop.** "If the workbook is missing, say
  which one and stop" beats leaving it open.
- **Forbid the tempting shortcut.** If there is a wrong-but-easy path, name it:
  "never infer the vendor from the filename".
- **Say what to report.** A skill that finishes silently gets run twice by a
  user who cannot tell whether it worked.

## Put long material in supporting files

The body loads only when the skill runs, and supporting files load only when
Claude follows the link. Long reference material is close to free, so keep
`SKILL.md` to the steps and push the detail down:

```
skills/receipt-check/
  SKILL.md          the steps
  references/       specs, contracts, worked examples
  scripts/          helper scripts the skill runs
  assets/           templates and files the skill copies out
```

Link them by relative path from `SKILL.md`. When the working directory could be
anything, use `${CLAUDE_SKILL_DIR}`, which always resolves to the skill's own
folder wherever the client installed it:

```markdown
Full contract: `references/receipt-check-spec.md`

    python "${CLAUDE_SKILL_DIR}/scripts/extract.py" --project "<project>"
```

Never hard-code a path from your own machine. `C:\Users\...` works for you and
fails for every client.

## Frontmatter worth knowing

`name` and `description` are all you need. These are the ones that earn their
place in this plugin:

| Field | Use it for |
| --- | --- |
| `disable-model-invocation: true` | Anything with side effects — writing, renaming, sending. Only the user can then run it, by typing the command. |
| `allowed-tools` | Tools the skill may use without a permission prompt, e.g. `Read Grep`. Keep it to what the skill genuinely needs. |
| `argument-hint` | A hint shown in `/` autocomplete, e.g. `[project-name]`. |
| `when_to_use` | More trigger phrases, when they will not fit in the description. |

In a plugin skill the frontmatter `name` **sets the command**, so it must match
the folder name — `./scripts/validate.sh` fails the build if the two drift.

The full field list is in the
[skills reference](https://code.claude.com/docs/en/skills#frontmatter-reference).

## Test before you push

Validation catches shape problems:

```bash
./scripts/validate.sh
```

But it cannot tell you whether the skill actually works. Do that too — point a
real Claude Code session at a copy of the plugin:

```bash
cp -R . ~/.claude/skills/lsg-dev
```

Start a session, and check three things:

1. **It fires.** Ask for the job in the words a client would use, without naming
   the skill. If Claude does not reach for it, the description is the problem.
2. **It runs.** Give it a real project folder and watch it through.
3. **It stops well.** Take something away — a missing workbook, an empty folder
   — and confirm it stops and says why, rather than guessing.

Remove the copy when you are done, so it does not shadow the installed plugin:

```bash
rm -rf ~/.claude/skills/lsg-dev
```

## Then ship it

See [releasing.md](releasing.md). The short version: clients get nothing until
the version in `plugin.json` changes, and `./scripts/release.sh` is what changes
it.
