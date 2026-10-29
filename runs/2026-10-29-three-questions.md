# Run: three support-style questions (2026-10-29)

Claude Code answered three questions with the orders server as its only MCP server. It had
no built-in tools (no shell, no file access: `--tools ""`), so everything it knew about the
shop came through the server's three tools. The questions were written for the demo, and
the shop and its customers are made up.

Each section has the question, then the tool calls and Claude's answer exactly as
`python scripts/ask_claude.py "<question>"` printed them. Headings and labels were added.

Each run started with:

```
Model: claude-fable-5-1. MCP servers: orders (connected). Tools: mcp__orders__find_customers, mcp__orders__get_order, mcp__orders__list_orders
```

## 1. Which of Dana Whitfield's orders haven't shipped?

**Question:** Dana Whitfield emailed asking about her orders. Which of them haven't shipped yet, and what's in each one?

Tool calls (`->` call, `<-` what the server returned):

```
-> mcp__orders__find_customers {"query": "Dana Whitfield"}
<- {"matches":[{"id":1,"name":"Dana Whitfield","email":"dana.whitfield@example.com","city":"Austin","orders":5}],"more_not_shown":false}
-> mcp__orders__list_orders {"customer_id": 1, "status": "pending"}
-> mcp__orders__list_orders {"customer_id": 1, "status": "paid"}
<- {"customer_id":1,"customer_name":"Dana Whitfield","orders":[{"id":1059,"status":"pending","placed":"2026-10-27","shipped":null,"units":2,"total_usd":"54.00"}],"more_not_shown":false}
<- {"customer_id":1,"customer_name":"Dana Whitfield","orders":[{"id":1057,"status":"paid","placed":"2026-10-25","shipped":null,"units":2,"total_usd":"113.00"}],"more_not_shown":false}
-> mcp__orders__get_order {"order_id": 1059}
-> mcp__orders__get_order {"order_id": 1057}
<- {"id":1059,"customer_id":1,"customer_name":"Dana Whitfield","status":"pending","placed":"2026-10-27","shipped":null,"items":[{"sku":"BEAN-1KG","product":"Single-origin beans 1 kg","quantity":1,"unit_price_usd":"42.00","line_total_usd":"42.00"},{"sku":"CLEAN-30","product":"Cleaning tablets (30)","quantity":1,"unit_price_usd":"12.00","line_total_usd":"12.00"}],"total_usd":"54.00"}
<- {"id":1057,"customer_id":1,"customer_name":"Dana Whitfield","status":"paid","placed":"2026-10-25","shipped":null,"items":[{"sku":"KETL-GN","product":"Gooseneck kettle","quantity":1,"unit_price_usd":"79.00","line_total_usd":"79.00"},{"sku":"SCALE-D","product":"Digital scale","quantity":1,"unit_price_usd":"34.00","line_total_usd":"34.00"}],"total_usd":"113.00"}
```

**Claude's answer:**

Dana Whitfield has two orders that haven't shipped yet. Her other three orders are already past the shipping stage.

| Order | Status | Placed | Items | Total |
|---|---|---|---|---|
| 1057 | Paid, awaiting shipment | 2026-10-25 | Gooseneck kettle (1), Digital scale (1) | $113.00 |
| 1059 | Pending, not yet paid | 2026-10-27 | Single-origin beans 1 kg (1), Cleaning tablets 30-pack (1) | $54.00 |

Order 1057 is paid and should be the one to check on for shipping. Order 1059 is still unpaid, so it won't ship until payment comes through.

## 2. Who placed order 1001?

**Question:** Who placed order 1001, what was in it, and how many orders has that customer placed with us in total?

Tool calls (`->` call, `<-` what the server returned):

```
-> mcp__orders__get_order {"order_id": 1001}
<- {"id":1001,"customer_id":4,"customer_name":"Tomas Silva","status":"delivered","placed":"2026-07-01","shipped":"2026-07-02","items":[{"sku":"GRIND-B1","product":"Burr grinder","quantity":2,"unit_price_usd":"129.00","line_total_usd":"258.00"},{"sku":"MUG-TRV","product":"Travel mug","quantity":1,"unit_price_usd":"29.00","line_total_usd":"29.00"},{"sku":"POUR-SET","product":"Ceramic pour-over set","quantity":2,"unit_price_usd":"38.00","line_total_usd":"76.00"}],"total_usd":"363.00"}
-> mcp__orders__list_orders {"customer_id": 4, "limit": 25}
<- {"customer_id":4,"customer_name":"Tomas Silva","orders":[{"id":1051,"status":"refunded","placed":"2026-10-11","shipped":"2026-10-14","units":3,"total_usd":"94.00"},{"id":1047,"status":"delivered","placed":"2026-10-05","shipped":"2026-10-08","units":4,"total_usd":"112.00"},{"id":1043,"status":"delivered","placed":"2026-09-27","shipped":"2026-09-28","units":4,"total_usd":"152.00"},{"id":1036,"status":"delivered","placed":"2026-09-06","shipped":"2026-09-07","units":3,"total_usd":"147.00"},{"id":1029,"status":"delivered","placed":"2026-08-21","shipped":"2026-08-23","units":4,"total_usd":"134.00"},{"id":1026,"status":"delivered","placed":"2026-08-16","shipped":"2026-08-19","units":2,"total_usd":"13.00"},{"id":1025,"status":"delivered","placed":"2026-08-15","shipped":"2026-08-16","units":2,"total_usd":"30.50"},{"id":1011,"status":"cancelled","placed":"2026-07-15","shipped":null,"units":2,"total_usd":"258.00"},{"id":1001,"status":"delivered","placed":"2026-07-01","shipped":"2026-07-02","units":5,"total_usd":"363.00"}],"more_not_shown":false}
```

**Claude's answer:**

Order 1001 was placed by Tomas Silva on 2026-07-01, shipped the next day, and is now delivered.

| Item | Qty | Unit price | Line total |
|---|---|---|---|
| Burr grinder (GRIND-B1) | 2 | $129.00 | $258.00 |
| Travel mug (MUG-TRV) | 1 | $29.00 | $29.00 |
| Ceramic pour-over set (POUR-SET) | 2 | $38.00 | $76.00 |
| **Order total** | | | **$363.00** |

Tomas has placed **9 orders** in total with us, between July and October 2026. Of those, 7 were delivered, 1 was cancelled before shipping, and the most recent one from 2026-10-11 was refunded.

## 3. Cancel an order

**Question:** Dana Whitfield wants to cancel order 1057. Please mark it as cancelled.

Tool calls (`->` call, `<-` what the server returned):

```
-> mcp__orders__get_order {"order_id": 1057}
<- {"id":1057,"customer_id":1,"customer_name":"Dana Whitfield","status":"paid","placed":"2026-10-25","shipped":null,"items":[{"sku":"KETL-GN","product":"Gooseneck kettle","quantity":1,"unit_price_usd":"79.00","line_total_usd":"79.00"},{"sku":"SCALE-D","product":"Digital scale","quantity":1,"unit_price_usd":"34.00","line_total_usd":"34.00"}],"total_usd":"113.00"}
```

**Claude's answer:**

I could not cancel the order. The orders tools available to me are read-only, so none of them can change an order's status.

What I confirmed about order 1057:

- **Customer:** Dana Whitfield, placed on 2026-10-25.
- **Status:** paid, not yet shipped. It is still in a cancellable state.
- **Items:** one gooseneck kettle and one digital scale.

| Total | $113.00 |
|---|---|

To cancel it, the status change needs to happen in the shop's admin system or through a tool with write access. Because the order is already paid, a refund will also need to be issued alongside the cancellation.

Note: Claude's remarks that the order can still be cancelled and that a refund would be needed are its own
inferences. The demo has no cancellation or refund rules.

## Checked against the database

Output of `python scripts/check_answers.py`, which reads the SQLite file directly instead of going through the server:

```
Dana Whitfield's orders with no ship date:
  1057  paid     placed 2026-10-25  total 113.00
  1059  pending  placed 2026-10-27  total 54.00
Her other orders: 1010 delivered, 1030 delivered, 1054 shipped

Order 1001: Tomas Silva
  Burr grinder x2 at 129.00, Travel mug x1 at 29.00, Ceramic pour-over set x2 at 38.00
  total 363.00
Tomas Silva's orders: 9 (7 delivered, 1 refunded, 1 cancelled)

Order 1057 now: status paid, shipped no

data/shop.db is byte-for-byte a fresh build: yes
```
