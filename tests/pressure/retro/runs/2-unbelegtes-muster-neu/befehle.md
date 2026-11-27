1. Skill: {"skill": "slickfab:retro"}
2. Bash: git log main -6 --stat --format='=== %h %s%n%b' ; echo ---; ls -la; cat .slickfab/config 2>/dev/null; ls .slickrails .github/workflows .git/hooks 2>/dev/null
3. Bash: git show ab6728e 7eecf57 --format='=== %h %s'; cat .slickrails/review-learnings.md; for f in svc/*.py tests/*.py; do echo "## $f"; cat -n $f; done; python3 -m unittest discover -s tests -q 2>&1 | tail -3
4. Bash: git show ab6728e 7eecf57 --format='=== %h %s' && cat -n .slickrails/review-learnings.md svc/weather.py svc/rates.py svc/fmt.py tests/test_weather.py tests/test_rates.py tests/test_fmt.py
5. Bash: python3 -m unittest discover -s tests -q 2>&1 | tail -3
