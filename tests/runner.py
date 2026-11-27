"""Führt die Python-Unittests unter tests/ aus und meldet sich dabei regelmäßig.

Aufruf über tests/run.sh, nicht direkt: `python3 tests/runner.py [--fast]`.

- Lebenszeichen: Ein Hintergrund-Thread schreibt alle SLICKFAB_TEST_HEARTBEAT
  Sekunden (Standard 20) eine Zeile mit Stand und laufendem Test. Werkzeuge mit
  Ausgabe-Timeout und Menschen sehen so, dass der Lauf nicht hängt.
- `--fast` lässt die Module in SLOW_MODULES aus und nennt sie am Ende. Die volle
  Suite bleibt der Standard und die Pflicht in CI.
"""
import os
import sys
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_HEARTBEAT = 20

# Die langsamsten Module (Prozess-, Strg-C- und Dispatch-Tests), zusammen gut 80 % der Laufzeit.
SLOW_MODULES = (
    "test_dispatch_tick",
    "test_role_bash_guard",
    "test_worktree",
    "test_docs_lookup",
    "test_pressure_run",
    "test_guard_start",
)


def heartbeat_seconds():
    raw = os.environ.get("SLICKFAB_TEST_HEARTBEAT", "")
    if raw == "":
        return DEFAULT_HEARTBEAT
    if not raw.isdigit() or int(raw) < 1:
        raise ValueError("SLICKFAB_TEST_HEARTBEAT must be a whole number of seconds >= 1, got %r" % raw)
    return int(raw)


def iter_tests(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from iter_tests(item)
        else:
            yield item


def module_of(test):
    # Ladefehler (_FailedTest) tragen den Modulnamen als Testnamen.
    name = type(test).__module__
    if name == "unittest.loader":
        name = test.id().split(".")[-1]
    return name.split(".")[-1]


class Progress:
    """Gemeinsamer Stand zwischen Testlauf und Lebenszeichen-Thread."""

    def __init__(self, total):
        self.total = total
        self.done = 0
        self.current = ""
        self.lock = threading.Lock()


class ProgressResult(unittest.TextTestResult):
    progress = None

    def startTest(self, test):
        super().startTest(test)
        with self.progress.lock:
            self.progress.current = test.id()

    def stopTest(self, test):
        super().stopTest(test)
        with self.progress.lock:
            self.progress.done += 1


def beat(progress, interval, started, stop, stream):
    while not stop.wait(interval):
        with progress.lock:
            line = "... still running: %d/%d tests done after %ds, now %s" % (
                progress.done, progress.total, time.time() - started, progress.current)
        stream.write(line + "\n")
        stream.flush()


def main(argv):
    fast = False
    for arg in argv:
        if arg == "--fast":
            fast = True
        else:
            sys.stderr.write("runner.py: unknown option %s (known: --fast)\n" % arg)
            return 2
    try:
        interval = heartbeat_seconds()
    except ValueError as e:
        sys.stderr.write("runner.py: %s\n" % e)
        return 2

    suite = unittest.defaultTestLoader.discover(HERE, pattern="test_*.py", top_level_dir=HERE)
    tests, skipped = [], {}
    for test in iter_tests(suite):
        mod = module_of(test)
        if fast and mod in SLOW_MODULES:
            skipped[mod] = skipped.get(mod, 0) + 1
        else:
            tests.append(test)

    stream = sys.stderr
    progress = Progress(len(tests))
    ProgressResult.progress = progress
    stream.write("Running %d Python tests%s, sign of life every %ds\n" % (
        len(tests), " (--fast)" if fast else "", interval))
    stream.flush()

    started = time.time()
    stop = threading.Event()
    thread = threading.Thread(target=beat, args=(progress, interval, started, stop, stream), daemon=True)
    thread.start()
    try:
        result = unittest.TextTestRunner(stream=stream, verbosity=0, resultclass=ProgressResult).run(
            unittest.TestSuite(tests))
    finally:
        stop.set()
        thread.join()

    if fast:
        names = ", ".join("%s (%d)" % (m, skipped.get(m, 0)) for m in SLOW_MODULES)
        stream.write("--fast skipped %d tests in: %s. Full suite: sh tests/run.sh\n" % (
            sum(skipped.values()), names))
    stream.flush()
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
