# Project configuration `.slickfab/config`

Every repo in which slickfab steps use the tracker has a file `.slickfab/config` in the repo root. It says where specs and tickets live and which commands run the checks. It is checked in and holds no credentials.

This file is the source. The steps carry the parts they need verbatim in their `SKILL.md` (blocks `<!-- vertrag:config-… -->`); `tests/test_contract_blocks.py` checks that the copies are identical.

## Format

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

## Check commands with slickrails

<!-- vertrag:config-slickrails -->
If the repo has `.slickrails/config.sh`, the check commands come from there: all non-empty `CHECK_*` values, the same way slickrails uses them in its hooks. `CHECK_*` entries in `.slickfab/config` are then not used; if they hold different values, the step names the contradiction once and follows slickrails. `.slickrails/config.sh` is also read only as text.

Answer in the user's language.
<!-- /vertrag:config-slickrails -->

The runtime tools are narrower than the steps: `runtime/herdr/slickfab-worktree` (the baseline of a new worktree, and through it the dispatcher's post-merge check) reads only `CHECK_TYPECHECK` and `CHECK_TEST` from `.slickrails/config.sh` and runs the non-empty ones. Other `CHECK_*` keys, such as `CHECK_LINT_STAGED` or `CHECK_PREPUSH_REVIEW`, are not run there.

## When the configuration is missing

<!-- vertrag:config-fehlt -->
If `.slickfab/config` is missing, a required value is missing, or `TRACKER=` names an unknown tracker, the step reports exactly that (which file, which key) and stops at the point where it would need the tracker. It writes no plan, ledger or state file and no ticket list into the repo as a substitute; whatever it has already worked out, it shows in the chat.

It offers to create `.slickfab/config` and shows the content with the values it found in the repo or in the tracker. The file is created only once the human has confirmed team and project.

Answer in the user's language.
<!-- /vertrag:config-fehlt -->
