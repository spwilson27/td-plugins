import ast

from td_organize.cli import build_code


def test_build_code_is_valid_python():
    for cmd in ("organize", "check"):
        ast.parse(build_code(cmd, "/project1/foo", True, False))
