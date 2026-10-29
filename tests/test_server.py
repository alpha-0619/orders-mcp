"""The server, tested the way Claude uses it: through an MCP client, one tool call at a time."""
import hashlib
import logging
import sqlite3
import tempfile
import unittest
from contextlib import closing
from decimal import Decimal
from pathlib import Path

import anyio
from mcp.client import Client

from orders_mcp.db import build_demo_db, connect_readonly
from orders_mcp.server import create_server

TMP = tempfile.TemporaryDirectory()
DB = Path(TMP.name) / "shop.db"


def setUpModule():
    build_demo_db(DB)
    logging.disable(logging.INFO)  # the server logs each expected tool error; keep test output readable


def tearDownModule():
    logging.disable(logging.NOTSET)
    TMP.cleanup()


async def _session(work):
    async with Client(create_server(DB)) as client:
        return await work(client)


def call(tool: str, **args):
    return anyio.run(_session, lambda client: client.call_tool(tool, args))


def data(tool: str, **args) -> dict:
    result = call(tool, **args)
    assert not result.is_error, result.content
    return result.structured_content


def error_text(tool: str, **args) -> str:
    result = call(tool, **args)
    assert result.is_error, f"{tool} {args} should have failed"
    return " ".join(part.text for part in result.content)


def sql(query: str, *params):
    """A second way to read the data, not through the server, to check its answers against."""
    with closing(sqlite3.connect(DB)) as conn:
        return conn.execute(query, params).fetchall()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ToolList(unittest.TestCase):
    def test_exactly_three_tools_all_marked_read_only(self):
        tools = anyio.run(_session, lambda client: client.list_tools()).tools
        self.assertEqual(sorted(t.name for t in tools), ["find_customers", "get_order", "list_orders"])
        for tool in tools:
            self.assertTrue(tool.annotations and tool.annotations.read_only_hint, tool.name)


class FindCustomers(unittest.TestCase):
    def test_matches_name_or_email_in_any_case(self):
        self.assertEqual([m["name"] for m in data("find_customers", query="WHITFIELD")["matches"]], ["Dana Whitfield"])
        self.assertEqual([m["id"] for m in data("find_customers", query="ravi.iyer@")["matches"]], [16])

    def test_says_when_more_matches_were_cut_off(self):
        found = data("find_customers", query="@example.com", limit=5)
        self.assertEqual(len(found["matches"]), 5)
        self.assertTrue(found["more_not_shown"])
        self.assertFalse(data("find_customers", query="@example.com", limit=25)["more_not_shown"])

    def test_wildcards_and_quotes_are_plain_text(self):
        for query in ["%%", "__", "' OR 1=1 --", "\" OR \"\"=\""]:
            self.assertEqual(data("find_customers", query=query)["matches"], [], query)


class ListOrders(unittest.TestCase):
    def test_newest_first_and_filtered_by_status(self):
        everything = data("list_orders", customer_id=1)
        self.assertEqual(everything["customer_name"], "Dana Whitfield")
        self.assertEqual([o["id"] for o in everything["orders"]], [1059, 1057, 1054, 1030, 1010])
        self.assertEqual([o["id"] for o in data("list_orders", customer_id=1, status="paid")["orders"]], [1057])

    def test_unknown_customer_is_a_clear_error(self):
        self.assertIn("No customer with id 999.", error_text("list_orders", customer_id=999))


class GetOrder(unittest.TestCase):
    def test_line_items_and_total(self):
        order = data("get_order", order_id=1057)
        self.assertEqual((order["customer_name"], order["status"], order["shipped"]), ("Dana Whitfield", "paid", None))
        self.assertEqual([(i["sku"], i["quantity"]) for i in order["items"]], [("KETL-GN", 1), ("SCALE-D", 1)])
        self.assertEqual(order["total_usd"], "113.00")

    def test_unknown_order_is_a_clear_error(self):
        self.assertIn("No order with id 99999.", error_text("get_order", order_id=99999))


class Limits(unittest.TestCase):
    def test_no_tool_returns_more_than_25_rows(self):
        self.assertIn("less than or equal to 25", error_text("find_customers", query="example", limit=26))
        self.assertIn("less than or equal to 25", error_text("list_orders", customer_id=1, limit=26))


class Totals(unittest.TestCase):
    def test_every_total_agrees_with_a_direct_sql_sum(self):
        expected = {order_id: Decimal(cents) / 100 for order_id, cents in sql(
            "SELECT order_id, SUM(quantity * unit_price_cents) FROM order_items GROUP BY order_id")}
        self.assertEqual(len(expected), 60)
        listed = {}
        for (customer_id,) in sql("SELECT id FROM customers"):
            for order in data("list_orders", customer_id=customer_id, limit=25)["orders"]:
                listed[order["id"]] = Decimal(order["total_usd"])
        self.assertEqual(listed, expected)
        for order_id, total in expected.items():
            order = data("get_order", order_id=order_id)
            self.assertEqual(Decimal(order["total_usd"]), total, order_id)
            self.assertEqual(sum(Decimal(i["line_total_usd"]) for i in order["items"]), total, order_id)


class ReadOnly(unittest.TestCase):
    def test_the_connection_refuses_every_kind_of_write(self):
        writes = ["UPDATE orders SET status = 'refunded' WHERE id = 1057",
                  "INSERT INTO customers VALUES (99, 'X', 'x@example.com', 'Y', '2026-10-28')",
                  "DELETE FROM order_items",
                  "DROP TABLE orders"]
        for statement in writes:
            with closing(connect_readonly(DB)) as conn, \
                    self.assertRaisesRegex(sqlite3.OperationalError, "attempt to write a readonly database"):
                conn.execute(statement)

    def test_tool_calls_leave_the_file_byte_for_byte_unchanged(self):
        before = sha256(DB)
        data("find_customers", query="ex", limit=25)
        for order_id in (1001, 1030, 1057, 1060):
            data("get_order", order_id=order_id)
        data("list_orders", customer_id=1, status="pending")
        error_text("get_order", order_id=0)
        self.assertEqual(sha256(DB), before)


if __name__ == "__main__":
    unittest.main()
