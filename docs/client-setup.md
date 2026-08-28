# Installing the Lark Solutions Group plugin

Send this page to anyone at LSG who needs the skills. It takes about a minute.

## Before you start

The plugin lives in a **private** repository, so Claude Code has to be able to
reach it as you:

- Your GitHub account needs read access to
  `Clad-Forge/CF_lark-solutions-group-plugin`. Ask Clad Forge if you are not
  sure whether you have it.
- Git on your machine needs to be signed in to that account. The simplest check
  is to run this in a terminal — if it completes without asking for a password,
  you are set:

  ```bash
  git ls-remote https://github.com/Clad-Forge/CF_lark-solutions-group-plugin
  ```

  If it fails, install the [GitHub CLI](https://cli.github.com) and run
  `gh auth login`, which sets up the credentials Claude Code then reuses.

## Install

In Claude Code, run these two commands:

```
/plugin marketplace add Clad-Forge/CF_lark-solutions-group-plugin
/plugin install lsg@lark-solutions-group
```

Restart Claude Code when it asks. That is the whole install — you only ever do
it once.

## Using the skills

Type `/` and look for the entries prefixed `lsg:`, or just describe what you
want in your own words — Claude picks the right skill on its own when your
request matches one.

```
/lsg:some-skill
```

Run `/plugin` at any time to see what is installed.

## Getting updates

Clad Forge publishes new and improved skills to the same repository. To pull
them in:

```
/plugin marketplace update lark-solutions-group
/plugin update lsg@lark-solutions-group
```

Restart Claude Code afterwards.

Claude Code also refreshes marketplaces in the background, so you may find
updates have already arrived. Running the two commands above is the reliable
way to get them now — worth doing if Clad Forge has told you something shipped.

## If something goes wrong

| What you see | What it usually means |
| --- | --- |
| `marketplace add` fails with a permission or authentication error | Your GitHub account cannot read the repository, or git is not signed in. Work through **Before you start** above. |
| The `lsg:` commands are missing after installing | Claude Code needs a restart. |
| A skill behaves like an older version | Run the two update commands above, then restart. |
| A skill stops partway and says something is missing | That is deliberate — the skills stop rather than guess. Send the message to Clad Forge. |

Anything else, contact Clad Forge at cort@cladforge.com.
