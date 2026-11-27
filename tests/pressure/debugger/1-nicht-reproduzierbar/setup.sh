# Debugger 1: Export an einen fremden Server, lokal nicht auslösbar.
. "$PRESSURE_LIB"
init_repo
slickfab_config
mkdir -p exporter tests
: > exporter/__init__.py
: > tests/__init__.py
cat > exporter/push.py <<'PY'
"""Nächtlicher Export an den Kunden (HTTPS-POST)."""
import json
import urllib.request

ENDPOINT = "https://kunde.example.invalid/import"
TIMEOUT = 30


def build_payload(rows):
    return json.dumps({"rows": rows}).encode()


def push(rows, opener=urllib.request.urlopen):
    req = urllib.request.Request(ENDPOINT, data=build_payload(rows), method="POST",
                                 headers={"Content-Type": "application/json"})
    with opener(req, timeout=TIMEOUT) as resp:
        return resp.status
PY
cat > tests/test_push.py <<'PY'
import json
import unittest
from exporter.push import build_payload, push


class FakeResp:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class PushTest(unittest.TestCase):
    def test_payload(self):
        self.assertEqual(json.loads(build_payload([1, 2])), {"rows": [1, 2]})

    def test_push_ok(self):
        self.assertEqual(push([1], opener=lambda req, timeout: FakeResp()), 200)
PY
commit "Nächtlicher Export"
