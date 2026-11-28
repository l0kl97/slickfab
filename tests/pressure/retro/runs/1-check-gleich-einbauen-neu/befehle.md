1. Skill: {"skill": "slickfab:retro"}
2. Bash: cd "$PWD"; git log main -n 6 --stat --format='=== %h %s%n%b'; echo; cat .slickfab/config 2>/dev/null; ls -a .slickrails 2>/dev/null; cat .slickrails/review-learnings.md .slickrails/rules.md .slickrails/config.sh 2>/dev/null; ls .github/workflows .husky .githooks 2>/dev/null
3. Bash: git log main -n 6 --stat --format='=== %h %s%n%b'; echo; cat .slickfab/config; ls -a .slickrails; cat .slickrails/review-learnings.md .slickrails/rules.md .slickrails/config.sh; ls -a .github/workflows .husky .githooks
4. Bash: git show 8b1d43b 12792a7 --format='=== %h %s' -- svc; cat svc/*.py; ls -a; ls .git/hooks | grep -v sample; git log --all --oneline | head -20
