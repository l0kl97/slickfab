import io, json, runpy, signal, sys
guard, roles = sys.argv[1], sys.argv[2].split(",")
try:
    data = sys.stdin.read()
    agent = json.loads(data).get("agent_type")
except Exception:
    sys.exit(0)
if not isinstance(agent, str) or agent not in roles:
    sys.exit(0)
def deny(why):
    sys.__stdout__.write(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "slickfab-Waechter nicht lauffaehig (" + why + "), im Zweifel abgelehnt"}}))
    sys.exit(0)
def late(*_):
    raise TimeoutError("Frist")
signal.signal(signal.SIGALRM, late)
signal.alarm(8)
out = io.StringIO()
sys.stdin, sys.stdout = io.StringIO(data), out
try:
    runpy.run_path(guard, run_name="__main__")
    code = 0
except SystemExit as e:
    code = e.code
except BaseException as e:
    deny(type(e).__name__)
signal.alarm(0)
if code not in (0, None):
    deny("Exit %s" % code)
sys.__stdout__.write(out.getvalue())
