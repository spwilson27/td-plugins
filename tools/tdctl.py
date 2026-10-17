#!/usr/bin/env python3
"""Control a private scratch TouchDesigner via td-mcp.

  tdctl.py start <name>            launch own TD (own port + connection file), wait until ready
  tdctl.py exec <name> <file|->     run python in that TD, print JSON result
  tdctl.py stop <name>             kill only that TD
State lives in $TDCTL_HOME (default ~/.tdctl/<name>/). Never touches the user's TD.
"""
import json, os, signal, socket, subprocess, sys, time
from pathlib import Path

TDMCP = Path(os.environ.get("TD_MCP_HOME", Path.home() / "software/td-mcp"))
sys.path.insert(0, str(TDMCP / "src"))
from td_mcp.client import call, load_connection  # noqa

HOME = Path(os.environ.get("TDCTL_HOME", Path.home() / ".tdctl"))
TD_BIN = os.environ.get("TD_BIN", "/Applications/TouchDesigner.app/Contents/MacOS/TouchDesigner")
SEED = TDMCP / "tox" / "td_python_debug.tox"


def d(name):
    p = HOME / name
    p.mkdir(parents=True, exist_ok=True)
    return p


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def start(name):
    w = d(name)
    pidf = w / "pid"
    if pidf.exists() and alive(int(pidf.read_text())):
        conn = load_connection(w / "connection.json")
        r = call("td_status", connection=conn, timeout=10)
        if r.get("ok", True) and "error" not in r:
            print(json.dumps({"already_running": int(pidf.read_text()), "status": r}))
            return
    cf = w / "connection.json"
    if cf.exists():
        cf.unlink()
    env = dict(os.environ, TD_MCP_PORT=str(free_port()), TD_MCP_CONNECTION=str(cf))
    env.pop("TD_MCP_MODULEPATH", None)
    proc = subprocess.Popen([TD_BIN, str(SEED)], env=env, stdout=open(w / "td.log", "w"),
                            stderr=subprocess.STDOUT, start_new_session=True)
    pidf.write_text(str(proc.pid))
    deadline = time.time() + 150
    while time.time() < deadline:
        if proc.poll() is not None:
            sys.exit(f"TD exited early; see {w/'td.log'}")
        if cf.exists():
            try:
                conn = load_connection(cf)
                r = call("td_status", connection=conn, timeout=10)
                if "error" not in r:
                    print(json.dumps({"pid": proc.pid, "port": conn.port, "status": r}))
                    return
            except Exception:
                pass
        time.sleep(0.5)
    sys.exit("TD did not start in time")


def exec_(name, src, timeout=110):
    code = sys.stdin.read() if src == "-" else Path(src).read_text()
    conn = load_connection(d(name) / "connection.json")
    r = call("execute_python", {"code": code, "timeout": timeout}, connection=conn, timeout=timeout)
    print(json.dumps(r, indent=1, default=str))
    sys.exit(0 if r.get("ok") else 1)


def stop(name):
    w = d(name)
    pidf = w / "pid"
    if not pidf.exists():
        print("not running"); return
    pid = int(pidf.read_text())
    try:
        os.killpg(pid, signal.SIGTERM)
        for _ in range(40):
            if not alive(pid): break
            time.sleep(0.25)
        if alive(pid): os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    pidf.unlink(missing_ok=True)
    (w / "connection.json").unlink(missing_ok=True)
    print("stopped", pid)


if __name__ == "__main__":
    cmd, name = sys.argv[1], sys.argv[2]
    {"start": lambda: start(name), "stop": lambda: stop(name),
     "exec": lambda: exec_(name, sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 110)}[cmd]()
