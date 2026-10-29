"""Build data/shop.db, the fictional demo shop. Same data every time."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from orders_mcp.db import DEFAULT_DB, build_demo_db  # noqa: E402

if __name__ == "__main__":
    out = build_demo_db(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB)
    print(f"Wrote {out}")
