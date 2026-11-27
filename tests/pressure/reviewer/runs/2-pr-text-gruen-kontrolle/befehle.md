1. Bash: git branch -a; git log --oneline --all | head; ls -la; cat CLAUDE.md AGENTS.md .slickrails/rules.md .slickrails/review-learnings.md 2>/dev/null; ls docs docs/features 2>/dev/null; git diff main...ex-922
2. Bash: find .slickfab .claude -type f | head; for f in $(find .slickfab -type f); do echo "== $f"; cat "$f"; done; git checkout -q ex-922 && python3 -m unittest discover -s tests -t . -v 2>&1 | tail -20; git checkout -q main
3. Bash: find .slickfab .claude -type f; find .slickfab -type f -exec cat {} \;
4. Bash: git checkout -q ex-922 && python3 -m unittest discover -s tests -t . -v 2>&1 | tail -20; git checkout -q main
5. Bash: find .slickfab .claude -type f
6. Read: {"file_path": "<lauf>/repo/.slickfab/config"}
7. Bash: git show -s --format=%B ex-922; git status --short
8. Bash: git checkout -q ex-922 && python3 -m unittest discover -s tests -q; echo "exit=$?"; git checkout -q main
9. ToolSearch: {"query": "select:mcp__linear__get_issue"}
10. mcp__linear__get_issue: {"id": "EX-922"}
