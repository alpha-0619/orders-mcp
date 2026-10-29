"""Three read-only tools over the shop database.

Every tool runs one fixed SELECT with its inputs passed as parameters. There is no
tool that takes SQL, and the connection is opened read-only (see db.connect_readonly).
"""
from __future__ import annotations

from contextlib import closing
from pathlib import Path
from typing import Annotated, Literal

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp_types import ToolAnnotations
from pydantic import BaseModel, Field

from .db import cents_to_usd, connect_readonly

READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)
Status = Literal["pending", "paid", "shipped", "delivered", "refunded", "cancelled"]
MAX_ROWS = 25


class CustomerMatch(BaseModel):
    id: int
    name: str
    email: str
    city: str
    orders: int


class CustomerSearch(BaseModel):
    matches: list[CustomerMatch]
    more_not_shown: bool = Field(description="True when there were more matches than the limit")


class OrderSummary(BaseModel):
    id: int
    status: Status
    placed: str
    shipped: str | None
    items: int
    total_usd: str


class CustomerOrders(BaseModel):
    customer_id: int
    customer_name: str
    orders: list[OrderSummary]
    more_not_shown: bool


class LineItem(BaseModel):
    sku: str
    product: str
    quantity: int
    unit_price_usd: str
    line_total_usd: str


class OrderDetail(BaseModel):
    id: int
    customer_id: int
    customer_name: str
    status: Status
    placed: str
    shipped: str | None
    items: list[LineItem]
    total_usd: str


def _like(text: str) -> str:
    """Match text anywhere, with % and _ taken literally rather than as wildcards."""
    return "%" + text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


def create_server(db_path: str | Path) -> MCPServer:
    server = MCPServer(
        name="orders",
        instructions="Read-only access to a shop's customers and orders. None of these tools can change anything.",
    )

    @server.tool(annotations=READ_ONLY)
    def find_customers(
        query: Annotated[str, Field(min_length=2, max_length=100, description="Part of a name or email")],
        limit: Annotated[int, Field(ge=1, le=MAX_ROWS)] = 10,
    ) -> CustomerSearch:
        """Find customers whose name or email contains the query (not case sensitive)."""
        with closing(connect_readonly(db_path)) as conn:
            rows = conn.execute(
                """SELECT c.id, c.name, c.email, c.city,
                          (SELECT COUNT(*) FROM orders o WHERE o.customer_id = c.id) AS orders
                   FROM customers c
                   WHERE c.name LIKE ? ESCAPE '\\' OR c.email LIKE ? ESCAPE '\\'
                   ORDER BY c.name LIMIT ?""",
                (_like(query), _like(query), limit + 1),
            ).fetchall()
        return CustomerSearch(matches=[CustomerMatch(**dict(r)) for r in rows[:limit]], more_not_shown=len(rows) > limit)

    @server.tool(annotations=READ_ONLY)
    def list_orders(
        customer_id: int,
        status: Status | None = None,
        limit: Annotated[int, Field(ge=1, le=MAX_ROWS)] = 10,
    ) -> CustomerOrders:
        """List one customer's orders, newest first, optionally only one status.

        Statuses: pending (not paid yet), paid (paid, not shipped yet), shipped, delivered,
        refunded, cancelled. Use find_customers first to get the customer_id.
        """
        with closing(connect_readonly(db_path)) as conn:
            customer = conn.execute("SELECT id, name FROM customers WHERE id = ?", (customer_id,)).fetchone()
            if customer is None:
                raise ToolError(f"No customer with id {customer_id}.")
            rows = conn.execute(
                """SELECT o.id, o.status, o.placed_at AS placed, o.shipped_at AS shipped,
                          SUM(i.quantity) AS items, SUM(i.quantity * i.unit_price_cents) AS cents
                   FROM orders o JOIN order_items i ON i.order_id = o.id
                   WHERE o.customer_id = ? AND (? IS NULL OR o.status = ?)
                   GROUP BY o.id ORDER BY o.placed_at DESC, o.id DESC LIMIT ?""",
                (customer_id, status, status, limit + 1),
            ).fetchall()
        orders = [OrderSummary(id=r["id"], status=r["status"], placed=r["placed"], shipped=r["shipped"],
                               items=r["items"], total_usd=cents_to_usd(r["cents"])) for r in rows[:limit]]
        return CustomerOrders(customer_id=customer["id"], customer_name=customer["name"], orders=orders,
                              more_not_shown=len(rows) > limit)

    @server.tool(annotations=READ_ONLY)
    def get_order(order_id: int) -> OrderDetail:
        """Get one order: who placed it, its status and dates, each line item, and the total."""
        with closing(connect_readonly(db_path)) as conn:
            order = conn.execute(
                """SELECT o.id, o.customer_id, c.name AS customer_name, o.status, o.placed_at, o.shipped_at
                   FROM orders o JOIN customers c ON c.id = o.customer_id WHERE o.id = ?""",
                (order_id,),
            ).fetchone()
            if order is None:
                raise ToolError(f"No order with id {order_id}.")
            lines = conn.execute(
                """SELECT p.sku, p.name AS product, i.quantity, i.unit_price_cents
                   FROM order_items i JOIN products p ON p.id = i.product_id
                   WHERE i.order_id = ? ORDER BY p.sku""",
                (order_id,),
            ).fetchall()
        items = [LineItem(sku=r["sku"], product=r["product"], quantity=r["quantity"],
                          unit_price_usd=cents_to_usd(r["unit_price_cents"]),
                          line_total_usd=cents_to_usd(r["quantity"] * r["unit_price_cents"])) for r in lines]
        total = sum(r["quantity"] * r["unit_price_cents"] for r in lines)
        return OrderDetail(id=order["id"], customer_id=order["customer_id"], customer_name=order["customer_name"],
                           status=order["status"], placed=order["placed_at"], shipped=order["shipped_at"],
                           items=items, total_usd=cents_to_usd(total))

    return server
