---
name: grill
description: Use when a plan, an idea or a feature request should be probed for open decisions before the spec, or when someone says “grill me”, “interview me” or “stress-test”.
argument-hint: "[topic or plan]"
---

<!-- regel:einleitung -->
# grill: interview in rounds

Goal: At the end, no decision is silently assumed anymore. The human makes the decisions only they can make; everything else you settle yourself and disclose.

Answer in the user's language.
<!-- /regel:einleitung -->

## Wann

<!-- regel:wann -->
- Before a spec, when a request still has gaps: for whom, what for, how success is recognized, which constraint binds.
- When someone wants a plan checked before it is built.
- Not for unambiguous small tasks (renaming, typos) and not without a human who answers. If you run without a human (autopilot, CI), report the open decisions as blockers instead of guessing them.
<!-- /regel:wann -->

## Ablauf

<!-- regel:lage-erkunden-bevor-du-fragst -->
### 1. Explore the situation before you ask

You fetch facts yourself, never the human. Everything that is in the repo or the environment (language, frameworks, folder structure, existing tests, existing specs, `GLOSSARY.md`, `docs/adr/`, `CLAUDE.md`), you look up. For more than a few files you send off a subagent with a fresh context and have it summarize the result briefly. Questions that depend on a running exploration wait; the others you already ask.

A question whose answer is in the repo is a mistake. If the answer is there, state it as a finding (“The project uses Python 3.12, so …”) and ask only what remains to be decided from it.
<!-- /regel:lage-erkunden-bevor-du-fragst -->

<!-- regel:entscheidungsbaum-aufbauen -->
### 2. Build the decision tree

Every decision can lead to further ones. The **front** is all decisions whose prerequisites are settled. If a question depends on another one that is still open in this round, it belongs in a later round.
<!-- /regel:entscheidungsbaum-aufbauen -->

<!-- regel:jede-frage-einordnen -->
### 3. Classify every question

| Kind | Example | Who decides |
|---|---|---|
| **Product question** (value, audience, scope, behavior, taste) | Who may export? | human |
| **Hard to reverse** (data format on disk/on the wire, public API, database schema that others read, binding to an external service, deletion of data) | What format does the export file have that customers archive? | human |
| **Reversible, technical** (one file, one function, swappable behind a stable interface) | Which internal helper function, which variable name? | you, with an entry under “Decided autonomously” |

If you are unsure whether something is hard to reverse and cannot name a concrete migration or a concrete broken contract, it counts as reversible. Whoever turns everything into a one-way door creates question fatigue.
<!-- /regel:jede-frage-einordnen -->

<!-- regel:eine-runde-stellen -->
### 4. Ask one round

Ask the whole front at once, numbered Q1, Q2, … Every question has a recommendation and is phrased so that “yes” accepts the recommendation. For hard-to-reverse questions you state in one sentence what a way back would cost.

```
**Q1 – <title>** <question, with options A/B/C if any>
→ Recommendation: <your answer, one sentence why>

**Q2 – <title>** (hard to reverse: <what a way back costs>) <question>
→ Recommendation: <…>
```

Then you wait for the answers. No upper limit on rounds; the round is as large as the front.
<!-- /regel:eine-runde-stellen -->

<!-- regel:antworten-auswerten -->
### 5. Evaluate the answers

- “yes”, “fine”, “Q1 yes” accepts the recommendation.
- An answer of their own replaces the recommendation.
- **“don't care”, “you decide”, “as you like”, silence on a question:**
  - For reversible technical questions: decide yourself and enter it under “Decided autonomously”.
  - For product questions and hard-to-reverse questions this is **not consent**. Ask the same decision again in the next round, narrowed to two concrete options with one consequence each, and wait. Do not move on as if the human had agreed.
- Every answer shifts the front: new questions become free, others drop away. Recompute the front and ask the next round.
<!-- /regel:antworten-auswerten -->

<!-- regel:nebenbei-mitschreiben -->
### 6. Take notes along the way

- **Glossary:** If a project-specific term comes up or two words are used for the same thing, enter it immediately in `GLOSSARY.md` in the repo root (create it if it does not exist): term in bold, one or two sentences on what it is, below it `_Not:_` with the rejected synonyms. General programming terms do not belong in it.
- **ADR:** An ADR is due if both apply: (1) The decision is hard to reverse. (2) Without a reason, a later reader would find it surprising or reopen it. If both apply, you create the ADR; if one does not apply, you create none. You check this for every decision of this round and for every earlier one passed in as text that has no ADR yet, not by gut feeling. The ADR lives under `docs/adr/NNNN-slug.md` (next free number, create the folder only with the first ADR), a title and one to three sentences: situation, decision, reason.

Both are reversible and need no question back.
<!-- /regel:nebenbei-mitschreiben -->

<!-- regel:abschluss -->
### 7. Wrap-up

You are done when the front is empty: every branch visited, nothing silently assumed, and you could predict the human's next answers. Then you summarize (see Ergebnis) and ask whether the shared understanding is right. Only after a clear yes is the step done. You build nothing in this step.
<!-- /regel:abschluss -->

## Ergebnis

<!-- regel:ergebnis -->
A summary in the chat, in this form:

```
## Ergebnis grill

**Decided by the human**
- <decision> (Q<n>)

**Decided autonomously**
- <decision> — <why> — reversible because <…>
(or: “none”)

**Out of scope**
- <what is explicitly not built>

**Changed files:** GLOSSARY.md, docs/adr/… (or “none”)

Nächster Schritt: `/slickfab:spec`
```

The list “Decided autonomously” is always there, even when it is empty, so that the human does not overlook anything hidden.
<!-- /regel:ergebnis -->

## Nächster Schritt

<!-- regel:naechster-schritt -->
`/slickfab:spec`: writes the spec from this conversation without interviewing again. If questions remained open that cannot be settled by asking (look, handling), `/slickfab:prototype` first.
<!-- /regel:naechster-schritt -->
