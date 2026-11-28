---
name: retro
description: Use when recurring mistakes from the last pull requests, reviews or sessions should become rules, for example after a feature or every tenth merge, or when someone says “do a retro”.
argument-hint: "[spec issue | PR range | session]"
---

<!-- regel:einleitung -->
# retro: turn recurring mistakes into rules

Goal: A mistake that has happened twice should not slip through a third time. You find recurring mistakes and propose for each the cheapest brake that catches it in future.

Answer in the user's language. Tracker rules and project configuration are below in the section “Vertrag”.
<!-- /regel:einleitung -->

## Wann

<!-- regel:wann -->
- After `/slickfab:verify` for a feature, after roughly every tenth merge, or when a mistake shows up that has happened before.
- Not to fix a single bug; for that there is `/slickfab:debug`.
<!-- /regel:wann -->

## Ablauf

<!-- regel:ablauf -->
You propose, you do not apply. You change no file: no checks, no hooks, no CI workflows, no linter configuration, no rule files (`.slickrails/rules.md`, `.slickrails/review-learnings.md`, `CLAUDE.md`, `AGENTS.md`, coding standards), not even “just one entry”. Every brake that you propose changes what gets through in future; a human decides on that. Whatever they accept is built and checked like any other change, as a ticket or pull request.

### 1. Check the precondition

- Settle the time period: spec issue, range of pull requests or session (argument). If none is given: the repo's last ten merged pull requests.
- Read `.slickfab/config`. retro reads the tracker (Linear through the session's Linear tools, via tool search `+linear`) only to find review comments and labels; retro writes nothing to the tracker. If the tracker is unreachable, that is no reason to abort: You keep working with Git and pull requests and name the error message and what you are missing because of it.
- Read which brakes already exist: `.slickrails/config.sh`, `.slickrails/rules.md`, `.slickrails/review-learnings.md`, hooks, CI workflows, linter configuration, `CLAUDE.md`/`AGENTS.md`.

### 2. Collect mistakes

Sources, the ones that went wrong first:

- review comments with findings `Critical` or `Required` and verdicts `REWORK` or `REPLAN` (on the PR and on the ticket),
- tickets with `slickfab:rework`, `slickfab:needs-human` or `slickfab:replan`, fix tickets from `/slickfab:verify`,
- bugfix commits and reverts in the time period, red CI runs,
- entries that humans reported afterwards.

One line per mistake: what happened, where (PR, commit, `file:line`), who or what found it, who should have found it earlier. Combine identical causes. A mistake is recurring from its second occurrence; one-off mistakes you name only if they were severe (data loss, security hole, production broken).

### 3. Classify: check or review lesson

For every recurring mistake exactly one classification:

- **mechanical:** a fixed pattern that a machine can recognize (forbidden call, import form, file location, missing test for a file, new `.skip`, lowered threshold). This becomes a proposal for a check: a rule in the repo's linter, a step in an existing hook or a CI job, whichever is cheapest in the repo. If the check already exists but is not wired in or silently broken, exactly that is the proposal. If the repo has no automatic check at all (no hook, no CI job with tests), that is a finding in itself.
- **judgement:** needs judgement (consistency across files, the right abstraction, whether a test checks the right thing). This becomes a proposal for an entry in `.slickrails/review-learnings.md` (one dated line, short and concrete, as the file prescribes) or, without slickrails, in the repo's review rules.

When in doubt, mechanical: A check that always runs beats a rule that someone has to remember. `CLAUDE.md` and `AGENTS.md` get at most a reference, no new rules; they sit in every agent's context and get more expensive with every line.

If a proposal concerns slickrails itself (a check that every repo would need), write it as text for an issue or a pull request to slickrails; you do not change slickrails.

### 4. Present

Show the proposals, the most severe mistake first. Per proposal: the mistake with evidence (at least two places for recurring ones), the classification, the exact change as text (the check as a code proposal, the entry as a finished line) and where it belongs. Ask which ones the human accepts. If they accept some, you offer to create tickets for them with `/slickfab:tickets` or to build a pull request with `/slickfab:implement`; you do not write them into the files yourself.
<!-- /regel:ablauf -->

## Vertrag

<!-- regel:vertrag-quelle -->
Verbatim from `tracker/linear.md` and `docs/project-config.md` of the slickfab plugin. It is here so that you do not have to read anything outside the project; it applies exactly as written.
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

### Project configuration: check commands with slickrails

<!-- vertrag:config-slickrails -->
If the repo has `.slickrails/config.sh`, the check commands come from there: all non-empty `CHECK_*` values, the same way slickrails uses them in its hooks. `CHECK_*` entries in `.slickfab/config` are then not used; if they hold different values, the step names the contradiction once and follows slickrails. `.slickrails/config.sh` is also read only as text.

Answer in the user's language.
<!-- /vertrag:config-slickrails -->

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
## Ergebnis retro

**Time period:** <spec, PR range or session> · **Mistakes reviewed:** <n>, of which recurring: <n>

1. <mistake> — <n>× (<evidence: PR, commit, file:line>)
   Classification: mechanical → proposal for a check in <hook, linter, CI job> | judgement → proposal for an entry in `.slickrails/review-learnings.md`
   Proposal: <code or finished line>

**For slickrails:** <text for an issue> (or “none”)
**Changed files:** none

Nächster Schritt: `/slickfab:grill` (new feature) | `/slickfab:tickets <spec>`

SLICKFAB-STATUS: DONE
```
<!-- /regel:ergebnis -->

## Nächster Schritt

<!-- regel:naechster-schritt -->
The human decides on every proposal. Whatever they accept is built like any change: as a ticket via `/slickfab:tickets` or directly with `/slickfab:implement`. After that, work continues with the next feature, starting with `/slickfab:grill`.
<!-- /regel:naechster-schritt -->
