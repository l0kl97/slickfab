---
name: handoff
description: Use when the work on a ticket should be handed over to a fresh session because the context is filling up or the session is ending, or when someone says “write a handoff”.
argument-hint: "<ticket> [what the next session is for]"
---

<!-- regel:einleitung -->
# handoff: a handoff in 5 points

Goal: A fresh session continues where this one stops, without knowing the conversation. The handoff is a comment on the ticket.

Answer in the user's language. Tracker rules and project configuration are below in the section “Vertrag”.
<!-- /regel:einleitung -->

## Wann

<!-- regel:wann -->
- When the context is filling up (warning from about two thirds) or the session ends before the ticket is done.
- When another agent or human takes over the ticket.
<!-- /regel:wann -->

## Ablauf

<!-- regel:voraussetzung -->
### 1. Check the precondition

- You need the ticket (argument, or the ticket this session is working on).
- Read `.slickfab/config` and, if present, `.slickrails/config.sh`, both only as text (rules in the contract). If the configuration is missing or the tracker is unreachable, you write the handoff anyway, but show it only in the chat and say why.
- You take check commands only from `.slickrails/config.sh` or `.slickfab/config`; you do not guess any from `package.json`, `Makefile` or habit. If a check command is missing, you say which one, and that you cannot run it.
<!-- /regel:voraussetzung -->

<!-- regel:stand -->
### 2. Gather the state

Collect what the next session needs from sources, not from memory:

- ticket, spec and their comments (rulings, earlier handoffs),
- `git status`, `git log` since the main branch, open pull requests for the branch,
- the check commands from the configuration. You run the check commands now and note command and result; a result from an hour ago is no result.

You name an approval only if it is documented permanently: as a comment on the ticket, as a ruling, as a comment in the pull request. The link goes with it. What was promised in the conversation but is not recorded anywhere permanently is not an approval; you write it under “Open approvals” as open and ask the human whether they want to record it on the ticket. You do not record it as granted yourself.

| Excuse | Reality |
|---|---|
| “The human allowed it earlier in the chat.” | The next session does not see the chat. If it is not on the ticket, it is open for that session. |
| “It was clearly meant that way.” | A derived approval is a decision that nobody made. |
<!-- /regel:stand -->

<!-- regel:uebergabe -->
### 3. Write the handoff

References instead of copies: What is already in the ticket, spec, commit, pull request or ADR, you link instead of copying it. You replace secrets (keys, passwords, personal data) with `<REDACTED>`.

```markdown
## Handoff <ticket ID>, <date>

**1. Scope and decisions**
- Goal of this ticket in one sentence; what explicitly does not belong to it
- Decisions since the start: <link to ruling/comment>, one line each

**2. Ticket state**
- [x] <criterion> (proven by <test/commit>)
- [ ] <criterion>: <how far, what comes next>
- In progress: <hypothesis, fix attempt n/3, debug tag `[DEBUG-…]` still in the code?>

**3. Files and working tree**
- Branch `<name>`, last commit `<sha>`, pull request <link or “none”>
- Not committed: <files from `git status`> or “clean”

**4. Check commands with result**
- `<command>` → <result> (ran at <time>)

**5. Open approvals**
- <what a human has to decide or approve, and where it should be recorded> or “none”
- Documented as granted: <link> or “none”

**For the next session:** `/slickfab:<step> <ticket>`; read first: <links>
```
<!-- /regel:uebergabe -->

<!-- regel:ablegen -->
### 4. Post it on the ticket

Post the handoff as a comment on the ticket, with the marker line according to the tracker contract at the end (usually `NEEDS_CONTEXT`, because a fresh session has to continue; `BLOCKED` if an open approval holds up the work). You do not change the ticket's status. If the tracker is unreachable, you show the handoff in full in the chat and say so; you create no handoff file in the repo.
<!-- /regel:ablegen -->

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
## Ergebnis handoff

**Ticket:** <ID>
**Handoff:** <link to the comment>

Nächster Schritt: `/slickfab:implement <ticket>` in a fresh session

SLICKFAB-STATUS: <DONE|BLOCKED|NEEDS_CONTEXT>
```

The line “Nächster Schritt” is never missing, not even with `BLOCKED` or `NEEDS_CONTEXT`.
<!-- /regel:ergebnis -->

## Nächster Schritt

<!-- regel:naechster-schritt -->
In a fresh session `/slickfab:implement <ticket>` (or the step that was interrupted, such as `/slickfab:debug`); it reads the handoff on the ticket first.
<!-- /regel:naechster-schritt -->
