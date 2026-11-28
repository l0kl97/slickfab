1. Skill: {"skill": "slickfab:retro"}
2. Bash: git log main -6 --stat --format='=== %h %s%n%b' ; ls -a; cat .slickfab/config 2>/dev/null; ls .slickrails .github/workflows .husky 2>/dev/null
3. Bash: git show 91ec2fe 5253516 --format='=== %h' ; cat svc/*.py tests/*.py .slickrails/review-learnings.md; git remote -v; ls .claude; python3 -m unittest discover -s tests -q 2>&1 | tail -3
