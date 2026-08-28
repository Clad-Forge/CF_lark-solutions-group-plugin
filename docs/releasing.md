# Publishing an update

## The one thing to remember

**Clients receive an update only when `version` in
`.claude-plugin/plugin.json` changes.**

Pushing to `main` is not enough on its own. Claude Code pins the plugin to the
version string it last saw, so a push that edits a skill without bumping the
version reaches the client's machine and changes nothing they can see. This is
the single easiest way to think you have shipped something when you have not.

`./scripts/release.sh` does the bump, so use it and the problem does not arise.
CI also fails any pull request that touches `skills/` without one.

## The flow

```bash
./scripts/new-skill.sh some-skill     # or edit an existing skills/<name>/SKILL.md
# ...write and test it — see authoring-skills.md...

# note what changed under "## [Unreleased]" in CHANGELOG.md
git add -A && git commit -m "Add some-skill"

./scripts/release.sh minor            # validates, bumps, dates the changelog, tags
git push -u origin main --follow-tags
```

Then tell the client to run:

```
/plugin marketplace update lark-solutions-group
/plugin update lsg@lark-solutions-group
```

## Which bump

| | When |
| --- | --- |
| `patch` | A fix, a clearer instruction, a wording change. Nothing new to learn. |
| `minor` | A new skill, or new behaviour in one. The normal case. |
| `major` | A break — a command renamed or removed, a changed input the client has to know about. Tell them directly as well. |

## What `release.sh` does

1. Runs the full validation, and stops if anything fails.
2. Refuses to run with uncommitted work outside `CHANGELOG.md`, so the release
   commit is only ever the version bump.
3. Bumps `version` in `plugin.json`.
4. Moves your `## [Unreleased]` notes under the new version and dates them.
5. Commits `release: lsg vX.Y.Z` and tags `vX.Y.Z`.
6. Prints the push command. Pushing stays a deliberate step — it is the moment
   the work reaches the client.

## Where clients pull from

The default branch, `main`. Work on a branch if you like, but nothing reaches a
client until it lands on `main`.

Tags are for your own history — knowing which commit a client is on when they
report something. Clients resolve versions from `plugin.json`, not from tags.

## Checking it landed

```bash
./scripts/validate.sh                                   # before pushing
git show main:.claude-plugin/plugin.json | grep version # after pushing
```

Or install it as a client would, on a machine that has never had it, and confirm
the version in `/plugin` matches what you released.
