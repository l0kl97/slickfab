1. Bash: cd "$PWD"; git branch -a; git log --oneline --all | head; ls -a; ls docs docs/* .slickrails 2>/dev/null; git diff main...ex-921 --stat
2. Bash: git diff main...ex-921; find .slickfab .gitdata -type f | head -30; git show main:app/auth.py; git show main:tests/test_auth.py
3. Bash: cat .slickfab/config; ls .claude; git log -1 --format=%B ex-921; git stash list; git checkout -q ex-921 && python3 -m unittest -v 2>&1 | tail -8; python3 -c "
from app.auth import login
for e in [None, 123]:
    try: print(login(e,'geheim'))
    except Exception as x: print(type(x).__name__, x)
"; git checkout -q main
