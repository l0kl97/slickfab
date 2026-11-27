1. Skill: {"skill": "slickfab:retro"}
2. Bash: git log --oneline -n 10 main && git status --short | head && ls -a && ls .slickrails 2>/dev/null
3. Bash: cat .slickfab/config; echo ---; for f in .slickrails/*; do echo "== $f"; cat "$f"; done; echo ---; ls -R svc tests .claude; ls .git/hooks | grep -v sample; echo ---; git log -p -n 6 main --stat
4. Bash: cat .slickfab/config .slickrails/review-learnings.md; ls -a .slickrails .claude svc tests; git log -p -n 6 main --stat
