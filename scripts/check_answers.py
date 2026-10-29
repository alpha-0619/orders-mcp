"""Print the facts behind the run log's three answers, read straight from the SQLite file.

This does not go through the server, so it is a second, independent way to get the same
facts. It also checks that data/shop.db is still byte-for-byte a fresh build.
Usage: python scripts/check_answers.py
"""
import hashlib
import sqlite3
import sys
import tempfile
from contextlib import closing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from orders_mcp.db import DEFAULT_DB, build_demo_db, cents_to_usd  # noqa: E402


def main() -> None:
    with closing(sqlite3.connect(f"{DEFAULT_DB.resolve().as_uri()}?mode=ro", uri=True)) as conn:
        q = lambda sql, *args: conn.execute(sql, args).fetchall()  # noqa: E731
        print("Dana Whitfield's orders with no ship date:")
        for order_id, status, placed, cents in q(
                """SELECT o.id, o.status, o.placed_at, SUM(i.quantity * i.unit_price_cents)
                   FROM orders o JOIN order_items i ON i.order_id = o.id
                   WHERE o.customer_id = 1 AND o.shipped_at IS NULL GROUP BY o.id ORDER BY o.id"""):
            print(f"  {order_id}  {status:<8} placed {placed}  total {cents_to_usd(cents)}")
        others = q("SELECT id, status FROM orders WHERE customer_id = 1 AND shipped_at IS NOT NULL ORDER BY id")
        print("Her other orders: " + ", ".join(f"{i} {s}" for i, s in others))

        (name,), = q("SELECT c.name FROM orders o JOIN customers c ON c.id = o.customer_id WHERE o.id = 1001")
        print(f"\nOrder 1001: {name}")
        lines = q("""SELECT p.name, i.quantity, i.unit_price_cents FROM order_items i JOIN products p ON p.id = i.product_id
                     WHERE i.order_id = 1001 ORDER BY p.sku""")
        print("  " + ", ".join(f"{p} x{n} at {cents_to_usd(c)}" for p, n, c in lines))
        print(f"  total {cents_to_usd(sum(n * c for _, n, c in lines))}")
        (customer_id,), = q("SELECT customer_id FROM orders WHERE id = 1001")
        counts = q("SELECT status, COUNT(*) FROM orders WHERE customer_id = ? GROUP BY status ORDER BY 2 DESC", customer_id)
        print(f"{name}'s orders: {sum(n for _, n in counts)} (" + ", ".join(f"{n} {s}" for s, n in counts) + ")")

        (status, shipped), = q("SELECT status, shipped_at FROM orders WHERE id = 1057")
        print(f"\nOrder 1057 now: status {status}, shipped {shipped or 'no'}")

    with tempfile.TemporaryDirectory() as tmp:
        fresh = build_demo_db(Path(tmp) / "fresh.db")
        same = hashlib.sha256(DEFAULT_DB.read_bytes()).digest() == hashlib.sha256(fresh.read_bytes()).digest()
    print(f"\ndata/shop.db is byte-for-byte a fresh build: {'yes' if same else 'NO'}")


if __name__ == "__main__":
    main()
