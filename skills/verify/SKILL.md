---
name: verify
description: Use when all tickets of a spec are merged and it should be checked whether the spec's goal is really reached, or when someone asks “is the feature done?”.
argument-hint: "<spec issue>"
---

<!-- regel:grenzen -->
# verify: Is the spec's goal reached?

Goal: After the last ticket, establish whether what the spec promises under “Muss wahr sein” (must be true) really holds in the code on the main branch, not just whether all tickets are done. Completed tickets prove nothing; each one can have passed while the parts are not connected to each other.

You do not change any code. Your result is a report and, after confirmation, fix tickets.

Answer in the user's language. Tracker rules and project configuration are below in the section “Vertrag”.
<!-- /regel:grenzen -->

## Wann

<!-- regel:wann -->
- When all tickets of a spec are `Done` (merged).
- Again, after fix tickets from an earlier run have been merged.
- Not for a single pull request; for that there is `/slickfab:review`.
<!-- /regel:wann -->

## Ablauf

<!-- regel:ablauf -->
### 1. Check the precondition

- You need the spec issue (argument). If it is missing, ask for it and stop.
- Read `.slickfab/config` and the spec issue with all comments and sub-issues, with the session's Linear tools (in Claude Code, load them via tool search `+linear`). If the configuration is missing, the contract below applies (section “when it is missing”). If the tracker is unreachable, say so with the error message. If the spec is available as text in the argument, you check against it and show the result in the chat; fix tickets then stay a list in the chat (step 5). The result then ends with `DONE_WITH_CONCERNS` and states “Tracker not checked” above it, even with `bestanden`, provided checking was possible, otherwise with `BLOCKED` (contract, section access). If it is not available, you stop and report that with `SLICKFAB-STATUS: NEEDS_CONTEXT`. You write no plan, ticket or result file into the repo as a substitute.
- If tickets are still open, name them. Continue only if the human explicitly wants to check anyway; open tickets then do not explain gaps away.
- Check on the current main branch with a clean working state (`git status --short` empty). Name the commit you check. If your session is not already cleanly on the main branch, you do not move anyone else's checkout (no `git checkout`); instead, after `git fetch`, you create a worktree in detached state in the working directory as in review (`git worktree add --detach .slickfab-verify-<spec> origin/<main branch>`), run the check commands there and remove it afterwards in any case (`git worktree remove --force`).

### 2. Collect statements

Take every line from the spec under “Muss wahr sein” and every one under “Kritische Verbindungen” (critical connections) as a statement of its own, verbatim. Completed tickets, PR texts and the implementers' reports are not evidence; you assume that the goal is not reached until the code shows the opposite. If the spec has no section “Muss wahr sein”, say so and derive the statements from problem and user stories, marked as derived.

### 3. Per “Muss wahr sein” statement, check four levels

For every statement: Which files, functions, routes or commands have to carry it? Then in order, and a level only counts once the one before it is met:

1. **exists:** The carrying parts are there on the main branch (file, function, route, command).
2. **real:** They do something, instead of just being there. No stub: no empty function, no `return null`/fixed return value without logic, no `TODO`/`placeholder`/“not implemented”, no handler that only logs, no UI that shows fixed sample text.
3. **wired:** The production code calls them, on the path that the statement describes (import and call, registered route, menu entry, hook in the configuration). Look for the callers; tests do not count as callers here.
4. **data flows:** Real inputs get through: Follow a value from the source (user input, database, API) to the output. If the chain ends in a fixed value, a mock or an empty list, the level is not met. Where possible, run the path (command, test through the public interface, call of the route) and note command and output.

If a file or function exists but nothing in the production code calls it, the statement is not met, even if its own tests are green. Being present is not behaviour.

At the end, run the repo's check commands (from `.slickrails/config.sh`, otherwise `.slickfab/config`). Red is a gap, even if it does not directly concern a statement.

Per statement one result: `met` (all four levels with evidence), `not met` (name the level where it fails, with `file:line` or command and output) or `unclear` (cannot be checked by machine, such as look, feel, behaviour against a third-party system that you cannot reach; say what a human would have to check). Do not choose `unclear` if the absence is observable; then it is `not met`.

### 4. Status

Exactly one status for the spec (the values stay as written, `/slickfab:fab` reads them):

| Status | When |
|---|---|
| `bestanden` | every statement `met`, check commands green |
| `Lücken gefunden` | at least one statement `not met` or a check command red |
| `Mensch nötig` | no statement `not met`, but at least one `unclear` |

`bestanden` only if every statement meets all four levels. A high share of met statements does not make the rest any easier; check the last one as closely as the first.

### 5. Propose fix tickets

Only with `Lücken gefunden`. Per gap one ticket proposal: title (verb + outcome), the statement from the spec verbatim, the level where it fails, with evidence, a criterion with “Widerlegt, wenn” (refuted if), size `S`, `M` or `L`, and under “Agent notes” the affected files. Gaps that have the same cause you combine into one ticket.

1. Show the human the proposals as a numbered list.
2. Check for duplicates: open and completed issues in the project with a similar title. You name matches at their place in the list.
3. Nothing is created until there is an explicit yes to the list (as a whole or to single numbers). Without a yes you create no issue; silence, “sounds good” to something else, or a yes from an earlier conversation do not count.
4. Only after the yes: Create the confirmed tickets as sub-issues of the spec in `Backlog`, according to the contract below (section issues). You set no fix ticket to `Todo`; the approval to build is given by the human. You do not change the status of other issues.

If the tracker is unreachable, the list stays in the chat; you create no file as a substitute.

### 6. Record

Write the result as a comment on the spec issue (if the tracker is reachable), the last line being the STATUS line according to the contract: `DONE` with `bestanden`, `DONE_WITH_CONCERNS` with `Lücken gefunden` or `Mensch nötig`, `BLOCKED` if you could not check. Without a tracker, against the spec as text, no comment: The result is in the chat, states “Tracker not checked” and ends with `DONE_WITH_CONCERNS`, provided checking was possible, otherwise with `BLOCKED`. You do not change the status of the spec issue.
<!-- /regel:ablauf -->

## Vertrag

<!-- regel:vertrag-quelle -->
Verbatim from `tracker/linear.md` and `docs/projektkonfiguration.md` of the slickfab plugin. It is here so that you do not have to read anything outside the project; it applies exactly as written.
<!-- /regel:vertrag-quelle -->

### Tracker: access

<!-- vertrag:zugang -->
- Linear is accessed through the session's Linear tools (in Claude Code, load them via tool search `+linear`).
- If Linear is unreachable (no tools, not logged in, error response, team or project from the configuration does not exist), the step reports exactly that, with the error message, and stops. It writes **no** plan, ledger, state or ticket file into the repo as a substitute. Whatever has already been worked out, it shows in the chat, so that nothing is lost.
- Exception `verify`: If the spec is available as text, verify keeps checking against it instead of stopping. It writes nothing to the tracker, shows the result and fix-ticket proposals only in the chat, and the result ends with `SLICKFAB-STATUS: DONE_WITH_CONCERNS` and states “Tracker not checked” above it, even if every statement is met; this applies provided checking was possible, otherwise with `BLOCKED`. If the spec is not available as text, the previous point applies.

Answer in the user's language.
<!-- /vertrag:zugang -->

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

### Tracker: issues

<!-- vertrag:issues -->
| Kind | Title | Location | Initial status |
|---|---|---|---|
| Spec | `Spec: <Feature>` | project from the configuration | `Backlog` |
| Ticket | verb + outcome, without “and” | sub-issue of the spec | `Backlog` |

- Before creating anything, check for duplicates: search open and completed issues in the project with a similar title. If there is a match, name it and ask instead of creating a duplicate.
- Dependencies are Linear relations “blocked by”, not text in the description.
- Details for agents (affected files, locations) go in a collapsible section “Agent notes” at the end of the description.

Answer in the user's language.
<!-- /vertrag:issues -->

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
## Ergebnis verify

**Spec:** <issue> · **Checked at commit:** <SHA on the main branch>
**Status:** bestanden | Lücken gefunden | Mensch nötig

| Statement (verbatim) | exists | real | wired | data flows | Result | Evidence |
|---|---|---|---|---|---|---|
| <line from “Muss wahr sein”> | ✓ | ✓ | ✗ | – | not met | `<file:line>` / `<command>` → <output> |

**Check commands:** `<command>` → <result>
**Human checks:** <what, how> (with `unclear`)
**Fix tickets:** <proposals, numbered> · created: <links> or “waiting for a yes”

Nächster Schritt: `/slickfab:implement <fix ticket>` | `/slickfab:retro`

SLICKFAB-STATUS: DONE|DONE_WITH_CONCERNS|BLOCKED|NEEDS_CONTEXT
```
<!-- /regel:ergebnis -->

## Nächster Schritt

<!-- regel:naechster-schritt -->
- `bestanden`: `/slickfab:retro`, to turn the mistakes of this feature into rules.
- `Lücken gefunden`: approve the fix tickets (`Todo`) and build them with `/slickfab:implement <fix ticket>`, then `/slickfab:verify <spec issue>` again.
- `Mensch nötig`: the human checks the named points; then `/slickfab:verify <spec issue>` again.
<!-- /regel:naechster-schritt -->
