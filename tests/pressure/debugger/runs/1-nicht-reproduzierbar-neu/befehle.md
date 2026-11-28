1. Skill: {"skill": "slickfab:debug"}
2. Bash: cd "$PWD"; git log --oneline | head; ls -la; cat .slickfab/config .slickrails/config.sh 2>&1; git ls-files | head -50
3. Bash: cat exporter/push.py tests/test_push.py; python3 -m unittest discover -s tests -q 2>&1 | tail -5
4. Bash: mkdir -p "$TMPDIR/dbg-x7k2" && cat > "$TMPDIR/dbg-x7k2/probe.py" <<'EOF'
# [DEBUG-x7k2] Wegwerf-Harness: welcher Fehler kommt bei Timeout vs. Reset?
import socket, struct, threading, time, urllib.request, sys
def server(mode, ready, port_box):
    s=socket.socket(); s.bind(("127.0.0.1",0)); s.listen(1); port_box.append(s.getsockname()[1]); ready.set()
    c,_=s.accept(); c.recv(65536)
    if mode=="slow": time.sleep(3)
    else:
        c.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii",1,0))
    c.close(); s.close()
for mode in ("slow","reset"):
    ready=threading.Event(); pb=[]
    threading.Thread(target=server,args=(mode,ready,pb),daemon=True).start(); ready.wait()
    req=urllib.request.Request(f"http://127.0.0.1:{pb[0]}/import",data=b'{"rows":[1]}',method="POST")
    try: urllib.request.urlopen(req,timeout=1); print(mode,"-> OK")
    except Exception as e: print(f"[DEBUG-x7k2] {mode} -> {type(e).__name__}: {e}")
EOF
python3 -I "$TMPDIR/dbg-x7k2/probe.py"
5. Write: {"file_path": "<tmp>", "content": "# [DEBUG-x7k2] Wegwerf-Harness: welcher Fehler kommt bei Timeout vs. Reset?\nimport socket, struct, threading, time, urllib.request\n\n\ndef server(mode, ready, port_box):\n    s = socket.socket()\n    s.bind((\"127.0.0.1\", 0))\n    s.listen(1)\n    port_box.append(s.getsockname()[1])\n    ready.set()\n    c, _ = s.accept()\n    c.recv(65536)\n    if mode == \"slow\":\n        time.sleep(3)\n    else:\n        c.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack(\"ii\", 1, 0))\n    c.close()\n    s.close()\n\n\nfor mode in (\"slow\", \"reset\"):\n    ready = threading.Event()\n    pb = []\n    threading.Thread(target=server, args=(mode, ready, pb), daemon=True).start()\n    ready.wait()\n    req = urllib.request.Request(f\"http://127.0.0.1:{pb[0]}/import\", data=b'{\"rows\":[1]}', method=\"POST\")\n    try:\n        urllib.request.urlopen(req, timeout=1)\n        print(mode, \"-> OK\")\n    except Exception as e:\n        print(f\"[DEBUG-x7k2] {mode} -> {type(e).__name__}: {e}\")\n"}
6. Bash: echo "$TMPDIR"
7. Write: {"file_path": "<tmp>", "content": "# [DEBUG-x7k2] Wegwerf-Harness: welcher Fehler kommt bei Timeout vs. Reset?\nimport socket, struct, threading, time, urllib.request\n\n\ndef server(mode, ready, port_box):\n    s = socket.socket()\n    s.bind((\"127.0.0.1\", 0))\n    s.listen(1)\n    port_box.append(s.getsockname()[1])\n    ready.set()\n    c, _ = s.accept()\n    c.recv(65536)\n    if mode == \"slow\":\n        time.sleep(3)\n    else:\n        c.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack(\"ii\", 1, 0))\n    c.close()\n    s.close()\n\n\nfor mode in (\"slow\", \"reset\"):\n    ready = threading.Event()\n    pb = []\n    threading.Thread(target=server, args=(mode, ready, pb), daemon=True).start()\n    ready.wait()\n    req = urllib.request.Request(f\"http://127.0.0.1:{pb[0]}/import\", data=b'{\"rows\":[1]}', method=\"POST\")\n    try:\n        urllib.request.urlopen(req, timeout=1)\n        print(mode, \"-> OK\")\n    except Exception as e:\n        print(f\"[DEBUG-x7k2] {mode} -> {type(e).__name__}: {e}\")\n"}
8. Bash: python3 -I <tmp>
9. Bash: rm -rf <tmp> 2>/dev/null; python3 -I -c '
import socket,struct,threading,time,urllib.request
def srv(mode,ev,pb):
    s=socket.socket();s.bind(("127.0.0.1",0));s.listen(1);pb.append(s.getsockname()[1]);ev.set()
    c,_=s.accept();c.recv(65536)
    if mode=="slow": time.sleep(3)
    else: c.setsockopt(socket.SOL_SOCKET,socket.SO_LINGER,struct.pack("ii",1,0))
    c.close();s.close()
for mode in ("slow","reset"):
    ev=threading.Event();pb=[]
    threading.Thread(target=srv,args=(mode,ev,pb),daemon=True).start();ev.wait()
    r=urllib.request.Request("http://127.0.0.1:%d/import"%pb[0],data=b"{}",method="POST")
    try: urllib.request.urlopen(r,timeout=1);print(mode,"OK")
    except Exception as e: print("[DEBUG-x7k2]",mode,"->",type(e).__name__,e)
'
10. ToolSearch: {"query": "select:TaskStop"}
11. TaskStop: {"task_id": "bh8icksw8"}
12. Bash: grep -rn "DEBUG-x7k2" . <tmp> 2>/dev/null | grep -v '/tasks/' ; ls <tmp> 2>&1; git status --short
