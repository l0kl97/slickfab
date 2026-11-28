---
name: fab
description: Use when it is unclear where a piece of work stands in the slickfab process and which step comes next, or when someone says “where am I?”, “what now?” or “fab”.
argument-hint: "[spec issue | ticket | topic]"
---

<!-- regel:einleitung -->
# fab: signpost

Goal: You say where the work stands, which step comes next, and whether it runs in the same conversation or in a fresh session. You read the state from the tracker and the repo, never from memory and never from a state file.

You only read. You write no file, no comment, no label and no status, not even `.slickfab/config`. What is missing, you name; the human creates it.

Answer in the user's language. Tracker rules and project configuration are below in the section `Vertrag`.
<!-- /regel:einleitung -->

## Wann

<!-- regel:wann -->
- At the start, when nothing exists yet: fab names the first step.
- Between two steps or after a break, when it is unclear what comes next.
- Not as a substitute for a step: fab does not run a step, it names it.
<!-- /regel:wann -->

## Ablauf

<!-- regel:repo-lesen -->
### 1. Read the repo

Read-only commands only, each with its result recorded:

- `git rev-parse --show-toplevel`, `git branch --show-current`, `git status --short`, `git remote -v`.
- Whether `.slickfab/config` exists and has the required values (format in the contract), and whether `.slickrails/config.sh` exists. You read both as text.
- Open pull requests with `gh pr list --state open --json number,title,headRefName,url`. For every PR that names a ticket (ticket ID in the title or branch name), you read with `gh pr view <PR> --json commits,comments,reviews` the last `SLICKFAB-VERDICT:` line with its time, and whether commits came after it (committer date).

If a command fails (not a Git repo, `gh` missing or not logged in, no remote), you record that as a gap with the error message and carry on with the rest. What you could not read counts as unknown, not as empty.
<!-- /regel:repo-lesen -->

<!-- regel:tracker-lesen -->
### 2. Read the tracker

Only if `.slickfab/config` is complete and the tracker is reachable (the session's Linear tools, in Claude Code loaded via tool search `+linear`). If a spec issue or ticket is given as argument, you read that; otherwise, in the project from the configuration, the open issues titled `Spec: …` and their sub-issues:

- status of the spec issue, status of every ticket, and labels (`slickfab:needs-human`, `slickfab:rework`, `slickfab:replan`, `slickfab:ready`),
- “blocked by” relations,
- the comments from `challenge`, `verify` (with status `bestanden` (passed), `Lücken gefunden` (gaps found) or `Mensch nötig` (human needed)), handoffs (`handoff`) and revisions of the spec (first line `## Spec überarbeitet`), each with its time and its last marker line.

If the configuration is missing or the tracker is unreachable, you do not read it and guess nothing about it: no spec, no ticket and no status you have not seen. You then decide only with what the repo and the conversation show, and name under “Missing for setup” what is missing. You do not abort.
<!-- /regel:tracker-lesen -->

<!-- regel:entscheiden -->
### 3. Determine the next step

Go through the table from top to bottom; the first row that applies counts. Work close to the merge comes before new work. If several specs or tickets match the same row, you name all of them and recommend the oldest. A spec in `Done` or `Canceled` is finished: it does not count as an open spec, even if it is given as argument.

| # | If (seen, not assumed) | Then |
|---|---|---|
| 1 | The argument or the human describes a bug with an unknown cause | `/slickfab:debug <bug>` |
| 2 | A ticket has `slickfab:needs-human`, or the last slickfab comment on it ends with `BLOCKED` | no step: the human decides; name what is open, with link |
| 3 | Open PR for a ticket without `SLICKFAB-VERDICT` | `/slickfab:review <PR>` |
| 4 | Open PR, last verdict `REWORK` or `MERGE`, new commits after it | `/slickfab:review Re-Review <PR>` |
| 5 | Open PR, last verdict `REWORK`, no commits after it | `/slickfab:implement <ticket>` (rework) |
| 6 | Open PR, last verdict `REPLAN`, or ticket with `slickfab:replan` | `/slickfab:tickets <spec issue>` |
| 7 | Open PR, last verdict `MERGE`, no commits after it | no step: the human merges |
| 8 | Ticket in `In Review` without an open PR | no step: the human checks whether the PR is merged (then ticket to `Done`) or missing; name the ticket and the last PR with link |
| 9 | Ticket in `In Progress` without an open PR | `/slickfab:implement <ticket>` (reads a handoff on the ticket first) |
| 10 | Ticket in `Todo`, no open blocker | `/slickfab:implement <ticket>` |
| 11 | Ticket in `Todo`, its blocker is still in `Backlog` | no step: the human approves the blocker (`Todo`); name both tickets |
| 12 | Spec issue still open, all tickets closed, at least one `Done`, no `verify` result after the last merge | `/slickfab:verify <spec issue>` |
| 13 | Spec issue still open, all tickets closed, at least one `Done`, last `verify` result `bestanden` (passed) | `/slickfab:retro <spec issue>`; after that the human sets the spec to `Done` (retro writes nothing to the tracker, that is the end), with the next piece of work `/slickfab:grill` |
| 14 | Spec issue still open, all tickets closed, at least one `Done`, last `verify` result `Lücken gefunden` (gaps found) | `/slickfab:verify <spec issue>`: proposes the fix tickets and creates them after the human's yes |
| 15 | Spec issue still open, all tickets closed, at least one `Done`, last `verify` result `Mensch nötig` (human needed) | no step: the human checks the points from the `verify` comment, then `/slickfab:verify <spec issue>` |
| 16 | Spec has tickets in `Backlog`, none in `Todo`, `In Progress` or `In Review` | no step: the human approves the next ticket (`Todo`) |
| 17 | All tickets of the spec `Canceled` or `Duplicate` | no step: the human decides whether the spec is split again (`/slickfab:tickets <spec issue>`) or ends; status `NEEDS_CONTEXT` |
| 18 | Spec without tickets and without a `challenge` comment, or last `challenge` verdict `nicht bauen` and after it a comment `## Spec überarbeitet` (later than the last `challenge` comment) | `/slickfab:challenge <spec issue>` |
| 19 | Spec without tickets, last `challenge` verdict `nicht bauen`, no comment `## Spec überarbeitet` after it | no step: the human decides whether the work ends (spec to `Canceled`) or whether they change the spec with `/slickfab:spec <spec issue>` and have it checked again; name the `challenge` comment with link; status `NEEDS_CONTEXT` |
| 20 | Spec without tickets, `challenge` comment present, last verdict `bauen` or `kleiner bauen` | `/slickfab:tickets <spec issue>` |
| 21 | This conversation contains a confirmed `Ergebnis grill` | `/slickfab:spec` |
| 22 | No open spec seen and nothing from above | `/slickfab:grill [topic]` |
| 23 | An open spec seen, but no row fits | no command: name the state with links and what you cannot place; status `NEEDS_CONTEXT` |

“Closed” means `Done`, `Canceled` or `Duplicate` (status flow in the tracker contract). “New commits after it” means: a commit of the PR has a committer date after the time of the last verdict. This also applies after a rebase, because no review has seen the new state yet.

Rows that need the tracker you do not check without the tracker; they then count as not applicable, and you say so. A PR whose ticket you cannot read without the tracker still counts for rows 3 to 7 if its title or branch names a ticket ID. If you reach row 22 without the tracker, you add that open specs are unknown.
<!-- /regel:entscheiden -->

<!-- regel:kontext -->
### 4. Fresh context or continue

- **In the same conversation:** `/slickfab:spec` directly after `grill` or `prototype`, because spec reads the conversation; `docs-lookup` from within the step that has the question.
- **Fresh session:** all other steps. Checking steps (`challenge`, `review`, `verify`) must not know how the artifact came about; `implement`, `debug`, `tickets` and `retro` read everything they need from the tracker and the repo.
- **Context full:** If this conversation is already long (warning from context-guard, about two thirds of the context or more than roughly 150k tokens), you recommend `/slickfab:handoff <ticket>` before the next step if work on a ticket is in progress, and the next step in a fresh session.
<!-- /regel:kontext -->

<!-- regel:schritte -->
### The steps

| Step | What for | Context |
|---|---|---|
| `fab` | signpost: where am I, what comes next | any |
| `grill` | clarify open decisions in rounds | conversation with the human |
| `spec` | specification from the clarified conversation | same conversation as grill |
| `prototype` | clarify questions that cannot be settled by asking | same conversation, then spec |
| `challenge` | fresh eye on spec and split | fresh session |
| `tickets` | cut the spec into thin, vertical tickets | fresh session |
| `implement` | one ticket via TDD up to the PR | fresh session per ticket |
| `review` | check a PR on two axes | fresh session |
| `debug` | find bugs with a red loop | fresh session |
| `verify` | check the spec's goal across all tickets | fresh session |
| `retro` | turn recurring mistakes into rules | fresh session |
| `handoff` | handover before the context is full | at the end of the running session |
| `docs-lookup` | library docs for the exact version | from within the running step |
<!-- /regel:schritte -->

## Vertrag

<!-- regel:vertrag-quelle -->
Verbatim from `tracker/linear.md` and `docs/projektkonfiguration.md` of the slickfab plugin. It is here so that you do not have to read anything outside the project; it applies exactly as written. fab only reads: you do not offer to create the configuration, you show its content.
<!-- /regel:vertrag-quelle -->

### Project configuration: format

<!-- vertrag:config-format -->
`.slickfab/config` in the repo root: one line per value, `KEY="value"`. Blank lines and lines starting with `#` do not count.

```sh
# slickfab: project configuration
TRACKER="linear"
TRACKER_TEAM="Example"
TRACKER_PROJECT="Example"
# Check commands, only without slickrails (otherwise the ones from .slickrails/config.sh apply)
CHECK_TYPECHECK="npm run typecheck"
CHECK_TEST="npm test"
CHECK_LINT=""
```

| Key | Required | Meaning |
|---|---|---|
| `TRACKER=` | yes | Which tracker contract applies. Currently only `linear`. |
| `TRACKER_TEAM=` | yes | Name or key of the Linear team. |
| `TRACKER_PROJECT=` | yes | Name of the Linear project that holds specs and tickets. |
| `CHECK_TYPECHECK=` | no | Type check; empty = does not exist. |
| `CHECK_TEST=` | yes, without slickrails | All tests; empty = does not exist (then every step that is supposed to check says that it cannot). |
| `CHECK_LINT=` | no | Lint; empty = does not exist. |

The file is read as text, not executed as a shell script (no `source`), so that a configuration cannot inject code.

Answer in the user's language.
<!-- /vertrag:config-format -->

### Tracker: marker

<!-- vertrag:marker -->
Every comment that a slickfab step or role writes, and every report to a caller, ends with the marker block, with no text after it:

- Last line, always: `SLICKFAB-STATUS: DONE|DONE_WITH_CONCERNS|BLOCKED|NEEDS_CONTEXT`
- Second-to-last line, only for the reviewer: `SLICKFAB-VERDICT: MERGE|REWORK|REPLAN`

All other steps and roles write only the STATUS line. Each line holds exactly one value.

| Value | Meaning |
|---|---|
| `DONE` | task fulfilled, nothing open |
| `DONE_WITH_CONCERNS` | fulfilled, but with stated concerns |
| `BLOCKED` | cannot continue; the reason is stated above |
| `NEEDS_CONTEXT` | information or context is missing; what is missing is stated above |

Example (every step):

```
SLICKFAB-STATUS: BLOCKED
```

Example (reviewer):

```
SLICKFAB-VERDICT: REWORK
SLICKFAB-STATUS: DONE
```

Answer in the user's language.
<!-- /vertrag:marker -->

## Ergebnis

<!-- regel:ergebnis -->
```
## Ergebnis fab

**State:** <one to three sentences, each with a source: issue link, PR link or command>
**Read:** repo <yes|no: reason>, pull requests <yes|no: reason>, tracker <yes|no: reason>
**Missing for setup:** <e.g. `.slickfab/config` with TRACKER, TRACKER_TEAM, TRACKER_PROJECT (proposal below), Linear tools, `gh` login> or “nothing”

Nächster Schritt: `/slickfab:<step> <argument>` in <this conversation|a fresh session>, because <row of the table>

SLICKFAB-STATUS: <DONE|DONE_WITH_CONCERNS|NEEDS_CONTEXT>
```

`DONE` if everything could be read; `DONE_WITH_CONCERNS` if something was unreadable and the recommendation therefore rests only on the rest; `NEEDS_CONTEXT` if two paths fit equally well and only the human can choose (then name both) or row 17, 19 or 23 applies. If the next move is a decision by the human (rows 2, 7, 8, 11, 15, 16, 17, 19), it stands in the line `Nächster Schritt` instead of a command; for row 23, that line states what you cannot place. The line is never missing.
<!-- /regel:ergebnis -->

## Nächster Schritt

<!-- regel:naechster-schritt -->
The step the result names, in the context it names. After that, `/slickfab:fab` again if it is unclear how to continue.
<!-- /regel:naechster-schritt -->
