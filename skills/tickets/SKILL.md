---
name: tickets
description: Use when a reviewed spec should be split into tickets for the tracker, or when someone says “cut this into tickets” or “create the tickets”.
argument-hint: "<spec issue>"
---

<!-- regel:einleitung -->
# tickets: cut the spec into thin, continuous tickets

Goal: Tickets that an agent can build without asking back, as parallel as possible, and that together deliver exactly the spec, not less. Nothing is created until the human has confirmed the list.

Answer in the user's language. Tracker rules and project configuration are below in the section `Vertrag`.
<!-- /regel:einleitung -->

## Wann

<!-- regel:wann -->
- After `/slickfab:challenge`, when the human has decided on objections and the spec is right.
- Not without a spec in the tracker; not if the verdict is `nicht bauen` and the human has agreed.
<!-- /regel:wann -->

## Ablauf

<!-- regel:voraussetzung-pruefen -->
### 1. Check the precondition

- Read `.slickfab/config`. If it is missing or the tracker is unreachable, stop here and report exactly that. Tickets exist only in the tracker; you write no ticket, plan or state file into the repo as a substitute.
- You need the spec issue (argument or `Ergebnis spec` in this conversation). If it is missing, recommend `/slickfab:spec`.
- Read the spec issue with all its comments. Look for the comment from `challenge` (verdict, objections). If it is missing, say so and recommend `/slickfab:challenge <spec issue>` first; continue only if the human explicitly wants to split without a check. If the human has decided on objections that are not yet in the spec, `/slickfab:spec <spec issue>` first. If the last verdict is `nicht bauen`, stop here and put the question to the human (template “question” below), unless they have explicitly said that the spec is to be split anyway.
<!-- /regel:voraussetzung-pruefen -->

<!-- regel:repo-lesen -->
### 2. Read the repo

Find where the spec touches the repo: modules, interfaces, tests, `GLOSSARY.md`, `docs/adr/`, `CLAUDE.md`. For more than a few files, a subagent. Watch for preparatory refactorings that make the actual change easy.
<!-- /regel:repo-lesen -->

<!-- regel:schneiden -->
### 3. Cut

- **Tracer first:** The first ticket is the thinnest path through all layers that wires the spec's critical connections for real once and makes them checkable from outside. It blocks all other tickets.
- **Continuous slices:** Every further ticket delivers a behavior that is checkable from outside, across the layers, is demonstrable on its own and fits into a fresh session. You separate frontend and backend only if the ticket fixes the interface between the two verbatim.
- A **preparatory refactoring** that several tickets need is a ticket of its own, directly after the tracer.
- **Broad mechanical refactorings** (renaming a column, changing a shared type) you cut as Expand–Migrate–Contract: first the new next to the old (expand), then move the callers over in batches, one ticket per batch, blocked by the expand, with the checks staying green in between (migrate), finally remove the old, blocked by all batches (contract).
- An “and” in the title usually means two tickets; more than about 5 criteria usually means too big.

Every ticket in this form:

```markdown
## Was gebaut wird

<behavior from the users' point of view, not layers>

## Akzeptanzkriterien

- [ ] <observable behavior, including error cases>. **Widerlegt, wenn** <the observation that refutes it>.

## Schnittstellen

- Verbraucht: <names, data shapes, routes that this ticket uses from others, with ticket no.>
- Liefert: <names, data shapes, routes that other tickets use from this one>

## Nicht im Umfang

- <what another ticket explicitly does>

+++ Agent notes

**Betroffene Dateien (voraussichtlich)**
- <path>

**Fundstellen** <where in the repo examples are>

+++
```

On the text: `Was gebaut wird` and the criteria in the language of the spec, without paths; paths go only in the Agent notes. Every criterion would be false in the current state; if it is already true, it is not a criterion. The spec's Global Constraints apply to every ticket, because it is a sub-issue of the spec.

Labels per ticket: exactly one size `S`, `M` or `L`, and `door:one-way` if the ticket is hard to reverse (migration, auth, payment, deletion of data, deploy, public interface).
<!-- /regel:schneiden -->

<!-- regel:abhaengigkeiten-setzen -->
### 4. Set dependencies

- The tracer blocks all other tickets.
- Real dependencies (one ticket consumes what another delivers) become blocked-by relations.
- **File overlap:** Make a table file → tickets from the Agent notes. If two tickets name the same file, the later one gets a blocked-by relation on the earlier one, even if they need nothing from each other in content; built in parallel, they would overwrite each other.
- No cycles. Whatever then has no blockers other than the tracer can run in parallel.
<!-- /regel:abhaengigkeiten-setzen -->

<!-- regel:auf-stille-kuerzung-pruefen -->
### 5. Check for silent shortening

Read every title, every description and every criterion for phrases that defer work: “v1”, “simplified”, “placeholder”, “will be wired later”, and everything equivalent (stub, hard-coded for now, TODO, follows later; in German, for example, `vereinfacht`, `Platzhalter`, `wird später verdrahtet`). A ticket with such a phrase you do not create. Instead of replacing the word, you correct the cut: either the ticket delivers it completely, or the deferred part becomes a ticket of its own with its own criteria and a blocked-by relation and is listed in the first one under `Nicht im Umfang`.

| Excuse | Reality |
|---|---|
| “A simplified version is enough to start with.” | Then the smaller version is the spec, and the human decides that in `grill` or `challenge`, not the ticket text. |
| “The next ticket does the wiring.” | Then it is a ticket of its own with criteria. Otherwise nobody builds it. |
<!-- /regel:auf-stille-kuerzung-pruefen -->

<!-- regel:zerlegung-pruefen-und-bestaetigen-lassen -->
### 6. Check the split and get it confirmed

1. Call the split check of `/slickfab:challenge` with spec and list (fresh subagent, round 1). With findings: revise the list, round 2 with the number of findings from round 1. There are at most these 2 rounds; whatever is open after that, you put to the human.
2. Check for duplicates: search the project from `.slickfab/config` for open and completed issues with a similar title, also among the sub-issues of the spec. You show matches in the list. If the tracker answers the search with an error, stop (template “abort” below, `BLOCKED`).
3. Show the numbered list:

```
1. <title> — <size>, <door:one-way if applicable> — blocked by: — (tracer)
   delivers: <one sentence> · files: <short>
2. <title> — <size> — blocked by: 1
   delivers: … · files: …
…
Split check: passed in round <n> | open: <findings>
Duplicates: none | <matches>
```

Ask: Is the size of the slices right? Are the dependencies right? Merge or split anything? Then you wait. Change requests you work in and show the list again. Nothing is created until there is an explicit yes to the list; “fine” to a single row is not a yes to the whole list.
<!-- /regel:zerlegung-pruefen-und-bestaetigen-lassen -->

<!-- regel:anlegen -->
### 7. Create

Only after the yes, and in dependency order (tracer first), so that every relation points to a real issue ID:

- one sub-issue of the spec per ticket, status `Backlog`, labels as in step 3, relations as in step 4,
- after that a comment on the spec issue with the list of tickets and the marker line according to the tracker contract.

You set no ticket to `Todo`; that is the human's approval. You do not change the spec itself. If the tracker breaks off in the middle of creating, stop and report which tickets are created and which are not, with the error message (template “abort” below, `BLOCKED`). You create no file as a substitute.
<!-- /regel:anlegen -->

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
Where tickets ends, and with which template. Every place in the flow where you stop, recommend, wait or put something to the human is listed here:

| Place | Case | Template | STATUS |
|---|---|---|---|
| Step 1 | `.slickfab/config` missing or tracker unreachable | Ergebnis tickets (abort) | `BLOCKED` |
| Step 1 | spec issue missing | Ergebnis tickets (question) | `NEEDS_CONTEXT` |
| Step 1 | `challenge` comment missing | Ergebnis tickets (question) | `NEEDS_CONTEXT` |
| Step 1 | decision not yet in the spec | Ergebnis tickets (question) | `NEEDS_CONTEXT` |
| Step 1 | last `challenge` verdict `nicht bauen` | Ergebnis tickets (question) | `NEEDS_CONTEXT` |
| Step 6 | tracker answers the duplicate search with an error | Ergebnis tickets (abort) | `BLOCKED` |
| Step 6 | duplicate, list waiting for the yes, or findings open after round 2 | Ergebnis tickets (question) | `NEEDS_CONTEXT` |
| Step 7 | tracker breaks off while creating | Ergebnis tickets (abort) | `BLOCKED` |
| Step 7 | all tickets created | Ergebnis tickets | `DONE` or `DONE_WITH_CONCERNS` |

```
## Ergebnis tickets

**Spec:** <issue ID>
**Tickets:** <ID> tracer, <ID>, … (all in Backlog)
**Parallel after the tracer:** <IDs>
**door:one-way:** <IDs or “none”>
**Open from the split check:** <findings or “none”>

Nächster Schritt: `/slickfab:implement <tracer ID>`, once you have set the tickets to Todo

SLICKFAB-STATUS: <DONE|DONE_WITH_CONCERNS>
```

If the step ends without creating tickets because you are asking the human something (duplicate, missing `challenge` comment, verdict `nicht bauen`, list waiting for the yes) or because something is missing (spec, decision in the spec), this template applies. You choose the next step by the reason, as in step 1:

```
## Ergebnis tickets (question)

**Spec:** <issue ID>
**Question:** <what the human has to decide or provide, with links to matches>
**Worked out so far:** <list or state, so that nothing is lost>

Nächster Schritt: `/slickfab:<step>` by reason: if the spec is missing or a decision is not yet in it: `/slickfab:spec [spec issue]`; if the check is missing: `/slickfab:challenge <spec issue>`; if the verdict is `nicht bauen`: `/slickfab:spec <spec issue>` if you change the spec (after that `/slickfab:challenge <spec issue>`); if you agree with the verdict, the work ends and you set the spec to `Canceled`; question about the cut (duplicate, list waiting for the yes, findings open after round 2): `/slickfab:tickets <spec issue>` again, once the answer is there

SLICKFAB-STATUS: NEEDS_CONTEXT
```

If in step 1 the configuration is missing or the tracker is unreachable, if it answers the duplicate search with an error (step 6), or if it breaks off in the middle of creating (step 7), this template applies:

```
## Ergebnis tickets (abort)

**Spec:** <issue ID>
**Where:** step 1 (configuration or tracker) | step 6 (duplicate search) | step 7 (while creating)
**Already created:** <IDs with title and relations set> (in steps 1 and 6: none)
**Not created:** <titles from the confirmed list> (in step 1: all, there is no list yet; in step 6: all titles of the not yet confirmed list)
**Error message:** <verbatim: missing file or missing key, or the tracker's error response>

Nächster Schritt: `/slickfab:tickets <spec issue>` again, after you have <created `.slickfab/config` | checked the tracker (tools loaded, logged in, team and project exist)>; after an abort in step 7 the duplicate check finds the tickets already created, and only the rest is created

SLICKFAB-STATUS: BLOCKED
```

The line `Nächster Schritt` is never missing, not even for a question (`NEEDS_CONTEXT`). The marker line is the last line of your answer and stands outside any code block. The templates are shown in code blocks here only for display; you write your answer as normal text, without a code block around result or marker.
<!-- /regel:ergebnis -->

## Nächster Schritt

<!-- regel:naechster-schritt -->
The human checks the tickets and sets them to `Todo`. Then `/slickfab:implement <tracer ID>` for the first ticket; the others become free as soon as the tracer is merged.
<!-- /regel:naechster-schritt -->
