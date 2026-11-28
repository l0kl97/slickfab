# Operating modes and setup

slickfab is a process of 13 steps. You can run it in three ways, and it is always the same steps: a step is exactly one `skills/<step>/SKILL.md`. The agent roles and the Herdr templates are only wrappers around them.

## Your first step in five minutes

1. Install the plugin: `claude plugin marketplace add <path-to-repo>`, then `claude plugin install slickfab@slickfab` (details in the README, "Install"). To try it without installing, use `claude --plugin-dir <path-to-slickfab>`.
2. Start Claude Code in your project and enter `/slickfab:fab`. fab tells you where you stand, what is missing from the setup and which step comes next. In a repo without prior work, that is `/slickfab:grill`.
3. `/slickfab:grill <your plan>` does not answer questions for you, it asks them: in rounds, with a recommendation, until no decision is left open.

`grill` needs no tracker. From `spec` on you need the project configuration (below).

## Setup in a new repo

| What | What for | How |
|---|---|---|
| `.slickfab/config` | tracker (team, project) and, without slickrails, check commands | Create the file in the repo root; format and keys in `docs/project-config.md`. `/slickfab:fab` shows a proposal with the values it finds. |
| Linear tools | read and create specs and tickets | Sign in to the Linear connector in Claude Code. The steps load it via tool search. |
| `gh`, signed in, repo on GitHub | open pull requests (`implement`) and read them (`review`, `fab`) | `gh auth login` |
| slickrails (recommended) | brakes: hooks, stop gate, AI review on push | `slickrails init` in the repo. The check commands then come from `.slickrails/config.sh`. |

If any of this is missing, no step stops without saying so: each one names the missing file or access and writes no substitute file into the repo. Linear stays the single source of truth about plan and state. There is no plan, ledger or state file in the repo; fab does not create one either.

The project you work in must not lie inside the plugin folder, whether installed or loaded with `--plugin-dir`. Claude Code protects files in the plugin folder as a "sensitive file", and then no step may write there (found in a trial run). For work on slickfab itself this means: if it is installed from the checkout, changes happen in a worktree outside of it (`git worktree add` or `runtime/herdr/slickfab-worktree add`), and the merged state reaches the checkout via `git pull`.

## The steps

| Step | What for | Context |
|---|---|---|
| `/slickfab:fab` | signpost: where am I, what comes next | any |
| `/slickfab:grill` | settle open decisions in rounds | conversation with you |
| `/slickfab:spec` | specification from the settled conversation, in the tracker | same conversation as grill |
| `/slickfab:prototype` | settle questions that cannot be answered by asking | same conversation, then spec |
| `/slickfab:challenge` | fresh look at spec and split | fresh session |
| `/slickfab:tickets` | cut the spec into thin, vertical tickets | fresh session |
| `/slickfab:implement` | one ticket via TDD up to the pull request | fresh session per ticket |
| `/slickfab:review` | check a pull request on two axes | fresh session |
| `/slickfab:debug` | find a bug with a red loop | fresh session |
| `/slickfab:verify` | check the spec's goal across all tickets | fresh session |
| `/slickfab:retro` | turn recurring mistakes into rules | fresh session |
| `/slickfab:handoff` | handoff before the context is full | at the end of the running session |
| `/slickfab:docs-lookup` | version-exact library docs | from within the running step |

The usual path: `grill` → `spec` → `challenge` → `tickets` → you set tickets to `Todo` → per ticket `implement` → `review` → you merge → after the last ticket `verify` → `retro` → you set the spec to `Done`. Every step names the next one at its end. If you are unsure, ask `/slickfab:fab`.

Checking steps run in a fresh session, so that the checker does not know how the artifact came about. If the running session gets long (warning from context-guard, at about two thirds of the context), write a handoff to the ticket with `/slickfab:handoff` and continue fresh.

## Manual

You call the steps yourself, one per slash command, in your session or in a new one. This is the mode for every Claude Code user, without Herdr. You see every step, answer its questions and approve what it wants to create.

## Assisted

One session, and the steps run as fresh subagents. The plugin brings seven roles: `slickfab:planner` (spec and tickets), `slickfab:challenger`, `slickfab:implementer`, `slickfab:reviewer`, `slickfab:debugger`, `slickfab:verifier` and `slickfab:retro`. Each role already has its step in context when it starts and ends with the marker line `SLICKFAB-STATUS: …`.

This is how you start them, in your session with the plugin loaded, in your own words:

> Start the agent slickfab:implementer with the task "EX-12". When it has pushed the branch, start slickfab:reviewer with the PR and the ticket. Give the reviewer nothing from the implementer's report.

What you give a role is only its input (ticket, PR, spec issue). A role cannot ask you: where the step would ask, it ends with `NEEDS_CONTEXT` or `BLOCKED` and names what is missing. Then you decide in the main session and start the role again. `grill` never runs as a role, because it needs you.

**How robust the roles are.** Each of the seven roles has at least two pressure scenarios under `tests/pressure/`: situations that push towards a shortcut (gate red and time pressure, a test in the way, "whatever, you do it" …), with "held" defined in advance. Each scenario ran with the new role and, as a control, with the old studio template or without instructions: new 14 of 14 held, control 2 of 14. Grading is by hand; `tests/check_pressure.py` only checks the filing (`docs/features/pressure-szenarien.md`, German).

**Guards.** The plugin brings three hooks (`hooks/hooks.json`):

- `role_bash_guard.py`: For `slickfab:reviewer`, `slickfab:verifier` and `slickfab:retro` it allows only an allowlist of Bash commands (read, test, `git`/`gh` without writing). Their tool limit (`disallowedTools`) would otherwise be void with free Bash (`docs/features/rollen-bash-waechter.md`, German).
- `docs_lookup_guard.py`: In the docs reader `slickfab:docs-reader` only the call of `lookup.py` is allowed (`docs/features/docs-lookup.md`, German).
- `context_guard.py`: warns a role from 65 % context on and demands the handoff from 80 % on. It acts only in Herdr terminals with a role label and a readable status line; in a normal session it stays silent (`docs/features/context-guard.md`, German).

Both Bash guards start through a shared launcher. Outside their roles they do not interfere; inside the role they refuse when in doubt.

## Autopilot

**Not yet live, but built.** A dispatcher starts the roles in parallel in Herdr terminals, Linear is the state machine, and you only step in at gates (objections, split, merge, `door:one-way`, `slickfab:needs-human`). At the switch-over it ran as a dry run against the real Linear. That turned up bugs that have since been fixed: red GitHub CI without running Actions, `space: "-"`, and Herdr templates with invalid frontmatter. It only goes live after the pilot in slickrails. Until then you run slickfab in the Manual or Assisted mode.

What exists:

- `runtime/herdr/slickfab-dispatch tick|watch [--dry-run]`: reads Linear, Herdr and GitHub, asks `decide()` and carries out the actions; `--dry-run` only shows the plans.
- `runtime/herdr/slickfab_dispatch.py`: the decision logic `decide()`.
- `runtime/herdr/slickfab-worktree add|review|rm`: ready-to-start worktrees with a baseline check.
- `runtime/herdr/slickfab-run`: starts a role as a Herdr session. `runtime/herdr/gen-templates` generates the Herdr templates from `agents/`.

**Factory configuration.** It lives privately with the operator (`~/.config/slickfab/factory.json`, never in the repo) and names per project whether the autopilot may touch it (`enabled`), the Linear project, the repo and the GitHub repo. Optional per project: `auto_merge` (default off), `max_parallel` (default 3), `space` (Herdr space or `-`) and `github_ci` (`use` or `ignore`; `ignore` also switches off server-side checks such as the secret scan as a brake). Setup, every field and an example: `docs/autopilot.md`.

## Working with slickrails

slickrails are the brakes, slickfab is the accelerator. If the repo has `.slickrails/`:

- The check commands come from `.slickrails/config.sh`, not from `.slickfab/config`.
- `implement` bypasses no hook. A red stop hook or a finding of the AI review on push means: not done.
- `review` first reads what slickrails has already reported (status checks, AI review) and does not report it twice.
- `retro` turns mechanical mistakes into proposals for slickrails checks and judgement calls into entries in `.slickrails/review-learnings.md`, always as a proposal for you.

Without slickrails every step works, but the brakes are missing: then only the check commands from `.slickfab/config` apply.
