# Tracker contract: Linear

This contract applies to every slickfab step that reads or writes the tracker. Team and project come from the project configuration (`docs/project-config.md`). Linear is the single source of truth about plan and state: whatever is not written there does not count as decided.

This file is the source. The steps carry the parts they need verbatim in their `SKILL.md` (between `<!-- vertrag:NAME -->` and `<!-- /vertrag:NAME -->`), because a step cannot read files in the plugin folder without read permission. Whoever changes something here changes the copies too; `tests/test_contract_blocks.py` checks that they are identical.

## Access

<!-- vertrag:zugang -->
- Linear is accessed through the session's Linear tools (in Claude Code, load them via tool search `+linear`).
- If Linear is unreachable (no tools, not logged in, error response, team or project from the configuration does not exist), the step reports exactly that, with the error message, and stops. It writes **no** plan, ledger, state or ticket file into the repo as a substitute. Whatever has already been worked out, it shows in the chat, so that nothing is lost.
- Exception `verify`: If the spec is available as text, verify keeps checking against it instead of stopping. It writes nothing to the tracker, shows the result and fix-ticket proposals only in the chat, and the result ends with `SLICKFAB-STATUS: DONE_WITH_CONCERNS` and states “Tracker not checked” above it, even if every statement is met; this applies provided checking was possible, otherwise with `BLOCKED`. If the spec is not available as text, the previous point applies.

Answer in the user's language.
<!-- /vertrag:zugang -->

## Issues

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

## Status flow

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

## Labels

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

## Marker

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

## Rulings

<!-- vertrag:rulings -->
If an agent decides something itself that a human could have decided differently, it immediately writes a comment on the affected issue in exactly this form:

`Ruling: what — why — cost if wrong`

Example: `Ruling: date stored as ISO string — that is how the existing API reads it — a migration of the column if time zones become necessary`

Rulings are collected and presented to the human at the end; they do not replace asking back on product questions or hard-to-reverse decisions.

Answer in the user's language.
<!-- /vertrag:rulings -->
