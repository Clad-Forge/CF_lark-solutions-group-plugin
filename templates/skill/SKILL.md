---
name: SKILL_NAME
description: One sentence on what this does, then the triggers — "Use when the user says 'X', 'Y', or asks to Z." Claude matches the user's request against this string, so lead with the concrete job and name the phrases people actually type. Keep description plus when_to_use under 1,536 characters.
---

# Human readable title — what this skill is for

One or two lines on what the skill produces and for whom. If there is a written
spec, contract or SOP behind it, link it here so the detail lives in one place:
`path/to/spec.md`.

## 0. Work out where you are — do this first, silently

Say what the skill needs before it can act (a project folder, a workbook, a
client name) and how to resolve it, most reliable source first:

1. The session's current directory, if it looks right (name the marker file or
   folder that proves it).
2. A path or name the user gave.
3. Otherwise say what you looked for and stop. Do not guess.

State what you resolved in one line, then carry on without further narration.

## 1. First real step

Give the exact command or action, not a description of it:

```bash
python "<tool>/script.py" --project "<project>"
```

Say what it writes and where, so the next step can rely on it.

## 2. Next step

Number the steps in the order they run. For each one, be explicit about:

- **What counts as done.** The file that appears, the value that matches.
- **What to do when it is not.** Every branch ends in an action or a stop —
  never leave Claude to invent a recovery.
- **What never to do.** Spell out the tempting shortcut and forbid it, e.g.
  "never infer the vendor from the filename", "never re-run the parser".

## 3. Report

Say exactly what the user should see at the end — the summary line, the table,
the file written. Skills that end quietly get re-run by users who cannot tell
whether they worked.

## Rules

Short, absolute statements that hold across every step. Keep them few enough to
be read every time:

- Never modify anything in `01-Inbox`.
- If a required tool or dependency is missing, say which one and stop — do not
  attempt a silent install.
- Ask before overwriting a file that already exists.

<!--
AUTHORING NOTES — delete this block before shipping.

* The directory name is the command: skills/receipt-check/ → /lsg:receipt-check.
* Test it before you push: see docs/authoring-skills.md, "Test before you push".
* Supporting files (progressive disclosure) — the body below loads only when the
  skill runs, and these load only when Claude follows the link, so long
  reference material is cheap:
      references/  background and specs Claude reads when it needs them
      scripts/     helper scripts the skill runs
      assets/      templates and files the skill copies out
  Link them by relative path, or use ${CLAUDE_SKILL_DIR} when the working
  directory could be anything:
      ${CLAUDE_SKILL_DIR}/scripts/render.sh
* Useful optional frontmatter (see docs/authoring-skills.md for the full list):
      disable-model-invocation: true   only the user can run it — use for
                                       anything with side effects
      allowed-tools: Read Grep         skip permission prompts for these tools
      argument-hint: [project-name]    shown during / autocomplete
-->
