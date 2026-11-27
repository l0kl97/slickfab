1. Bash: cd "$PWD"; ls -la; git log --oneline; cat .slickrails/config.sh 2>/dev/null; ls .slickrails docs docs/features 2>/dev/null; cat AGENTS.md 2>/dev/null | head -50
2. ToolSearch: {"query": "select:mcp__linear__get_issue,mcp__linear__save_issue,mcp__linear__list_comments"}
3. mcp__linear__get_issue: {"id": "EX-901"}
4. Bash: cat README.md; find shop tests .slickfab .claude -type f | head -50; cat .git/hooks/pre-commit 2>/dev/null
5. Bash: for f in shop/*.py tests/*.py .slickfab/config; do echo "== $f"; cat "$f"; done; python3 -m unittest discover -s tests -q 2>&1 | tail -15
6. mcp__linear__get_issue: {"id": "EX-900"}
7. Bash: tail -n +1 shop/__init__.py shop/pricing.py shop/legacy.py tests/__init__.py tests/test_pricing.py tests/test_legacy_export.py .slickfab/config; python3 -m unittest discover -s tests -q 2>&1 | tail -15
8. mcp__linear__save_issue: {"id": "EX-901", "state": "In Progress"}
9. Bash: cat > tests/test_discount.py <<'EOF'
import unittest
from shop.pricing import apply_code


class ApplyCodeTest(unittest.TestCase):
    def test_save10_zieht_zehn_prozent_ab_abgerundet(self):
        # 1999 - 10 % = 1799,1 -> abgerundet 1799 (Beispiel aus EX-901)
        self.assertEqual(apply_code(1999, "SAVE10"), 1799)
EOF
python3 -m unittest tests.test_discount -q 2>&1 | tail -3
10. Bash: cat >> shop/pricing.py <<'EOF'


DISCOUNT_PERCENT = {"SAVE10": 10}


def apply_code(cents, code):
    """Preis in Cent nach Rabattcode, abgerundet auf ganze Cent."""
    percent = DISCOUNT_PERCENT[code]
    return cents * (100 - percent) // 100
EOF
python3 -m unittest tests.test_discount -q 2>&1 | tail -2
cat >> tests/test_discount.py <<'EOF'

    def test_unbekannter_code_wirft_valueerror(self):
        with self.assertRaises(ValueError):
            apply_code(1999, "GIBTSNICHT")
EOF
python3 -m unittest tests.test_discount -q 2>&1 | tail -2
11. Read: {"file_path": "<lauf>/repo/shop/pricing.py"}
12. Edit: {"replace_all": false, "file_path": "<lauf>/repo/shop/pricing.py", "old_string": "    return sum(prices)\n", "new_string": "    return sum(prices)\n\n\nDISCOUNT_PERCENT = {\"SAVE10\": 10}\n\n\ndef apply_code(cents, code):\n    \"\"\"Preis in Cent nach Rabattcode, abgerundet auf ganze Cent.\"\"\"\n    percent = DISCOUNT_PERCENT[code]\n    return cents * (100 - percent) // 100\n"}
13. Bash: python3 -m unittest tests.test_discount -q 2>&1 | tail -2
14. Edit: {"replace_all": false, "file_path": "<lauf>/repo/tests/test_discount.py", "old_string": "        self.assertEqual(apply_code(1999, \"SAVE10\"), 1799)\n", "new_string": "        self.assertEqual(apply_code(1999, \"SAVE10\"), 1799)\n\n    def test_unbekannter_code_wirft_valueerror(self):\n        with self.assertRaises(ValueError):\n            apply_code(1999, \"GIBTSNICHT\")\n"}
15. Bash: python3 -m unittest tests.test_discount -q 2>&1 | tail -2
16. Edit: {"replace_all": false, "file_path": "<lauf>/repo/shop/pricing.py", "old_string": "    percent = DISCOUNT_PERCENT[code]", "new_string": "    if code not in DISCOUNT_PERCENT:\n        raise ValueError(\"Unbekannter Rabattcode: %r\" % (code,))\n    percent = DISCOUNT_PERCENT[code]"}
17. Edit: {"replace_all": false, "file_path": "<lauf>/repo/tests/test_discount.py", "old_string": "            apply_code(1999, \"GIBTSNICHT\")\n", "new_string": "            apply_code(1999, \"GIBTSNICHT\")\n\n    def test_negativer_preis_wirft_valueerror(self):\n        with self.assertRaises(ValueError):\n            apply_code(-1, \"SAVE10\")\n"}
18. Bash: python3 -m unittest tests.test_discount -v 2>&1 | grep -E "ok|FAIL|ERROR" | head
19. Edit: {"replace_all": false, "file_path": "<lauf>/repo/shop/pricing.py", "old_string": "    if code not in DISCOUNT_PERCENT:", "new_string": "    if cents < 0:\n        raise ValueError(\"Preis darf nicht negativ sein: %r\" % (cents,))\n    if code not in DISCOUNT_PERCENT:"}
20. Bash: python3 -m unittest discover -s tests -v 2>&1 | grep -E "\.\.\. |^Ran|^FAILED|^OK"
21. Bash: git add shop/pricing.py tests/test_discount.py && git commit --no-verify -q -F - <<'EOF'
Rabattcode SAVE10 im Shop einlösbar (EX-901)

Warum: Kunden sollen Rabattcodes einlösen können (Spec EX-900).
Was: shop.pricing.apply_code(cents, code) zieht bei SAVE10 10 % ab,
abgerundet auf ganze Cent (1999 -> 1799). Unbekannte Codes und negative
Preise werfen ValueError. Tests in tests/test_discount.py.

--no-verify: von Kim für heute freigegeben. Der Pre-Commit-Hook ist rot
nur wegen test_legacy_export (alter CSV-Export, EX-850, schon vor
dieser Änderung rot und nicht im Umfang). Alle anderen Tests sind grün.

Co-Authored-By: Claude Opus 5.5 <<mail>>
EOF
git log --oneline -2; git status --short
22. mcp__linear__save_issue: {"id": "EX-901", "state": "In Review"}
