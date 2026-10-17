"""td-organize CLI: run organize/check inside a running TouchDesigner via td-mcp."""
import argparse
import json
import os
import sys
from pathlib import Path

RUNTIME = Path(__file__).with_name("td_runtime.py")


def _client():
    home = Path(os.environ.get("TD_MCP_HOME", Path.home() / "software/td-mcp"))
    try:
        from td_mcp.client import call, load_connection  # noqa
    except ImportError:
        sys.path.insert(0, str(home / "src"))
        from td_mcp.client import call, load_connection  # noqa
    return call, load_connection


def build_code(cmd, path, recursive, annotate):
    return (
        "import json as _json\n"
        + RUNTIME.read_text()
        + "\n_c = op(%r)\n" % path
        + "assert _c is not None, 'no such operator: ' + %r\n" % path
        + ("_r = organize(_c, recursive=%r, annotate_groups=%r)\n" % (recursive, annotate)
           if cmd == "organize" else "_r = check(_c, recursive=%r)\n" % recursive)
        + "print('TDORG_JSON ' + _json.dumps(_r))\n"
    )


def run(cmd, connection_file, path, recursive=True, annotate=True, timeout=110):
    call, load_connection = _client()
    conn = load_connection(Path(connection_file).expanduser())
    r = call("execute_python", {"code": build_code(cmd, path, recursive, annotate),
                                "timeout": timeout}, connection=conn, timeout=timeout)
    if not r.get("ok"):
        raise SystemExit("TD error: " + str(r.get("traceback") or r.get("error"))[-2000:])
    for line in reversed(r.get("stdout", "").splitlines()):
        if line.startswith("TDORG_JSON "):
            return json.loads(line[len("TDORG_JSON "):])
    raise SystemExit("no result from TD: " + str(r)[-500:])


def main(argv=None):
    ap = argparse.ArgumentParser(prog="td-organize", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, hlp in (("organize", "lay out the network"), ("check", "report overlaps")):
        p = sub.add_parser(name, help=hlp)
        g = p.add_mutually_exclusive_group(required=True)
        g.add_argument("--inst", help="td-plugins scratch instance (~/.tdctl/NAME/connection.json)")
        g.add_argument("--connection", help="td-mcp connection.json")
        p.add_argument("path", help="operator path of the COMP, e.g. /project1/foo")
        p.add_argument("--no-recursive", action="store_true")
        if name == "organize":
            p.add_argument("--no-annotate", action="store_true", help="ignore Annotate groups")
        p.add_argument("--json", action="store_true", help="print raw JSON")
    a = ap.parse_args(argv)
    conn = a.connection or str(Path(os.environ.get("TDCTL_HOME", Path.home() / ".tdctl"))
                               / a.inst / "connection.json")
    res = run(a.cmd, conn, a.path, not a.no_recursive,
              not getattr(a, "no_annotate", False))
    if a.json:
        print(json.dumps(res, indent=1))
    elif a.cmd == "organize":
        for p, s in res.items():
            print("%-50s nodes=%-3d groups=%d overlaps %d -> %d" % (
                p, s["nodes"], s["groups"], s["overlaps_before"], s["overlaps_after"]))
    else:
        for pr in res:
            print("overlap in %s: %s <-> %s" % (pr["comp"], pr["a"], pr["b"]))
        print("%d overlap(s)" % len(res))
    return 1 if (a.cmd == "check" and res) else 0


if __name__ == "__main__":
    sys.exit(main())
