"""Break each safeguard on purpose, in a scratch copy, and check the tests notice.

A check that can't fail isn't a check. Each mutation switches one rule off; the run
fails if the test suite still passes with any rule off. A mutation only counts as caught
when a test fails, not when the code stops importing.
Usage: python scripts/mutation_check.py
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MUTATIONS = [
    ("read-only connection", "orders_mcp/db.py", 'f"{path.as_uri()}?mode=ro"', 'f"{path.as_uri()}"'),
    ("tools marked read-only", "orders_mcp/server.py", "ToolAnnotations(read_only_hint=True", "ToolAnnotations(read_only_hint=False"),
    ("wildcards taken literally", "orders_mcp/server.py",
     r'return "%" + text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"', 'return "%" + text + "%"'),
    ("25-row cap", "orders_mcp/server.py", "MAX_ROWS = 25", "MAX_ROWS = 1000"),
    ("customer list cut-off flag", "orders_mcp/server.py", "more_customers = len(rows) > limit", "more_customers = False"),
    ("order list cut-off flag", "orders_mcp/server.py", "more_orders = len(rows) > limit", "more_orders = False"),
    ("newest first", "orders_mcp/server.py", "ORDER BY o.placed_at DESC, o.id DESC", "ORDER BY o.placed_at, o.id"),
    ("status filter", "orders_mcp/server.py", "(? IS NULL OR o.status = ?)", "(? IS NULL OR ? IS NOT NULL)"),
    ("list totals count quantity", "orders_mcp/server.py",
     "COALESCE(SUM(i.quantity * i.unit_price_cents), 0) AS cents", "COALESCE(SUM(i.unit_price_cents), 0) AS cents"),
    ("units count quantity", "orders_mcp/server.py", "COALESCE(SUM(i.quantity), 0) AS units", "COUNT(i.order_id) AS units"),
    ("orders with no lines kept", "orders_mcp/server.py", "FROM orders o LEFT JOIN order_items i", "FROM orders o JOIN order_items i"),
    ("order total counts quantity", "orders_mcp/server.py",
     'total = sum(r["quantity"] * r["unit_price_cents"] for r in lines)', 'total = sum(r["unit_price_cents"] for r in lines)'),
    ("unknown customer named", "orders_mcp/server.py", "if customer is None:", "if False:"),
    ("unknown order named", "orders_mcp/server.py", "if order is None:", "if False:"),
]
FAILED_TEST = re.compile(r"^(?:FAIL|ERROR): (test_\w+)", re.M)


def main() -> int:
    missed = []
    for name, rel, old, new in MUTATIONS:
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "repo"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".venv", ".git", "data", "__pycache__", "*.egg-info"))
            target = copy / rel
            text = target.read_text(encoding="utf-8")
            if text.count(old) != 1:
                print(f"STALE   {name}: '{old}' found {text.count(old)} times in {rel}, expected once")
                missed.append(name)
                continue
            target.write_text(text.replace(old, new), encoding="utf-8")
            # The scratch copy comes first on the path, ahead of any installed orders_mcp.
            env = {**os.environ, "PYTHONPATH": str(copy)}
            result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
                                    cwd=copy, env=env, capture_output=True, text=True)
            failing = FAILED_TEST.findall(result.stderr)
            if result.returncode != 0 and failing:
                print(f"caught  {name}  ({', '.join(sorted(set(failing)))})")
            else:
                print(f"MISSED  {name}" + ("  (tests did not run)" if result.returncode != 0 else ""))
                missed.append(name)
    print(f"\n{len(MUTATIONS) - len(missed)}/{len(MUTATIONS)} mutations caught by the tests")
    return 1 if missed else 0


if __name__ == "__main__":
    sys.exit(main())
