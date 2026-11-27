# Contributing

Thanks for helping. slickfab has no build step and no dependencies beyond Python 3.9 or newer and a POSIX shell.

## Running the tests

```sh
sh tests/run.sh          # full suite, about 7 minutes
sh tests/run.sh --fast   # skips the slowest process tests, under 90 seconds
```

- The full suite is the default and the one CI runs on every pull request (Python 3.9 and the current 3.x). A pull request needs it green.
- `--fast` is for quick feedback while you work. At the end it lists the modules it skipped; run the full suite before you open a pull request.
- The run prints a sign of life at least every 20 seconds, so a long test does not look like a hang. `SLICKFAB_TEST_HEARTBEAT=<seconds>` changes the interval.

## Pull requests

- Keep them small (under about 800 changed lines); the PR size check enforces this.
- Every behaviour change comes with a test that was red before the change and green after it.
- The steps, roles and docs are written in German; code comments and tests follow the language of the file you are changing.
