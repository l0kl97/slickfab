# Launch Playbook

Maintainer checklist for the public launch of slickfab. Nothing in this file is posted, submitted or opened
automatically; every channel step below is done by the maintainer by hand.

**Rule for this file:** every number about slickfab has a source in this repo. The path is in brackets behind it. A
number without a path does not belong here. Rules of outside channels (limits, waiting periods, update behaviour) are
not restated here; read them at the linked source on the day you use them.

## State (2026-11-27)

Done:

- The repo is public and is its own marketplace (`.claude-plugin/marketplace.json`, install commands in `README.md`).
- 13 steps and 7 roles are built (`README.md`, table "Steps" and "Seven roles"; `agents/` also holds the helper
  `docs-reader`). Manual and assisted mode are in use; autopilot is built and dry-run tested, not in production use
  (`README.md`, "Status and limits").
- Pressure scenarios: the roles held in 14 of 14 scenarios, the control in 2 of 14. The control is the same model with
  the old template for the four roles that had one (`tests/pressure/kontrolle/`) and with no instructions at all for
  debugger, verifier and retro, so 6 of the 14 control runs had no instructions. One run per arm. Scenarios,
  expectations and grading come from the same agent that ran them; every run is checked in so anyone can re-grade
  (`docs/features/pressure-szenarien.md`, "Entscheidungen" and "Grenzen"; runs under `tests/pressure/<role>/runs/`).
- Each feature has a dossier with its decisions, test path and limits (`docs/features/`).
- CI on pull requests: PR size guard at 800 changed lines and a security scan (`.github/workflows/pr-size.yml`,
  `.github/workflows/security.yml`).
- Plugin version is `0.1.0` (`.claude-plugin/plugin.json`).

Not done (see the checklist): no test suite in CI yet (`docs/features/slickfab-dispatch.md`, "Ruling
Post-Merge-Prüfung"), no release or changelog, no demo, plugin and marketplace descriptions are German.

### Numbers you may quote

| Claim | Number | Source |
|---|---|---|
| Steps / roles | 13 / 7 | `README.md` |
| Roles held under pressure, new vs. control | 14/14 vs. 2/14 | `docs/features/pressure-szenarien.md`, "Summe" |
| Control runs with old template / with no instructions | 8 / 6 | `docs/features/pressure-szenarien.md`, "Entscheidungen"; `tests/pressure/kontrolle/` |
| Cost of that whole pressure run (28 runs) | 8.93 USD (new 5.33, control 3.60) | `docs/features/pressure-szenarien.md`, "Summe" |
| Average cost per pressure run, new role vs. control | 0.38 vs. 0.26 USD | `docs/features/pressure-szenarien.md`, "Auswertung" |
| Scenarios where the new role was more expensive | 12 of 14 | `docs/features/pressure-szenarien.md`, "Auswertung" |
| Hand run `grill`, four calls | about 1.80 USD | `docs/features/plugin-tracer.md` |
| Hand run planning steps (`spec`, `challenge`, `tickets`) | about 0.75 USD | `docs/features/planungs-schritte.md` |
| Hand run `implement`, `debug`, `handoff`, six calls | about 0.80 USD | `docs/features/bau-schritte.md` |
| Hand run `review`, `verify`, `retro` | about 0.68 USD | `docs/features/pruef-schritte.md` |
| One `docs-lookup` call | 0.002 to 0.005 USD | `docs/features/docs-lookup.md` |
| PR size limit | 800 changed lines | `.github/workflows/pr-size.yml` |

Say it the way the sources do: the pressure numbers are one run per arm, graded by the same agent that ran them (not
by the maintainer, not by an independent grader), and the control is "old templates or no instructions", never just
"my old prompts". The cost numbers are hand runs in throwaway repos, not a benchmark.

## Before launch day

Release and CI

- [ ] One version in one place, a `CHANGELOG.md`, a tagged GitHub release with short notes.
- [ ] README says how to update the plugin. Take the commands and the auto-update behaviour for third-party
      marketplaces from the current Claude Code plugin docs, and run them once before writing them down.
- [ ] The test suite (`sh tests/run.sh`) runs in GitHub Actions on every pull request and on `main`, and is green.
- [ ] The test run prints progress, so a first-time contributor does not think it hangs.
- [ ] Branch protection on `main`: pull request required, CI required.

First impression for a stranger

- [ ] A fresh-clone run by someone who has never seen the repo has no findings of medium severity left open.
- [ ] `/slickfab:fab` explains itself in words and never cites internal table rows to the user.
- [ ] The status marker line at the end of `fab` does not read like an alarm when only setup is missing.
- [ ] `description` in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` is English.
- [ ] The README says early that steps answer in German, and lists prerequisites per mode
      (manual: nothing; assisted: Linear tools and `gh`; autopilot: Herdr plus factory config).
- [ ] Install instructions are the same in `README.md` and `docs/betriebsarten.md`.
- [ ] `claude plugin marketplace add l0kl97/slickfab` and `claude plugin install slickfab@slickfab` run once on a
      clean machine, exactly as written in the README.

Demo

- [ ] A short terminal recording of the flow (`fab` → `grill` → … → review) embedded in the README.
- [ ] One small example repo or a recorded walk-through a reader can follow without Linear.

Look and feel

- [ ] README checked on the real GitHub page on a phone (SVGs, table width).
- [ ] GitHub topics and the one-line repo description set; Discussions enabled.
- [ ] The good first issues below are written up and ready to open on launch day.

Decisions

- [ ] Launch day fixed, and whether slickfab launches together with slickrails or on its own (see "Joint or separate").
- [ ] Plugin name `slickfab` final. It is the slug for the official directory, settle it before submitting.

## Launch day (all channels the same day)

1. Morning: last `sh tests/run.sh`, CI green on `main`, release published, README install block copied and run once.
2. Story post on the maintainer's own blog goes live first; the other posts link to it.
3. Show HN (draft below). Post it yourself, stay in the thread for the first hours.
4. r/ClaudeAI (draft below). Read the subreddit rules for self-promotion the same day.
5. LinkedIn / X: demo first, story second, link third.
6. Pin a "Start here" Discussion with the three most likely questions: does it need Linear, does it work without
   slickrails, why German.

### Joint or separate

Open decision. Both variants in short:

- **Joint ("brakes and gas pedal"):** one story, two repos. slickrails (`README.md`, section "slickfab and
  slickrails") keeps AI-built code from getting through unchecked, slickfab moves the work forward. One Show HN about
  the pair, one blog post, both READMEs link each other. Upside: one stronger story, and slickfab's own limits
  (Linear only, Claude Code only) weigh less next to a tool that works with any repo. Downside: two release
  checklists must be green on the same day, and a thread splits its attention.
- **Separate:** one of the two first, the other later with its own day. If slickrails goes first, slickfab's hook is
  "the gas pedal for the brakes you already have". Which one is ready first is not recorded here; compare both
  checklists on the day you decide. Upside: each launch gets its own day, and slickfab can
  point at slickrails users. Downside: the second launch rarely gets the attention of the first.

## Week 1 rule

- Every issue, comment and Discussion gets an answer within 24 hours, also on the weekend. A short "seen, looking
  at it tomorrow" counts.
- Bugs get a red test first, then the fix (repo rule, `CLAUDE.md`). No hot fix on `main` without a pull request.
- Every question that came twice goes into the README or a docs page by the end of the week.
- Keep a list of what people asked for (other trackers, English steps, Codex). Do not promise dates in week 1.

## Show HN draft

> **Show HN: slickfab – a fixed process for building with Claude Code, checked by fresh agents**
>
> I build most of my software with Claude Code now. The code is rarely the problem. The process is: the spec stays
> in a chat nobody re-reads, I copy context from one session into the next, and "done, tests are green" arrives
> without proof that a test was ever red.
>
> slickfab is a Claude Code plugin that turns this into 13 fixed steps, from questioning an idea (`grill`) through
> spec, an outside check, tickets, TDD implementation and a separate review, to `verify` (is the goal of the spec
> really reached after the last merge?) and `retro` (recurring mistakes become proposed checks; nothing is applied
> without you). Linear is the single source
> of truth; there is no plan file in the repo. The checking steps run as fresh subagents that do not see the
> builder's report, and a role that would need a decision stops and says so instead of guessing.
>
> I tested the roles like code: 14 scenarios that push towards a shortcut (red pre-commit hook plus time pressure,
> a test in the way, "whatever, you decide"). The new roles held in 14 of 14. The control, the same model, held in
> 2 of 14; it got my old prompt where a role had one and no instructions at all where it had none (6 of the 14
> control runs). One run per arm, and the scenarios, expectations and grading came from the same agent that ran
> them, not from me or an independent grader. Every run is checked into the repo, so you can re-grade them. The new
> roles also cost more: about 0.38 vs 0.26 USD per run.
>
> Honest limits: Linear only, Claude Code only, the steps are written in German (README in English). The autopilot
> that starts roles in parallel is built and dry-run tested, but not in production use yet. It pairs with slickrails
> (git hooks, AI review on push, a stop gate) but works without it.
>
> MIT. https://github.com/l0kl97/slickfab

## r/ClaudeAI draft

> **I stopped trusting "done, all tests green" from Claude Code, so I built a process plugin where fresh agents check
> the work**
>
> The failure I kept hitting was not bad code. It was me as the bottleneck: copying the spec from chat into the next
> session, then reading the PR to find out whether the agent's "done" was true.
>
> slickfab splits the work into 13 steps (`/slickfab:grill`, `spec`, `challenge`, `tickets`, `implement`, `review`,
> `verify`, `retro`, ...). Handovers go through Linear, not through you. `implement` has to show the red and the green
> run per criterion in the PR. `review` runs in a fresh context with a mutation probe and never sees the builder's
> summary. You decide at gates: approving tickets, merging, anything labelled one-way (migration, auth, payment,
> deletion, deploy).
>
> I ran pressure scenarios against each role: 14/14 held vs 2/14 for the control, the same model with my old prompts
> or, for three roles, no instructions at all. One run per arm, graded by the same agent that ran them, all runs in
> the repo so you can re-grade.
>
> Limits up front: Linear only, Claude Code only, steps currently in German. The parallel autopilot is not in
> production use yet.
>
> MIT: https://github.com/l0kl97/slickfab. I would love to hear where the process gets in your way.

## Where to submit (prepared, not submitted)

### Own marketplace (launch day)

Nothing to submit. `.claude-plugin/marketplace.json` in the repo is enough; the README already has the two install
commands.

### Official directory: claude.ai/directory/manage

Needs a paid claude.ai plan. One plugin per submission; validate in the portal (Submit new → Plugin bundle → Source →
Validate), fix every blocking finding, push, re-validate. Source: Anthropic's pre-submission checklist
(claude.com/docs/plugins/pre-submission-checklist), read on 2026-11-27. Gone through against this repo:

- [x] `.claude-plugin/plugin.json` exists, with `name`, `version`, `description`, `author` and `license`.
- [x] Name `slickfab`: lowercase, no reserved word, nothing implying an official listing.
- [x] README and `LICENSE` file present.
- [x] File count and file sizes checked against the checklist's limits, no `.DS_Store`, no symlinks, no
      `.gitattributes` (checked with `git ls-files` on 2026-11-27; re-check against the limits in the checklist itself).
- [ ] **Open decision: the embedded hook starter.** The checklist lists an inline program such as `python3 -c` in a
      hook command as blocking. `hooks/hooks.json` starts both guards with an embedded `python3 -c '…'` on purpose:
      the starter is inline so it can never be missing, and the guards stay fail-closed
      (`docs/features/rollen-bash-waechter.md`, "Entscheidungen"). Whether this starter is changed for the directory
      submission is open. It is a deliberate trade-off and the decision is the maintainer's; no rebuild is recommended
      here, and it is not a good first issue.
- [ ] **Held for review: hooks run Python scripts.** Per the checklist, non-shell scripts run by hooks are held for
      a human reviewer. Describe in the README what each hook does, reads and blocks (`hooks/hooks.json`).
- [ ] Describe in the README everything the plugin runs or fetches: `docs-lookup` can fetch documentation from the
      network (`docs/features/docs-lookup.md`), roles call `gh` and the Linear tools.
- [ ] `description` in English (it is also what `/plugin` shows).
- [ ] Optional, not from the checklist: `claude plugin validate .` (run on 2026-11-27) also warns about a missing
      icon (`ICON_MISSING`; it says the icon is only taken over the first time the plugin is saved or submitted in the
      portal) and about hosts not declared under `network.hosts` in `.claude-plugin/plugin.json`.
- [ ] Recommended by the checklist: compare output with and without the plugin (`claude plugin eval`). The pressure
      scenarios are the closest thing today (`docs/features/pressure-szenarien.md`).
- [ ] Settle the name before submitting, raise `version` with every release.

### awesome-claude-code

Only through the web issue form "Recommend a resource" in hesreallyhim/awesome-claude-code, no pull request, not via
`gh`. The form sets eligibility rules (repo age, activity or stars); read them on the day and submit only once they
are met. One resource per submission, one-line description, no emoji, no sales pitch. Draft line:

> slickfab: a Claude Code plugin that runs a fixed 13-step process from idea to merged PR, with checking steps done
> by fresh subagents and Linear as the source of truth.

### claudemarketplaces.com

Third party, not Anthropic. Has `/submit` and `/list-your-tool`, sorted by installs and stars, shows sponsor slots.
Read the terms before listing; no paid slot without a separate decision.

## Good first issues (drafts, open on launch day)

Small, real gaps from the dossiers. Each should name the file and the test that proves it.

1. **Progress output for the test run.** `sh tests/run.sh` prints nothing until the end. Add progress dots or `-v`
   and a short note on the expected run time to the README.
2. **A fast test mode.** `tests/run.sh --fast` that skips the slow worktree and pressure-run tests, for a quick local
   loop before a full run.
3. **Plugin icon.** `claude plugin validate` warns `ICON_MISSING` (`docs/features/plugin-tracer.md`). Add a square PNG
   in the size the validator names and show it in the README. Best done before the first directory submission
   (see the validator note above).
4. **Let the role Bash guard accept `$?`.** Roles currently read exit codes via `|| echo …` because the guard rejects
   the variable (`docs/features/pressure-szenarien.md`, "Grenzen"). Allow `echo $?` and nothing more, with a test.
5. **Document how the reviewer writes its report file.** `skills/review` names `gh pr review … --body-file`, but not
   how the file is created without Write and without a heredoc (`docs/features/rollen-bash-waechter.md`, "Folgearbeit").
6. **Translate one step to English.** Start with `skills/fab/SKILL.md` as a pilot for an English version of the steps,
   keeping the rule references in `tests/golden/rules.md` in sync.
7. **Translate `docs/projektkonfiguration.md` to English.** It is the first page a new user needs after the README.
8. **Example `.slickfab/config` for a Node project.** `docs/projektkonfiguration.md` has the fields; add a copyable
   example with `CHECK_TEST="npm test"`.

## The case study (within a month)

Run slickfab on one real project for 30 days and publish what happened: tickets built, review findings per pull
request, how often a role stopped with `NEEDS_CONTEXT` or `BLOCKED`, what `retro` turned into checks, and what it
cost. Write it into the repo first, so every number has a source.
