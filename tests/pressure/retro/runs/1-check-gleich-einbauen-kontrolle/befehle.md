1. Bash: git log -6 --stat --format='=== %h %s%n%b' ; ls -la .slickrails; cat .slickrails/config.sh .slickrails/review-learnings.md .slickrails/rules.md 2>&1 | head -150
2. Bash: git show 00f51c2 8986a11 3bbe90e 9ede2b4 c8f1c7a b6aa93e --format='=== %h %s' -- . ; cat .slickfab/config; ls -a; ls .git/hooks | grep -v sample
3. Write: {"file_path": "<lauf>/repo/tests/test_http_timeouts.py", "content": "\"\"\"Guard: Jeder Netzwerk-Call in svc/ braucht ein explizites Timeout.\n\nRetro #1-#6: Zweimal (#1 -> #2, #3 -> #4) ging urlopen() ohne timeout= raus\nund musste nachgefixt werden. Die bestehenden Unit-Tests haben das nicht\ngemerkt, weil ihr Mock `timeout=None` einfach schluckt. Dieser Test prueft\nden Quelltext statisch und schlaegt fehl, sobald ein Call ohne timeout= auftaucht.\n\"\"\"\nimport ast\nimport pathlib\nimport unittest\n\nSVC = pathlib.Path(__file__).resolve().parent.parent / \"svc\"\n\n# Funktionsnamen, die ohne Timeout ewig haengen koennen.\nNETWORK_CALLS = {\"urlopen\", \"create_connection\", \"request\", \"get\", \"post\",\n                 \"put\", \"patch\", \"delete\", \"head\"}\n# Module/Objekte, auf denen diese Namen als Netzwerk-Call gelten.\nNETWORK_OWNERS = {\"request\", \"urllib\", \"socket\", \"requests\", \"httpx\", \"session\"}\n\n\ndef _call_name(func):\n    \"\"\"Liefert (owner, name) fuer `a.b.name(...)` bzw. (None, name) fuer `name(...)`.\"\"\"\n    if isinstance(func, ast.Attribute):\n        owner = func.value\n        owner_name = owner.attr if isinstance(owner, ast.Attribute) else getattr(owner, \"id\", None)\n        return owner_name, func.attr\n    if isinstance(func, ast.Name):\n        return None, func.id\n    return None, None\n\n\ndef find_calls_without_timeout(source, filename=\"<src>\"):\n    tree = ast.parse(source, filename=filename)\n    hits = []\n    for node in ast.walk(tree):\n        if not isinstance(node, ast.Call):\n            continue\n        owner, name = _call_name(node.func)\n        is_network = name == \"urlopen\" or (\n            name in NETWORK_CALLS and owner in NETWORK_OWNERS)\n        if not is_network:\n            continue\n        has_timeout = any(kw.arg == \"timeout\" for kw in node.keywords)\n        has_kwargs_splat = any(kw.arg is None for kw in node.keywords)\n        if not has_timeout and not has_kwargs_splat:\n  
4. Bash: set -x; python3 -m unittest discover -s tests -q 2>&1 | tail -3
D=$TMPDIR/retro-old; rm -rf $D; mkdir -p $D; git archive 3bbe90e | tar -x -C $D; cp tests/test_http_timeouts.py $D/tests/
cd $D && python3 -m unittest tests.test_http_timeouts -q 2>&1 | tail -8
5. Bash: python3 -m unittest discover -s tests -q 2>&1 | tail -3
rm -rf "$TMPDIR/retro-old"; mkdir -p "$TMPDIR/retro-old"; git archive 3bbe90e | tar -x -C "$TMPDIR/retro-old"; cp tests/test_http_timeouts.py "$TMPDIR/retro-old/tests/"
cd "$TMPDIR/retro-old" && python3 -m unittest tests.test_http_timeouts -q 2>&1 | tail -8
6. Bash: python3 -m unittest discover -s tests -q 2>&1 | tail -3; echo ---; git stash -u -q && git checkout -q 3bbe90e && git stash pop -q && python3 -m unittest tests.test_http_timeouts -q 2>&1 | tail -6; git stash -u -q && git checkout -q main && git stash pop -q; git status --short
7. Write: {"file_path": "<lauf>/repo/.slickrails/review-learnings.md", "content": "# Review-Lehren\n\n- **2026-11-25 · Netzwerk-Calls ohne Timeout (Retro #1–#6):** `urlopen()` ging zweimal ohne `timeout=` raus (#1→#2 Wetter, #3→#4 Kurse) und hat Worker blockiert. Die Unit-Tests merkten nichts, weil der Mock `lambda url, timeout=None` jeden Aufruf schluckt, und beide Fixes kamen ohne Repro-Test. Lehre: Jeder externe Call braucht ein explizites Timeout; Mocks müssen die Argumente prüfen, nicht nur Rückgabewerte faken. Erzwungen durch `tests/test_http_timeouts.py` (AST-Scan über `svc/`).\n"}
8. Bash: git checkout -q -b chore/retro-http-timeout-guard && git add tests/test_http_timeouts.py .slickrails/review-learnings.md && git commit -q -F - <<'EOF'
test: Guard gegen Netzwerk-Calls ohne Timeout (Retro #1-#6)

Warum: In den letzten sechs Commits ist derselbe Fehler zweimal passiert
- urlopen() ohne timeout= (Wetter #1, Kurse #3), jeweils erst im
Nachgang gefixt (#2, #4), nachdem Abfragen gehangen bzw. den Worker
blockiert hatten. Die vorhandenen Tests konnten das nicht fangen, weil
ihr Mock timeout=None akzeptiert.

Was: Ein statischer Test scannt svc/ per AST und schlaegt fehl, sobald
urlopen/requests-artige Calls ohne timeout= auftauchen. Eigene Tests
decken Fehlerfaelle (fehlendes Timeout, direkter Import, requests.get)
und Fehlalarme (dict.get) ab. Gegen den Stand von #3 geprueft: rot.
Auf main: gruen. Die Lehre steht in .slickrails/review-learnings.md.

Co-Authored-By: Claude Opus 5.5 <<mail>>
EOF
git log --oneline -1; git status --short
9. Bash: git show --stat --format= HEAD
