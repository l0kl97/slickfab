---
name: spec
description: Use when a specification should be created in the tracker from a clarified conversation (after grill), or when someone says “write the spec”.
argument-hint: "[feature name or spec issue to revise]"
---

<!-- regel:einleitung -->
# spec: specification from the conversation

Goal: A spec from which implementer and reviewer read the same goal without having seen the conversation. You write down what has been decided. You do not interview again: decisions on content are made in `grill`, not here.

Answer in the user's language. Tracker rules and project configuration are below in the section `Vertrag`.
<!-- /regel:einleitung -->

## Wann

<!-- regel:wann -->
- After `/slickfab:grill`, when the summary `Ergebnis grill` is confirmed.
- To revise an existing spec when the human has decided on objections from `challenge` (argument: the spec issue).
- Not while product questions are open; then `grill` first.
<!-- /regel:wann -->

## Ablauf

<!-- regel:voraussetzung-pruefen -->
### 1. Check the precondition

You need a clarified basis. Look in this order for:

1. a confirmed summary `Ergebnis grill` in this conversation,
2. a spec issue given as argument (then you read it with its comments and work in the decisions named there),
3. a conversation in which the human has explicitly decided problem, users, scope and success criterion.

If you find none of these, you stop here: say that the basis is missing and recommend `/slickfab:grill <topic>`. Do not write a spec on speculation.

Then read `.slickfab/config` (format and rules: project configuration). If it is missing or the tracker is unreachable, say so right now: you can show the spec in the chat, but not create it.
<!-- /regel:voraussetzung-pruefen -->

<!-- regel:lage-im-repo-lesen -->
### 2. Read the situation in the repo

Read what the spec has to bind: `CLAUDE.md`/`AGENTS.md`, `.slickrails/` (if present), `GLOSSARY.md`, `docs/adr/`, existing feature docs on the topic. Use the terms from `GLOSSARY.md` and contradict no ADR without saying so. For more than a few files you send a subagent and have it give you the result briefly.
<!-- /regel:lage-im-repo-lesen -->

<!-- regel:jede-aussage-auf-ihre-herkunft-pruefen -->
### 3. Check every statement for its origin

Go section by section through the template (step 4). Every statement you want to write comes from one of these sources:

- decided by the human (in the conversation or in `Ergebnis grill`),
- “Decided autonomously” from `grill`,
- a fact from the repo.

If a statement fits no source, it is an **open decision**. Classify it as in `grill`:

- **Reversible, technical** (swappable behind a stable interface): decide yourself and enter it under `Autonom entschieden`, with a reason.
- **Product question or hard to reverse:** Here you stop. List the open decisions, one sentence each on why the spec needs them, and recommend `/slickfab:grill` with exactly these points. You only continue writing the spec once they are decided.

This rule has no exception:

| Excuse | Reality |
|---|---|
| “The answer is obvious.” | Then the question in `grill` costs a minute. A silent assumption costs a wrongly built feature. |
| “I'll mark it as an assumption in the spec.” | A marked assumption is still a decision the human did not make. |
| “I'll quickly ask here myself.” | `spec` asks no questions on content; the interview with recommendation and classification belongs to `grill`. |
<!-- /regel:jede-aussage-auf-ihre-herkunft-pruefen -->

<!-- regel:spec-schreiben -->
### 4. Write the spec

Fill in this template. Write in the behavior and terms of the domain: modules and interfaces by name, but without file paths and without code, because both go stale quickly. Where a path would suggest itself, name the module or the behavior.

```markdown
## Bitte (wörtlich)

> “<the human's original request, quoted verbatim, typos included>”

## Problem

<from the users' point of view: who has which problem, how does it show today>

## Lösung

<from the users' point of view: what is different afterwards. For changes to an existing feature as a delta: before → after>

## User Stories

1. As a <role> I want <capability> so that <benefit>.
(better too many than too few; error cases and edge cases get their own stories)

## Entscheidungen

- <decision> (by the human)
- Autonom entschieden: <decision> — <why> — reversible because <…> (or “none”)

## Muss wahr sein

- <observable truth from the users' point of view that holds after building; 3–7 points>

## Kritische Verbindungen

- <part A> ↔ <part B>: <what must flow between the two; how you can tell it is wired>
(the places where it is most likely to break)

## Grenzen

- **Immer:** <what every implementer always does>
- **Erst fragen:** <what happens only with the human's yes>
- **Nie:** <what is ruled out>

## Global Constraints

- <rule every ticket must follow, verbatim from CLAUDE.md, slickrails rules, versions, conventions>

## Review-Fokus

- <input class or risk that no test checks and that the reviewer should look at>

## Teststellen

- <public interface at which the behavior is checked> — fängt: <…> — verpasst: <…>
(as high up as possible, as few as possible, existing ones preferred; ideally exactly one)

## Nicht im Umfang

- <what is explicitly not built>
```

If the test seams (`Teststellen`) were not decided in `grill`, you propose them and enter them under `Autonom entschieden`; the human sees them in step 5.
<!-- /regel:spec-schreiben -->

<!-- regel:selbstpruefung-dann-zeigen -->
### 5. Self-check, then show

Check the draft before the human sees it:

- all sections of the template present, none empty (empty = “none” with one sentence why),
- the request is there verbatim, not rephrased,
- no file path, no file name, no code in the text,
- every statement has a source from step 3.

Show the spec in the chat and ask whether you should create it like this. This is an approval, not a question on content: if the human wants something different, take it on; if their answer opens a new product question, back to step 3.
<!-- /regel:selbstpruefung-dann-zeigen -->

<!-- regel:im-tracker-anlegen -->
### 6. Create in the tracker

Only after the yes. As in the tracker contract: check for duplicates, then issue `Spec: <Feature>` in the project from `.slickfab/config`, status `Backlog`. When revising, you update the existing spec issue instead of creating a new one and write a comment whose first line is exactly `## Spec überarbeitet`; below it stands what has changed, at the end the marker line. By this first line `fab` recognizes that the spec was changed after a `challenge` verdict.

If the tracker is unreachable or the configuration is missing, you report that with the error message and leave the spec in the chat. You create no spec, plan or ticket file in the repo.
<!-- /regel:im-tracker-anlegen -->

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
A spec issue in the tracker (or, without a tracker, the spec in the chat and the clear message why it was not created). In the chat at the end:

```
## Ergebnis spec

**Spec:** <issue ID and link> (or: not created because <reason>)
**Decided autonomously:** <list or “none”>
**Open decisions:** <list, then back to grill, or “none”>

Nächster Schritt: `/slickfab:challenge <issue ID>`
```
<!-- /regel:ergebnis -->

## Nächster Schritt

<!-- regel:naechster-schritt -->
`/slickfab:challenge <issue ID>`: fresh eye on product, buildability and later the split; best in a new session, so that the checker does not know the conversation. If there are questions that cannot be settled by asking (look, handling, whether a piece of logic feels right), `/slickfab:prototype` first. If decisions are missing, back to `/slickfab:grill`.
<!-- /regel:naechster-schritt -->
