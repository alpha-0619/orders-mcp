# What each tool does, and what it can reach

All three tools open `data/shop.db` read-only (SQLite `mode=ro`) for one query and close it
again. None of them can write, and none of them takes SQL from the model: each runs one
fixed SELECT with its inputs passed as parameters.

Money is stored as whole cents and turned into dollars without floating point.

## find_customers

Finds customers whose name or email contains the query. Not case sensitive. `%`, `_` and
quotes in the query are plain text, not wildcards.

| | |
|---|---|
| Inputs | `query`: 2 to 100 characters. `limit`: 1 to 25, default 10. |
| Reads | `customers`: id, name, email, city. `orders`: only to count each customer's orders. |
| Returns | Matching customers sorted by name, each with an order count, and `more_not_shown` when the limit cut the list short. |

## list_orders

Lists one customer's orders, newest first, optionally only one status.

| | |
|---|---|
| Inputs | `customer_id`. `status` (optional): pending, paid, shipped, delivered, refunded or cancelled. `limit`: 1 to 25, default 10. |
| Reads | `customers`: id, name. `orders`: id, status, placed and shipped dates. `order_items`: quantity and unit price, to count items and add up totals. |
| Returns | The customer's name and orders, each with status, dates, item count and total, and `more_not_shown`. |
| Errors | `No customer with id N.` |

The tool tells Claude what the statuses mean: pending (not paid yet), paid (paid, not
shipped yet), shipped, delivered, refunded, cancelled.

## get_order

Gets one order with its line items and total.

| | |
|---|---|
| Inputs | `order_id` |
| Reads | `orders`, the customer's name from `customers`, `order_items`, and SKU and product name from `products`. |
| Returns | Customer, status, placed and shipped dates, each line (SKU, product, quantity, unit price, line total) and the order total. |
| Errors | `No order with id N.` |

## Limits

- `find_customers` and `list_orders` return at most 25 rows. Asking for more is refused with
  a message that says so.
- An unknown customer or order id comes back as a clear error Claude can read, not a crash.
- The `readOnlyHint` on each tool tells MCP clients the tool changes nothing. It is a label
  for the client, not a lock; the read-only connection and the fixed queries are the locks.
