---
name: debug
description: Use when something is broken, throws an error, calculates wrongly or is slow and the cause is unknown, or when someone says “debug this”.
argument-hint: "<bug description or ticket>"
---

<!-- regel:einleitung -->
# debug: find a bug with a red loop

Goal: Find the cause of a bug with evidence, fix it and pin it down with a regression test. Guessing is not allowed; every statement rests on a run.

Answer in the user's language. Project configuration and marker are below in the section “Vertrag”.
<!-- /regel:einleitung -->

## Wann

<!-- regel:wann -->
- When a behaviour is wrong and the cause is not obvious.
- When `/slickfab:implement` has stopped after three fix attempts at the same place.
<!-- /regel:wann -->

## Ablauf

<!-- regel:voraussetzung -->
### 1. Check the precondition

- You need the description of the bug: what happens, what should happen instead.
- A ticket is not needed. If there is one, you read it with all comments. If there is a ticket and the tracker is unreachable, the contract “access” applies: report and stop, no file as a substitute.
- Read `.slickfab/config` and, if present, `.slickrails/config.sh`, both only as text (rules in the contract). You take check commands only from `.slickrails/config.sh` or `.slickfab/config`; you do not guess any from `package.json`, `Makefile` or habit. If a check command is missing, you say which one, and that you cannot run it. The red command from step 2 is not a check command: You build it yourself, for exactly this bug.
<!-- /regel:voraussetzung -->

<!-- regel:rote-schleife -->
### 2. Build a red loop

This is the core of the step. Build a command that turns red on exactly this bug and green as soon as it is fixed. Possible forms, roughly in this order: a failing test at the place that reaches the bug; a `curl` against a running service; a CLI call with fixed input, compared with the expected output; a browser script; a replayed recorded call; a small throwaway harness around the affected path; for “sometimes wrong”, a loop over many inputs; for “used to work”, a `git bisect run` with this command.

The loop is done when you can name **one** command that you have already run once (show command and output, with secrets replaced by `<REDACTED>`), and that

- checks exactly the symptom that was reported, not “runs without errors”,
- gives the same verdict on every run (for intermittent bugs: a high, fixed hit rate),
- runs in seconds and needs no human.

Without a command that turns red on exactly this bug, no search for the cause and no fix. If you catch yourself reading code to build a theory before this command exists: back to the start of this section.

If you do not manage to get a red command, you stop: You name what you have tried and ask for what is missing. You do not suggest a fix. What may be missing: access to the environment where it happens; a recorded example (log, request, file); permission for temporary measurement points. Status `NEEDS_CONTEXT`. Before stopping, step 7 applies.

| Excuse | Reality |
|---|---|
| “The cause is obvious, I can see it in the code.” | Then the red command is built in two minutes and proves it. Without it, after the fix you do not know whether it works. |
| “I can't reproduce it, but this change does no harm.” | A fix without a red command is a guess. Report, don't guess. |
<!-- /regel:rote-schleife -->

<!-- regel:nachstellen-und-minimieren -->
### 3. Reproduce and minimize

Run the command and compare the output with the report: Is it the same bug, not a neighbouring one? Then shrink the case piece by piece (inputs, callers, configuration, data), running it again after every cut, until every remaining part is needed for it to stay red.
<!-- /regel:nachstellen-und-minimieren -->

<!-- regel:hypothesen -->
### 4. Hypotheses

Write down 3 to 5 hypotheses, ordered by likelihood, before you check one. Each must be falsifiable, in the form: “If <X> is the cause, then <change Y> makes the bug go away and <change Z> makes it worse.” If you cannot name the prediction, it is not a hypothesis. Show the list to the human, if they are there; they often know what has already been ruled out. Do not wait for them.

Keep two lists and only append to them: **Ruled out** (hypothesis, evidence) and **Evidence** (finding, command). That way you never check a hypothesis twice.
<!-- /regel:hypothesen -->

<!-- regel:messen -->
### 5. Measure

Check the hypotheses in order. Every measurement belongs to a prediction from step 4; you change one thing at a time. Preferably with a debugger or REPL; otherwise targeted output at the places that tell two hypotheses apart, never “log everything and search”.

At the start, choose a short tag of four characters, such as `[DEBUG-a4f2]`, below `[DEBUG-<tag>]`. Every measurement point carries the tag, without exception. Only that way will you find them all again at the end.

For performance bugs you first measure a baseline figure (timing, profiler, query plan) and compare afterwards; logs rarely help there.
<!-- /regel:messen -->

<!-- regel:regressionstest -->
### 6. Regression test and fix

Turn the minimized case into a test at a test seam that hits the bug the way it arises at the caller. Run it: It must be red, with the reported symptom (command and output). Then the fix, namely the smallest one that removes the proven cause. Run the test and the command from step 2: both green (command and output). The check commands from the configuration then run in full.

If there is no test seam that hits the bug the way it arises, that is a finding of its own: You do not write a shallow test that only pretends; you name which test seam is missing and why. The red command from step 2 then remains the proof.

If the fix fails three times, the cause has usually been misunderstood: back to step 4 with the new evidence, not a fourth attempt at the same place. You go back to step 4 at most once. If three fixes fail again after that, you stop and report `BLOCKED` with the hypotheses, evidence and attempts; then the human decides.

The fix is subject to the same limits as in `/slickfab:implement`:

- **Stop list:** If the cause or the fix touches one of these points: auth and permissions, destructive migrations, payments, deletions of data, deploys, secrets, anything a revert does not bring back, then you stop before the fix and report `BLOCKED` with cause, evidence and the fix you propose. It is only built with an approval on the ticket.
- **Existing tests:** no skipping, no deleted or loosened assertions, no lowered thresholds. If an existing test is in the way, you do not change it; you stop and report it (status `BLOCKED`), even if you are sure that it is wrong.
<!-- /regel:regressionstest -->

<!-- regel:aufraeumen -->
### 7. Clean up

- Remove every measurement point and check it with `grep -rn "DEBUG-<tag>" .` (with your tag). As long as the tag appears anywhere, you are not done.
- Delete throwaway harnesses and helper files that do not belong to the regression test.
- Run the command from step 2 against the original, not minimized case: green.

If you stop before step 7 (`NEEDS_CONTEXT`, `BLOCKED`), you still clean up: You delete measurement points and throwaway harnesses, also outside the repo, or you name in the result every path that remains, and why.
<!-- /regel:aufraeumen -->

<!-- regel:warum-nicht-gefangen -->
### 8. Why not caught

Answer two questions and write them into the result, into the commit and, if there is a ticket, as a comment there:

- **Why not caught:** Which check should have found the bug, and why did it not? (no test at that place, the test checked something else, case not considered, a mock hid it)
- **Recurrence guard:** What prevents a bug of this kind from coming back? The regression test only covers this case; name a check or rule for the whole kind and put it forward as a proposal (for `/slickfab:retro`), instead of building it in unasked.

Then you commit (the message names the confirmed hypothesis, so that the next person learns from it). If the bug belongs to a ticket that is being built right now, work continues there; otherwise you open a pull request against the main branch, do not merge.
<!-- /regel:warum-nicht-gefangen -->

## Vertrag

<!-- regel:vertrag-quelle -->
Verbatim from `tracker/linear.md` and `docs/projektkonfiguration.md` of the slickfab plugin. It is here so that you do not have to read anything outside the project; it applies exactly as written.
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

### Project configuration: when it is missing

<!-- vertrag:config-fehlt -->
If `.slickfab/config` is missing, a required value is missing, or `TRACKER=` names an unknown tracker, the step reports exactly that (which file, which key) and stops at the point where it would need the tracker. It writes no plan, ledger or state file and no ticket list into the repo as a substitute; whatever it has already worked out, it shows in the chat.

It offers to create `.slickfab/config` and shows the content with the values it found in the repo or in the tracker. The file is created only once the human has confirmed team and project.

Answer in the user's language.
<!-- /vertrag:config-fehlt -->

### Tracker: access

<!-- vertrag:zugang -->
- Linear is accessed through the session's Linear tools (in Claude Code, load them via tool search `+linear`).
- If Linear is unreachable (no tools, not logged in, error response, team or project from the configuration does not exist), the step reports exactly that, with the error message, and stops. It writes **no** plan, ledger, state or ticket file into the repo as a substitute. Whatever has already been worked out, it shows in the chat, so that nothing is lost.
- Exception `verify`: If the spec is available as text, verify keeps checking against it instead of stopping. It writes nothing to the tracker, shows the result and fix-ticket proposals only in the chat, and the result ends with `SLICKFAB-STATUS: DONE_WITH_CONCERNS` and states “Tracker not checked” above it, even if every statement is met; this applies provided checking was possible, otherwise with `BLOCKED`. If the spec is not available as text, the previous point applies.

Answer in the user's language.
<!-- /vertrag:zugang -->

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
## Ergebnis debug

**Bug:** <one sentence>
**Red command:** `<command>` → before <red>, after <green>
**Cause:** <the confirmed hypothesis, with evidence>
**Ruled out:** <hypotheses with evidence>
**Regression test:** <test> | missing, finding: <which test seam is missing>
**Debug tag removed:** `grep -rn "DEBUG-<tag>" .` → no match
**Left behind:** <path and reason> or “nothing”
**Why not caught:** <…>
**Recurrence guard:** <proposal>

Nächster Schritt: `/slickfab:review <pull request>` in a fresh session

SLICKFAB-STATUS: <DONE|DONE_WITH_CONCERNS|BLOCKED|NEEDS_CONTEXT>
```

The line “Nächster Schritt” is never missing, not even with `BLOCKED` or `NEEDS_CONTEXT`. Without a red command it reads `Nächster Schritt: /slickfab:debug <bug>, once <what is missing> is available`.
<!-- /regel:ergebnis -->

## Nächster Schritt

<!-- regel:naechster-schritt -->
`/slickfab:review <pull request>` in a fresh session. If the fix is part of a ticket that is not finished yet: back to `/slickfab:implement <ticket>`.
<!-- /regel:naechster-schritt -->
