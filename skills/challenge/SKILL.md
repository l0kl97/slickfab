---
name: challenge
description: Use when a spec needs a fresh outside look before it is split (product, buildability), or a ticket split should be checked before the tickets are created, or when someone says “challenge this”.
argument-hint: "<spec issue> | split <spec issue> round <1|2>"
---

<!-- regel:einleitung -->
# challenge: fresh eye on spec and split

Goal: Mistakes stand out before anything is built. The checker knows only the result of the planning, not the conversation it came from; that way they see what is missing in the text instead of filling it in from memory.

Answer in the user's language. Tracker rules and project configuration are below in the section `Vertrag`.
<!-- /regel:einleitung -->

## Wann

<!-- regel:wann -->
- **Spec check:** after `/slickfab:spec`, before splitting. Checks product and buildability.
- **Split check:** from within `/slickfab:tickets`, before the human sees the ticket list. Checks whether the tickets cover the spec completely and cleanly.
- Not for code review; there is the review step for that.
<!-- /regel:wann -->

## Ablauf

<!-- regel:voraussetzung-pruefen -->
### 1. Check the precondition

- The **spec check** needs a spec: as a spec issue (argument) or, without a tracker, as text in the argument. If there is none, stop and recommend `/slickfab:spec`.
- The **split check** needs the spec, the numbered ticket list and the round (1 or 2, 1 if not stated). In round 2 also the number of findings from round 1. If the list is missing, recommend `/slickfab:tickets`.
- Read `.slickfab/config` and the spec issue with its comments. If the configuration is missing or the tracker is unreachable, say so; you can still check if the spec is available as text, but show the result only in the chat.
<!-- /regel:voraussetzung-pruefen -->

<!-- regel:frischen-blick-herstellen -->
### 2. Establish the fresh eye

The checker gets only the spec (for the split check: spec and ticket list) and may read the repo, but not the planning conversation.

- If planning is already going on in this session (`grill`, `spec`, `tickets` or a conversation about the feature), start a fresh subagent. Give it verbatim only the spec, or spec and list, the matching check assignment from step 3 or 4 and the output format. No summary of the conversation, no justifications, no assessment of your own.
- If the session is fresh (only this call), you check yourself.
- If you cannot start a subagent, say so and recommend calling `/slickfab:challenge <spec issue>` in a new session. Do not check yourself in a session that knows the conversation.
<!-- /regel:frischen-blick-herstellen -->

<!-- regel:spec-pruefung -->
### 3. Spec check (assignment for the checker)

Read the spec and then, in the repo, what already exists (README, feature docs, ADRs, affected places).

**A. Product.** Check from the users' point of view, not the technology:

- Who really has the problem, and how do you notice that it is solved?
- What is the smallest version with the same value? What can go?
- What already exists that does the same or contradicts it?
- Which assumption is the shakiest, and what happens if it is wrong?
- Does it fit earlier decisions in the repo?

Write at most 7 objections, the most important first, each with one sentence of reasoning and a recommendation: drop, change or keep. If you have no real objection, say so; do not invent one. Then a verdict, exactly one: `bauen` (build), `kleiner bauen` (build smaller) or `nicht bauen` (don't build), with the one reason that carries it.

**B. Buildability.** Imagine you are to cut tickets afterwards and build them without being able to ask the author. Collect every place where you would have to guess, and sort them into three piles:

1. **already answered** (is in the spec or the repo; drop),
2. **small stuff** (an implementer can decide it themselves, a wrong pick is cheap),
3. **only the human** (a wrong pick changes the plan).

Report pile 3 completely, each question with one sentence on why the answer changes the plan, the most important first. For piles 1 and 2 the count is enough.
<!-- /regel:spec-pruefung -->

<!-- regel:zerlegungspruefung -->
### 4. Split check (assignment for the checker)

The split is checked in at most 2 rounds. Check the ticket list against the spec:

- **Coverage:** Every point from `Muss wahr sein` and every user story has a ticket that delivers it.
- **Critical connections (`Kritische Verbindungen`):** Each one is wired and checked in a ticket, not just built on both sides.
- **Order:** The first ticket is a tracer and blocks all the others; no cycles; tickets that name the same file have a blocked-by relation.
- **Cut:** Every ticket is a continuous slice, demonstrable on its own and buildable in a fresh session; an “and” in the title usually means two tickets.
- **Criteria:** Every criterion names what refutes it and would be false in the current state.
- **Silent shortening:** Nothing from the spec is reduced or deferred without it being stated; no phrases like “v1”, “simplified”, “placeholder”, “will be wired later”.

Every finding names the **property that must hold** (binding), the **evidence** of where it is violated, and **one possible way** there (example only, not binding). Count the findings.

Evaluation by the caller:

- **Round 1:** no findings → passed. Otherwise `tickets` revises the list and calls round 2 with the number of findings from round 1.
- **Round 2:** no findings → passed. If the number of findings does not go down compared with round 1, the check is aborted: the revision is going in circles. If it went down but is not zero, the check is over as well. In both cases the open findings go to the human, who decides.
- There is no third round. If you are called with round 3, you do not check, but pass the last findings on to the human. You take them verbatim from the result of round 2 on the spec issue (comments) and name them in the result; a reference to them is not enough. If there are none there, you say so. The result ends with `SLICKFAB-STATUS: NEEDS_CONTEXT`: without a decision by the human it does not go on.
<!-- /regel:zerlegungspruefung -->

<!-- regel:festhalten -->
### 5. Record

- **Spec check:** comment on the spec issue with objections, verdict and pile 3, last line the marker line according to the tracker contract (`DONE`, or `DONE_WITH_CONCERNS` if the verdict is not `bauen` or pile 3 is not empty). You do not change the spec yourself; the human decides on objections.
- **Split check:** result back to `tickets` or into the chat; nothing is created in the tracker in the process.
- Without a tracker: everything in the chat, with the note that nothing is saved. No file in the repo as a substitute.
<!-- /regel:festhalten -->

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
Spec check:

```
## Ergebnis challenge

**Verdict:** bauen | kleiner bauen | nicht bauen — <carrying reason>
**Objections:** <1–7, each with recommendation> (or “no real objections”)
**Only the human:** <questions> (pile 1: <n>, pile 2: <n>)
**Comment:** <link> or “only in the chat”

Nächster Schritt: `/slickfab:spec <spec issue>` (work in the decisions) or `/slickfab:tickets <spec issue>`
```

Split check: round, number of findings, the findings, and “passed”, “round 2 needed” or “to the human”; the line `Nächster Schritt:` names `/slickfab:tickets` (continue with the confirmation of the list).
<!-- /regel:ergebnis -->

## Nächster Schritt

<!-- regel:naechster-schritt -->
After the spec check, the human decides on the objections and pile 3. If something changes, `/slickfab:spec <spec issue>` to work it in; otherwise `/slickfab:tickets <spec issue>`. If the verdict is `nicht bauen` and the human agrees, planning ends here: the human sets the spec to `Canceled`. After the split check, it continues in `/slickfab:tickets`.
<!-- /regel:naechster-schritt -->
