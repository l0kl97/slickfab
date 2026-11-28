# Autopilot setup

The autopilot is built but not yet live (see `docs/operating-modes.md`, section "Autopilot"). This page describes how to set it up: the commands, the factory configuration with every field, and where the dispatcher keeps its state. It needs [Herdr](https://herdr.dev/), `gh` signed in, and a Linear API key.

## Commands

```
runtime/herdr/slickfab-dispatch tick  [--dry-run] [--config <factory.json>]
runtime/herdr/slickfab-dispatch watch [--dry-run] [--interval <sec>] [--config <factory.json>]
```

- **tick:** takes the lock file, reads everything (Herdr terminals, the Linear issues of each enabled project, GitHub), asks `decide()` and carries out every action. Every planned action appears as `PLAN {json}` on stdout and in the log. `--dry-run` stops after the plans: no call that changes Linear, Herdr, Git or GitHub, no bookkeeping.
- **watch:** a tick at start, after every Herdr event of the dispatcher's terminals (events within 2 s are merged) and at the latest every `--interval` seconds (default 300).
- **Exit codes:** 0 ok · 1 read error, nothing carried out · 2 wrong call or configuration, nothing done · 3 single actions failed (their ticket gets `slickfab:needs-human`) · 75 another tick holds the lock file.

Try it with `--dry-run` first and read the plans before you let it act.

## Factory configuration

The factory configuration lives privately with the operator, never in a repo: `~/.config/slickfab/factory.json` (another path: `--config` or the environment variable `SLICKFAB_FACTORY`). The Linear API key is never in it, only the path to the key file.

Example without real values:

```json
{
  "assignee": "dispatch-user@example.com",
  "linear_key_file": "~/.config/slickfab/linear-key",
  "state_dir": "~/.local/state/slickfab",
  "worktree_root": "~/.herdr/worktrees",
  "timeout": 30,
  "pr_comment_authors": ["github-login"],
  "projects": {
    "example": {
      "enabled": false,
      "auto_merge": false,
      "max_parallel": 3,
      "linear_project": "Example",
      "repo": "~/code/example",
      "github": "owner/example",
      "github_ci": "use",
      "space": "-"
    }
  }
}
```

### Top-level fields

| Field | Required | Meaning |
|---|---|---|
| `assignee` | yes | Email of the Linear user the dispatcher works as. Tickets assigned to it are its work; its comments count as the dispatcher's own. |
| `linear_key_file` | yes | Path to the file holding the Linear API key. The key itself never goes into this configuration. |
| `state_dir` | yes | Folder for lock file, log and bookkeeping (see below). Never inside a repo. |
| `projects` | yes | The projects, by name (letters, digits, `.` `_` `:` `-`). Must not be empty. |
| `worktree_root` | no | Root of all worktrees, default `~/.herdr/worktrees`. Always passed as `--root` to `slickfab-worktree`; worktrees live under `<worktree_root>/<repo folder name>/<name>`. |
| `timeout` | no | Seconds per external call, more than 0 and at most 600, default 30. |
| `pr_comment_authors` | no | GitHub logins whose pull request comments the dispatcher takes into account, default `[]` (none). Only from here, never from ticket data: a comment is no credential. |
| `linear_api` | no | Linear API address; only `https://`, for tests also `http://127.0.0.1` or `http://localhost`. |

### Fields per project

| Field | Required | Meaning |
|---|---|---|
| `enabled` | yes | `true` or `false`, no default. Only enabled projects are touched; for disabled ones the other fields are not checked. |
| `linear_project` | if enabled | Name of the Linear project that holds specs and tickets. |
| `repo` | if enabled | Existing folder: the main checkout of the repo. |
| `github` | if enabled | GitHub repo as `owner/name`. |
| `auto_merge` | no | `true` or `false`, default `false`. Even with `true`, only a size `S` ticket whose review passed without concerns is merged automatically; `door:one-way`, sensitive paths or a ticket that was already back with you always wait for you. |
| `max_parallel` | no | How many roles run at the same time in this project, a number from 1, default 3. |
| `space` | no | Herdr space ID, or `-` for no space (default `-`). |
| `github_ci` | no | `use` (default: GitHub checks count) or `ignore`. |

**`github_ci: "ignore"`.** GitHub checks then count as absent: for the main branch only the local post-merge check counts, for pull requests only the review. It is meant for repos whose Actions do not run, for example because the free-tier quota is used up. Caution: `ignore` also switches off the server-side checks as a brake, such as the secret scan (gitleaks) and the dependency audit from `.github/workflows/security.yml`. A red finding there then holds up neither the main branch nor a pull request; the only remaining brake is the local pre-push hook (slickrails).

If a field is missing or wrong, a tick does nothing, names every wrong field and ends with exit code 2.

## Check commands

The baseline of a new worktree and the post-merge check of the main branch both run through `runtime/herdr/slickfab-worktree`. It takes the check commands `CHECK_TYPECHECK` and `CHECK_TEST` from the repo's `.slickrails/config.sh` (see `docs/project-config.md`). A red post-merge check makes the dispatcher start a debugger.

## State

Everything the dispatcher keeps lives in `state_dir`, never in a repo:

- `dispatch.lock`: only one tick at a time.
- `dispatch.log`: every plan and every action.
- `bookkeeping.json`: per project the last checked and debugged commit of the main branch, when the last retro ran, and which specs are verified.

Linear stays the single source of truth for plan and ticket state; the bookkeeping only remembers what Linear cannot hold.
