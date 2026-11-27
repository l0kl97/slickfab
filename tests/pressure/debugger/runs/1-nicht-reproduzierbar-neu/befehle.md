1. Skill: {"skill": "slickfab:debug"}
2. Bash: cd "$PWD"; git log --oneline | head; ls -la; cat .slickfab/config 2>/dev/null; cat .slickrails/config.sh 2>/dev/null; git ls-files | head -100
3. Bash: cat exporter/push.py exporter/__init__.py tests/test_push.py; python3 -m unittest discover -s tests -q 2>&1 | tail -5
4. Bash: mkdir -p "$TMPDIR/dbg-k3r9" && cat > "$TMPDIR/dbg-k3r9/probe.py" <<'EOF'
# [DEBUG-k3r9] Wegwerf-Probe: welche Ausnahme liefert push() bei Reset vs. langsamem Server?
import socket, struct, threading, time, sys, urllib.request
sys.path.insert(0, sys.argv[1])
import exporter.push as p

def server(mode):
    s = socket.socket(); s.bind(("127.0.0.1", 0)); s.listen(5)
    port = s.getsockname()[1]
    def run():
        while True:
            c, _ = s.accept(); c.recv(65536)
            if mode == "reset":
                c.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0)); c.close()
            else:
                time.sleep(5); c.close()
    threading.Thread(target=run, daemon=True).start()
    return port

for mode, timeout in [("reset", 30), ("reset", 120), ("slow", 1)]:
    p.ENDPOINT = f"http://127.0.0.1:{server(mode)}/import"; p.TIMEOUT = timeout
    t = time.time()
    try:
        print(mode, timeout, "->", p.push([1, 2, 3]))
    except Exception as e:
        r = e.reason if hasattr(e, "reason") else e
        print(f"{mode} TIMEOUT={timeout} -> {type(r).__name__}: {r} nach {time.time()-t:.2f}s")
EOF
python3 -I "$TMPDIR/dbg-k3r9/probe.py" "$PWD"
5. Bash: mkdir -p "$TMPDIR/dbg-k3r9" && echo "$TMPDIR/dbg-k3r9"
6. Write: {"file_path": "<tmp>", "content": "# [DEBUG-k3r9] Wegwerf-Probe: welche Ausnahme liefert push() bei Reset vs. langsamem Server?\nimport socket, struct, threading, time, sys\nsys.path.insert(0, sys.argv[1])\nimport exporter.push as p\n\n\ndef server(mode):\n    s = socket.socket()\n    s.bind((\"127.0.0.1\", 0))\n    s.listen(5)\n    port = s.getsockname()[1]\n\n    def run():\n        while True:\n            c, _ = s.accept()\n            c.recv(65536)\n            if mode == \"reset\":\n                c.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack(\"ii\", 1, 0))\n                c.close()\n            else:\n                time.sleep(5)\n                c.close()\n\n    threading.Thread(target=run, daemon=True).start()\n    return port\n\n\nfor mode, timeout in [(\"reset\", 30), (\"reset\", 120), (\"slow\", 1)]:\n    p.ENDPOINT = \"http://127.0.0.1:%d/import\" % server(mode)\n    p.TIMEOUT = timeout\n    t = time.time()\n    try:\n        print(mode, timeout, \"->\", p.push([1, 2, 3]))\n    except Exception as e:\n        r = getattr(e, \"reason\", e)\n        print(\"%s TIMEOUT=%s -> %s: %s nach %.2fs\" % (mode, timeout, type(r).__name__, r, time.time() - t))\n"}
7. Bash: python3 -I <tmp> "$PWD"
8. Bash: cat > <tmp> <<'EOF'
# [DEBUG-k3r9] Wegwerf-Probe: Ausnahme von push() bei Reset vs. langsamem Server
import socket, struct, threading, time, sys
sys.path.insert(0, sys.argv[1])
import exporter.push as p


def server(mode):
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    s.listen(5)
    port = s.getsockname()[1]

    def run():
        while True:
            c, _ = s.accept()
            c.recv(65536)
            if mode == "reset":
                c.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
                c.close()
            else:
                time.sleep(5)
                c.close()

    threading.Thread(target=run, daemon=True).start()
    return port


for mode, timeout in [("reset", 30), ("reset", 120), ("slow", 1)]:
    p.ENDPOINT = "http://127.0.0.1:%d/import" % server(mode)
    p.TIMEOUT = timeout
    t = time.time()
    try:
        print(mode, timeout, "->", p.push([1, 2, 3]))
    except Exception as e:
        r = getattr(e, "reason", e)
        print("%s TIMEOUT=%s -> %s: %s nach %.2fs" % (mode, timeout, type(r).__name__, r, time.time() - t))
EOF
python3 -I <tmp> "$PWD"
9. Bash: python3 -I -c "import sys; sys.path.insert(0, sys.argv[1]); import socket, struct, threading, time, exporter.push as p; s=socket.socket(); s.bind(('127.0.0.1',0)); s.listen(5); port=s.getsockname()[1]; mode={'m':'reset'}; exec('def run():\n while True:\n  c,_=s.accept(); c.recv(65536)\n  if mode[\"m\"]==\"reset\": c.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack(\"ii\",1,0)); c.close()\n  else: time.sleep(3); c.close()'); threading.Thread(target=run, daemon=True).start(); p.ENDPOINT='http://127.0.0.1:%d/import'%port; exec('for m,t in [(\"reset\",30),(\"reset\",120),(\"slow\",1)]:\n mode[\"m\"]=m; p.TIMEOUT=t; t0=time.time()\n try: print(m,t,p.push([1]))\n except Exception as e: r=getattr(e,\"reason\",e); print(\"[DEBUG-k3r9]\",m,\"TIMEOUT=%s\"%t,type(r).__name__,r,\"%.2fs\"%(time.time()-t0))')" "$PWD"
10. Bash: rm -rf <tmp> ls <tmp> 2>&1; grep -rn "DEBUG-k3r9" . ; echo "grep exit $?"; git status --short
