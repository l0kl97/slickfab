---
name: implement
description: Use when an approved ticket should be built, or when someone says “build the ticket” or “implement EX-123”.
argument-hint: "<ticket>"
---

<!-- regel:einleitung -->
# implement: one ticket via TDD up to the pull request

Goal: A pull request that fulfils exactly the ticket and proves for every criterion that the test was red first and then green. No more, no less.

Answer in the user's language. Tracker rules and project configuration are below in the section “Vertrag”.
<!-- /regel:einleitung -->

## Wann

<!-- regel:wann -->
- When a ticket is in `Todo` (the human has approved it) and should be built.
- Not without a ticket; not for finding a bug whose cause is unknown (use `/slickfab:debug` for that).
<!-- /regel:wann -->

## Ablauf

<!-- regel:voraussetzung -->
### 1. Check the precondition

- You need the ticket (argument). Read it with all comments, and the spec it is a sub-issue of. If a pull request for the ticket already exists, you also read its review comments; together with those on the ticket, they show which gaps a review has already found.
- Read `.slickfab/config` and, if present, `.slickrails/config.sh`, both only as text (rules in the contract). If the configuration is missing or the tracker is unreachable, stop here and report exactly that.
- You take check commands only from `.slickrails/config.sh` or `.slickfab/config`; you do not guess any from `package.json`, `Makefile` or habit. If a check command is missing, you say which one, and that you cannot run it. Without `CHECK_TEST` you cannot prove that the whole suite is green; the step then ends with `DONE_WITH_CONCERNS` at best.
- If the ticket is not in `Todo` or `In Progress`, it is not approved for building: stop and say so.
- If someone else's changes are open in the working tree, stop and say so. You do not move or hide anyone else's work.
- **Baseline:** Run `CHECK_TEST` once before the first change and record command and result. If it is already red, you report that before you build; you do not fix someone else's red tests on the side.
- Before the first test, check whether the ticket touches the stop list (step 5).
- Set the ticket to `In Progress`.
<!-- /regel:voraussetzung -->

<!-- regel:kriterien-in-tests-uebersetzen -->
### 2. Translate criteria into tests

Go through the ticket's acceptance criteria in order, one at a time. For each one you consider:

- **Test seam:** Through which public interface does the behaviour show (the spec's test seams)? Tests check behaviour from the outside: no private methods, no call counters, no direct look into the database if there is an interface for it. A test that breaks on a refactoring without a change in behaviour is cut wrong.
- **Expected value:** from the spec, the ticket or an example worked out by hand, never from the same logic as the code.
- **Counter-check:** Name the change to the production code that would turn this test red. If you cannot think of one, the test checks nothing.
- **Error cases** (invalid input, error responses, boundary values) are part of it. Mock only at system boundaries (third-party APIs, mail, time, randomness), never your own code.

The review (`/slickfab:review`) uses a mutation probe to check every behaviour in the diff, not just the criteria. That is why the same rule applies to you: Every behaviour that your diff introduces or changes needs a test, even if the ticket does not mention it. You close a known gap from an earlier review comment on the ticket or on the pull request with a red and a green run, or you explicitly justify in the pull request under “Nicht angefasst” why it stays open.

Do not write all tests up front and do not build anything in advance.
<!-- /regel:kriterien-in-tests-uebersetzen -->

<!-- regel:rot-gruen -->
### 3. Per criterion: red, then green

1. **Red:** Write exactly the test for this criterion and run it. Record command and output. It must be red for the expected reason (the assertion fails because the behaviour is missing), not because of a typo or an import. If it is green right away, the criterion is already met or the test checks nothing: clear that up before you continue.
2. **Green:** Write just enough production code for this test to pass, and run it again. Record command and output.
3. In between, the type check (`CHECK_TYPECHECK`, if present) and the affected test file.

No production code for this criterion without a red run. Cleaning up and refactoring do not belong in this loop; whatever you notice, you name in the pull request under “Bedenken”.

A fix attempt is a change to the production code after which the same test is red again. Count them visibly (“Attempt 1/3”). After 3 failed fix attempts at the same place, you stop. You do not start a fourth attempt. You report `BLOCKED` with the three attempts and their output and recommend `/slickfab:debug` in a fresh session; three failed attempts usually mean that the assumption about the cause is wrong, not that a fourth idea is missing.

You do not weaken existing tests to get green: no skipping (`skip`, `only`, `xfail`, commented out), no deleted or loosened assertions, no lowered thresholds (coverage, time limits, tolerances), no new suppressions (`@ts-ignore`, `eslint-disable`, `noqa`). If an existing test is in the way, you do not change it; you stop and report it: which test, what it expects, what the ticket demands, where they contradict each other. Status `BLOCKED`; whether the test or the ticket is wrong is for the human to decide. This applies even if the ticket explicitly wants to change the behaviour that the test pins down: Whether an existing test may go is only settled once the human has recorded it on the ticket. With this approval, you change exactly this test and name it under “Änderungen”.

| Excuse | Reality |
|---|---|
| “The ticket asks for exactly this new behaviour.” | The test records a decision that someone made earlier. Whether it no longer applies is for the human to decide, not the ticket text and not you. |
| “The old test is wrong anyway.” | Then that is a finding for the human. A test that the implementer adjusts to fit only checks the implementer. |
| “The test is flaky, I'll set it to skip for a moment.” | A skipped test is a deleted test that nobody notices. Report it. |
| “The threshold was too strict anyway.” | Whoever lowers the threshold decides on quality; that is not part of the ticket. |
<!-- /regel:rot-gruen -->

<!-- regel:abweichungen -->
### 4. Deviations

While building, you find work that is not in the ticket. This is how you deal with it:

- **Rule 1, bug:** Existing code does not do what it should and gets in the way of your criterion (wrong query, logic error, broken check). You fix it with its own red and green run.
- **Rule 2, missing critical function:** Without it, your criterion would not be correct or not safe (missing error handling, missing input validation, missing timeout on an external call). You add it with a test.
- **Rule 3, blocker:** Something stops you mechanically (wrong type, broken import, missing test configuration). You clear it away.
- **Rule 4, architecture question:** Here you stop and report `BLOCKED` with a reason. Architecture question means: a new table or interface that the ticket does not name, a different pattern from the existing one, a new dependency, a change that other tickets would have to follow. You name the question, the options and your recommendation.

What you do under rules 1–3 you name in the pull request under “Änderungen” as `[Rule N] what, why`, and for each decision that a human could have made differently you write a ruling on the ticket. The stop list takes precedence over rules 1–3.
<!-- /regel:abweichungen -->

<!-- regel:stopp-liste -->
### 5. Stop list

Before each change, check if it touches one of these points:

- auth and permissions (login, roles, access checks),
- destructive migrations (dropping a column or table, narrowing a type, rewriting data),
- payments,
- deletions of data,
- deploys and anything that rolls out live,
- secrets (creating, changing, printing, writing them into files),
- anything a revert does not bring back (sent mails, calls to third-party systems with side effects, published packages).

If the ticket or your way there touches one of these points, you stop before you build it and report `BLOCKED` with a reason: which point, where, what you would build, what a mistake would cost. This applies even if the ticket explicitly demands it; the approval for it is given by a human for exactly this point, and it is recorded on the ticket afterwards. With this approval, you keep building and set `door:one-way`.

When you stop (rule 4, stop list, test in the way), you write a comment on the ticket with the reason and the state so far, and set `slickfab:needs-human`. What is already built stays on the branch.
<!-- /regel:stopp-liste -->

<!-- regel:pruefungen -->
### 6. Whole suite and checks

Once all criteria are green, you run the whole suite (`CHECK_TEST`), plus `CHECK_TYPECHECK` and `CHECK_LINT`, where present. Record command and result. Red means not done. You never bypass hooks (`--no-verify` and the like), unless the human has recorded it on the ticket for exactly this push; then the reason is in the commit. A promise in the conversation is not enough. If a hook blocks with findings, you fix the findings.

If the repo (for example `CLAUDE.md`) requires a review before the pull request, you do it now. A mandatory review before the pull request (such as `/security-review`) is an intermediate step: Afterwards you continue with commit, push and pull request. You fix real findings with a red and a green run; the rest you name under “Bedenken”.
<!-- /regel:pruefungen -->

<!-- regel:pull-request -->
### 7. Pull request

Commit with a message that says why and what. Push the branch and open a pull request against the main branch. Do not merge. The text has this form (the section names stay as written, roles and the review refer to them):

```markdown
<ticket ID>: <title>

## Änderungen

- <what changes for users or callers, one sentence per point>
- [x] <acceptance criterion from the ticket, ticked when proven>
- Deviations: <[Rule 1–3] what, why> or “none”

## Nicht angefasst

- <what was close by but deliberately not changed, and why> or “none”

## Bedenken

- <what you noticed that does not belong to the ticket, open risks> or “none”

## Door

`one-way` | `two-way`: <one sentence on why; `one-way` if a revert does not bring everything back>

## Blast Radius

<one word or a short sentence: who or what is affected if it goes wrong>

## Nachweise

Baseline: `<CHECK_TEST>` → <result before the first change>

- K1 <criterion in short form>
  - red: `<command>` → <output, cut down to the decisive line>
  - green: `<command>` → <output>
- K2 …

Whole suite: `<CHECK_TEST>` → <result>
```

If the red run is missing for a criterion, the pull request is not done. Every section is in the text, even if it is empty; then it says “none” below it. An empty section tells the reviewer that you thought about it; a missing one tells them nothing.
<!-- /regel:pull-request -->

<!-- regel:abschluss -->
### 8. Wrap-up

Set the ticket to `In Review` as soon as the pull request is open, and write a comment on the ticket with the link. The step only ends with the “Ergebnis implement” (below); a review report, a test output or an open pull request without this result is not an end.
<!-- /regel:abschluss -->

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

### Tracker: status flow

<!-- vertrag:status -->
`Backlog` → `Todo` → `In Progress` → `In Review` → `Done` (abort: `Canceled`, duplicate: `Duplicate`)

| Transition | Who |
|---|---|
| create in `Backlog` | `spec`, `tickets` |
| `Backlog` → `Todo` | only the human (this is the approval to build) |
| `Todo` → `In Progress` | the implementer at the start |
| `In Progress` → `In Review` | the implementer, once the pull request is open |
| `In Review` → `Done` | after the merge |

No step sets a ticket to `Todo` by itself.

Answer in the user's language.
<!-- /vertrag:status -->

### Tracker: labels

<!-- vertrag:labels -->
The labels exist in the team; a step does not create new ones. If one is missing, it reports that.

| Label | Meaning |
|---|---|
| `slickfab:rework` | reviewer demands rework |
| `slickfab:ready` | review passed, waiting for a human to merge |
| `slickfab:needs-human` | loop exhausted or agent blocked: a human decides |
| `slickfab:replan` | ticket or spec is cut wrong: back to planning |
| `door:one-way` | hard to reverse (migration, auth, payment, deletion, deploy): always a human gate, never auto-merge |
| `S`, `M`, `L` | size (effort small, medium, large); exactly one per ticket. `L` is a hint that the ticket should rather be split |

In Linear, `rework`, `ready`, `needs-human` and `replan` are children of the label group `slickfab`; in texts, comments and this contract they are written as `slickfab:<name>`. When searching and setting via the Linear tools, the label is called `rework`, `ready`, `needs-human` or `replan` in the group `slickfab`; a search for `slickfab:rework` finds nothing, and that does not mean the label is missing. The group allows only one at a time.

Answer in the user's language.
<!-- /vertrag:labels -->

### Tracker: rulings

<!-- vertrag:rulings -->
If an agent decides something itself that a human could have decided differently, it immediately writes a comment on the affected issue in exactly this form:

`Ruling: what — why — cost if wrong`

Example: `Ruling: date stored as ISO string — that is how the existing API reads it — a migration of the column if time zones become necessary`

Rulings are collected and presented to the human at the end; they do not replace asking back on product questions or hard-to-reverse decisions.

Answer in the user's language.
<!-- /vertrag:rulings -->

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
## Ergebnis implement

**Ticket:** <ID> (now `In Review`)
**Pull request:** <link>
**Criteria:** <n> of <n> proven with a red and a green run
**Whole suite:** `<CHECK_TEST>` → <result>
**Deviations:** <[Rule N] …> or “none”
**Door:** `one-way` | `two-way`

Nächster Schritt: `/slickfab:review <pull request>` in a fresh session

SLICKFAB-STATUS: <DONE|DONE_WITH_CONCERNS|BLOCKED|NEEDS_CONTEXT>
```

With `BLOCKED` or `NEEDS_CONTEXT`, the reason takes the place of pull request and criteria: which point of the stop list, which architecture question, which test is in the way or which three fix attempts, and what the human has to decide. The line “Nächster Schritt” is never missing, not even with `BLOCKED` or `NEEDS_CONTEXT`. It then reads `Nächster Schritt: /slickfab:implement <ticket>, once the decision is on the ticket` (after three failed attempts: `/slickfab:debug`).
<!-- /regel:ergebnis -->

## Nächster Schritt

<!-- regel:naechster-schritt -->
`/slickfab:review <pull request>` in a fresh session, so that the reviewer does not know your report. With `BLOCKED`: the human decides, then `/slickfab:implement <ticket>` again.
<!-- /regel:naechster-schritt -->
