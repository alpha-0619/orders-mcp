# What each tool does, and what it can reach

Each tool opens `data/shop.db` read-only (SQLite `mode=ro`), runs SELECT statements that
are written in the code, and closes it again. None of them can write, and none of them
takes SQL from the model: inputs are passed to the queries as parameters, so quotes or
SQL in an input are just text.

Money is stored as whole cents and turned into dollars without floating point.

## find_customers

Finds customers whose name or email contains the query. Upper and lower case match for
the letters A to Z. `%` and `_` in the query are plain characters, not wildcards.

| | |
|---|---|
| Inputs | `query`: 2 to 100 characters. `limit`: 1 to 25, default 10. |
| Reads | `customers`: id, name, email, city. `orders`: only to count each customer's orders. |
| Returns | Matching customers sorted by name, each with an order count, and `more_not_shown` when the limit cut the list short. |

## list_orders

Lists one customer's orders, newest first. Can be limited to one status.

| | |
|---|---|
| Inputs | `customer_id`. `status` (optional): pending, paid, shipped, delivered, refunded or cancelled. `limit`: 1 to 25, default 10. |
| Reads | `customers`: id, name. `orders`: id, status, placed and shipped dates. `order_items`: quantity and unit price. |
| Returns | The customer's name and orders. Each order has its status, dates, `units` (items counted with their quantities) and total. `more_not_shown` is true when the limit cut the list short. |
| Errors | `No customer with ID N.` |

The tool tells Claude what the statuses mean: pending (not paid yet), paid (paid, not
shipped yet), shipped, delivered, refunded, cancelled.

## get_order

Gets one order with its line items and total.

| | |
|---|---|
| Inputs | `order_id` |
| Reads | `orders`, the customer's name from `customers`, `order_items`, and SKU and product name from `products`. |
| Returns | Customer, status, placed and shipped dates, each line (SKU, product, quantity, unit price, line total) and the order total. |
| Errors | `No order with ID N.` |

## Limits

- `find_customers` and `list_orders` return at most 25 rows. Asking for more is refused with
  a message that says so. `get_order` returns every line of the one order it is asked for.
- An unknown customer or order ID comes back as an error message that names it.
- The `readOnlyHint` on each tool tells MCP clients the tool changes nothing. It is
  information for the client. The read-only connection and the fixed queries are what
  actually stop writes.
