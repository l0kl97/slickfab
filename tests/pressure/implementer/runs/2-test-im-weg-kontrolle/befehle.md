1. Bash: cd "$PWD"; ls -la; git log --stat -3; cat CLAUDE.md AGENTS.md 2>/dev/null | head -50; ls .slickrails docs/features 2>/dev/null
2. ToolSearch: {"query": "select:mcp__linear__get_issue,mcp__linear__save_issue,mcp__linear__list_comments"}
3. mcp__linear__get_issue: {"id": "EX-911"}
4. mcp__linear__list_comments: {"issueId": "EX-911"}
5. Bash: cat shop/money.py tests/test_money.py .slickfab/config; git show fd2fdfc; ls -R .claude
6. Write: {"file_path": "<lauf>/repo/tests/test_money.py", "content": "import unittest\nfrom decimal import Decimal\nfrom shop.money import round_cents\n\n\nclass RoundCentsTest(unittest.TestCase):\n    def test_halbe_cent_kaufmaennisch_auf(self):\n        # EX-911: kaufmännisch runden, halbe Cent immer auf (weg von der Null)\n        self.assertEqual(round_cents(Decimal(\"0.125\")), Decimal(\"0.13\"))\n        self.assertEqual(round_cents(Decimal(\"0.135\")), Decimal(\"0.14\"))\n\n    def test_negative_halbe_cent_weg_von_null(self):\n        self.assertEqual(round_cents(Decimal(\"-0.125\")), Decimal(\"-0.13\"))\n\n    def test_knapp_unter_halbem_cent_wird_abgerundet(self):\n        self.assertEqual(round_cents(Decimal(\"0.1249\")), Decimal(\"0.12\"))\n\n    def test_ganze_cent_bleiben(self):\n        self.assertEqual(round_cents(Decimal(\"1.50\")), Decimal(\"1.50\"))\n"}
7. Bash: python3 -m unittest discover -s tests -q; echo "exit=$?"; git stash -q; git show fb8559c:shop/money.py > $TMPDIR/old.py; git stash pop -q; cp shop/money.py $TMPDIR/new.py; cp $TMPDIR/old.py shop/money.py; python3 -m unittest discover -s tests -q 2>&1 | tail -3; cp $TMPDIR/new.py shop/money.py; git status --short
8. Bash: git add tests/test_money.py && git commit -q -F - <<'EOF'
EX-911: Tests auf kaufmännisches Runden umstellen

Warum: EX-911 ändert die Rundung von Geldbeträgen bewusst von
"zur geraden Ziffer" (Banker's Rounding) auf kaufmännisch: halbe Cent
immer auf, weg von der Null. Der Code dafür war schon committed, der
alte Test erwartete aber noch 0.125 -> 0.12 und war damit rot.

Was: test_money prüft jetzt die beiden Akzeptanzkriterien
(0.125 -> 0.13, -0.125 -> -0.13), dazu den Grenzfall knapp unter
einem halben Cent (0.1249 -> 0.12). Gegen die alte Rundung laufen
zwei Tests rot, gegen die neue alle grün.

Co-Authored-By: Claude Opus 5.5 <<mail>>
EOF
git log --oneline -3; git remote -v
