---
name: prototype
description: Use when a question cannot be settled by asking, such as how something should look or whether a piece of logic or a state model feels right, or when someone says “quickly build a prototype”.
argument-hint: "[the open question]"
---

<!-- regel:einleitung -->
# prototype: throwaway code that answers a question

Goal: A question that cannot be settled by asking is decided afterwards. The prototype is a means to an end; it is thrown away, only the decision remains.

Answer in the user's language.
<!-- /regel:einleitung -->

## Wann

<!-- regel:wann -->
- Look and handling: “What should the page look like?”, “Which arrangement is better?”
- Logic and state: “Does this flow feel right?”, “What happens in this edge case?”
- Typically between `grill` and `spec`, when `grill` has marked a question as not settleable by asking.
- Not for questions that one sentence from the human settles (then `grill`), and not as the first building stage of the real feature.
<!-- /regel:wann -->

## Ablauf

<!-- regel:voraussetzung-pruefen -->
### 1. Check the precondition

- **The question:** Is there a concrete, open question in the conversation or in the argument? Phrase it in one sentence. If there is none, ask the human which question the prototype should answer. If it can be answered with one sentence, no prototype is needed: back to `/slickfab:grill`.
- **The repo:** It must be a Git repo with a clean working state (`git status` without changes). If changes are open, stop and say so. You do not move or hide anyone else's changes.

If you stop here, you end with the template “halt” (below).
<!-- /regel:voraussetzung-pruefen -->

<!-- regel:form-waehlen -->
### 2. Choose the form

The question determines the form:

- **Look → UI variants.** The default is 3, at most 5 clearly different variants on the same page, switchable via the URL parameter `?variant=` and a small floating bar. Preferably on an existing page with real data and the real frame, because variants in empty space all look good. Only if there is no suitable page, a new throwaway route following the project's routing convention.
- **Logic → throwaway script.** A file that pushes the flow through the difficult cases and prints the whole state after every step, or a single HTML file with buttons that a non-developer can operate too.

If it is unclear which form fits and the human is not there: if the question sits in a backend module, take logic; in a page or component, take UI. Write the assumption at the top of the prototype.
<!-- /regel:form-waehlen -->

<!-- regel:wegwerf-branch-anlegen -->
### 3. Create the throwaway branch

Remember the current branch. Then `git switch -c prototype/<short-slug>`. The whole prototype is created only on this throwaway branch; file and route names contain `prototype`, so that nobody mistakes it for real code.
<!-- /regel:wegwerf-branch-anlegen -->

<!-- regel:schnell-bauen -->
### 4. Build quickly

- Starts with one command from the project's task runner or by double-clicking the HTML file.
- State in memory; no database, unless the question is about exactly that (then a throwaway database with `prototype` in its name).
- State visible after every action or every variant switch.
- No tests, no error handling beyond what it takes to run, no abstractions.
<!-- /regel:schnell-bauen -->

<!-- regel:vorfuehren-und-urteil-holen -->
### 5. Demonstrate and get the verdict

Before you demonstrate, commit the prototype on the throwaway branch; the commit message names the question and the starting branch (the branch remembered in step 3). That way nothing lies around uncommitted if the session ends before the verdict. Before this commit, check with `git branch --show-current` that you are on `prototype/<slug>`. Otherwise you commit nothing and end with the template “halt”.

Tell the human how to start the prototype and what to compare. Wait for their verdict: which variant, which behavior, or what they take from several.

Close the demonstration with the template “awaiting verdict” (below, `NEEDS_CONTEXT`). If the session ends before the verdict, the human then knows how to continue. The repo stays on the throwaway branch so that they can start the prototype.
<!-- /regel:vorfuehren-und-urteil-holen -->

<!-- regel:festhalten-und-zurueck -->
### 6. Record and go back

- If the verdict comes in a new session (in the argument, with the question), the prototype is already committed. Then steps 2 to 5 are skipped: switch to the throwaway branch from the argument (`git switch prototype/<slug>`); you take the starting branch from the argument or from the prototype's commit message; then you only record. If one of the two is missing or the throwaway branch does not exist, stop and ask for it (template “branch question” below, `NEEDS_CONTEXT`).
- You never commit on a branch that does not start with `prototype/`.
- Commit on the throwaway branch (with an unchanged prototype with `--allow-empty`); the commit message names question and verdict.
- Back to the remembered branch (in a new session: the starting branch). Nothing from the prototype goes into the main branch, only the decision.
- If there already is a spec issue and a `.slickfab/config` (see `Vertrag`), write question, verdict and branch name as a comment there, with a marker line as in the section `Vertrag`. Otherwise both stay in the chat and travel along into the spec.
- You push the branch only if the human wants that.
<!-- /regel:festhalten-und-zurueck -->

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
## Ergebnis prototype

**Question:** <one sentence>
**Verdict:** <what the human decided>
**Branch:** prototype/<slug> (not merged) — back on <branch>
**Recorded:** <comment on issue …> or “in the chat”

Nächster Schritt: `/slickfab:spec`

SLICKFAB-STATUS: DONE
```

If the verdict raises new decisions, the next step is `/slickfab:grill`.

Before the verdict (step 5):

```
## Ergebnis prototype (awaiting verdict)

**Question:** <one sentence>
**Start:** <one command or double-click on …>
**Compare:** <what the human should look at or play through, one sentence per variant>
**Repo is on:** prototype/<slug> (prototype committed, created from <branch>) — back with `git switch <branch>`

Nächster Schritt: give the verdict here, then prototype records it; in a new session `/slickfab:prototype Question: <…> Verdict: <…> Branch: prototype/<slug> from <branch>`

SLICKFAB-STATUS: NEEDS_CONTEXT
```

Verdict in a new session, but branch missing (step 6):

```
## Ergebnis prototype (branch question)

**Question:** <one sentence>
**Verdict:** <as in the argument>
**Missing:** <throwaway branch | starting branch | `prototype/<slug>` does not exist>
**Nothing changed:** no commit, no branch switch; repo is on <branch>

Nächster Schritt: `/slickfab:prototype Question: <…> Verdict: <…> Branch: prototype/<slug> from <branch>`

SLICKFAB-STATUS: NEEDS_CONTEXT
```

Halt before building or before the commit:

```
## Ergebnis prototype (halt)

**Where:** <step>
**Reason:** <reason from the table>
**State:** repo on <branch>, no commit; <no branch created | uncommitted prototype files: …>

Nächster Schritt: <from the table>

SLICKFAB-STATUS: <NEEDS_CONTEXT | BLOCKED>
```

| Where | Reason | Next step | Status |
|---|---|---|---|
| Step 1 | no question | `/slickfab:prototype <question>` | `NEEDS_CONTEXT` |
| Step 1 | question can be settled with one sentence | `/slickfab:grill <question>` | `NEEDS_CONTEXT` |
| Step 1 | open changes in the repo | the human commits or sets them aside themselves, then `/slickfab:prototype <question>` again | `BLOCKED` |
| Step 5 | not on `prototype/<slug>` | the human checks the branch, then `/slickfab:prototype <question>` again | `BLOCKED` |

The marker line is the last line of your answer, outside any code block.
<!-- /regel:ergebnis -->

## Nächster Schritt

<!-- regel:naechster-schritt -->
`/slickfab:spec`: takes the verdict on as the human's decision. If the prototype raised new open questions, `/slickfab:grill` first.
<!-- /regel:naechster-schritt -->
