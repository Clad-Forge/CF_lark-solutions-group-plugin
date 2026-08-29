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

Two ways to do this. **Option A is quicker** — pick Option B if you would
rather click than type, or if your Claude Code does not offer `/plugin`.

You only ever do this once, either way.

### Option A — two commands

In Claude Code, run:

```
/plugin marketplace add Clad-Forge/CF_lark-solutions-group-plugin
/plugin install lsg@lark-solutions-group
```

Restart Claude Code when it asks. Done.

Both commands are needed. The first one only registers the catalogue — it
installs nothing on its own, so if you stop there it will look like nothing
happened.

### Option B — a settings file, then the plugin panel

This does the same thing without typing commands into Claude. Create one file,
then everything after is clicking.

**1. Create this file:**

| | |
| --- | --- |
| Windows | `C:\Users\<your-name>\.claude\settings.json` |
| Mac | `~/.claude/settings.json` |

with exactly this in it:

```json
{
  "extraKnownMarketplaces": {
    "lark-solutions-group": {
      "source": {
        "source": "github",
        "repo": "Clad-Forge/CF_lark-solutions-group-plugin"
      }
    }
  }
}
```

If the file already exists, add the `extraKnownMarketplaces` block alongside
what is already in there rather than replacing the file.

> **On Windows, do not use Notepad unless you are careful.** It saves as
> `settings.json.txt` by default, and a file with that name does nothing. In the
> Save dialog set **Save as type** to **All Files**, or use VS Code.

**2. Restart Claude.**

**3. Install it from the panel:** click the **+** button next to the prompt box
→ **Plugins** → **Add plugin** → choose **Lark Solutions Group** → **Install**.

The same **+** → **Plugins** → **Manage plugins** is where you turn it off or
remove it later.

The settings file only makes the plugin *available* to install — it does not
install it for you, so step 3 is not optional.

## Using the skills

Type `/` and look for the entries prefixed `lsg:`, or just describe what you
want in your own words — Claude picks the right skill on its own when your
request matches one.

```
/lsg:some-skill
```

Run `/plugin` at any time to see what is installed.

## Getting updates

Clad Forge publishes new and improved skills to the same repository. However you
installed it, both routes below work — use whichever you prefer.

**From the panel:** **+** → **Plugins** → open **Lark Solutions Group** → click
**Update**.

**From the command line:**

```
/plugin marketplace update lark-solutions-group
/plugin update lsg@lark-solutions-group
```

Restart Claude afterwards either way.

Claude also refreshes in the background, so an update may already have arrived
on its own. The steps above are the way to get one *now* — worth doing when Clad
Forge tells you something has shipped.

You can check which version you are on in the plugin panel; it is shown next to
the name.

## If something goes wrong

| What you see | What it usually means |
| --- | --- |
| Nothing appears after `/plugin marketplace add` | Expected — that command only registers the catalogue. Run the `/plugin install` line too. |
| `/plugin install` says the plugin was not found | Check the name. It is `lsg@lark-solutions-group` — not the repository name, and not the marketplace name on its own. |
| Anything fails with a permission or authentication error | Your GitHub account cannot read the repository, or git is not signed in. Work through **Before you start** above. |
| Option B: the plugin panel does not list it | The settings file is not being read. Check the name is exactly `settings.json` and not `settings.json.txt`, that it is in `.claude` in your user folder, and that Claude has been restarted. |
| The `lsg:` commands are missing after installing | Claude needs a restart. |
| A skill behaves like an older version | Update it as above, then restart. |
| A skill stops partway and says something is missing | That is deliberate — the skills stop rather than guess. Send the message to Clad Forge. |

Anything else, contact Clad Forge at cort@cladforge.com.
