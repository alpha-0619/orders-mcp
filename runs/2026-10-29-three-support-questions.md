# Run: three questions from a support team (2026-10-29)

Claude Code answered three questions with this server as its only tool. It had no shell
and no file access (`--tools ""`), so everything it knew about the shop came through the
three MCP tools. The questions were written for the demo. Everything else below is the
real output of `python scripts/ask_claude.py "<question>"`, copied unedited.

Each run started with:

```
Model: claude-fable-5-1. MCP servers: orders (connected). Tools: mcp__orders__find_customers, mcp__orders__get_order, mcp__orders__list_orders
```

## 1. Which of Dana Whitfield's orders haven't shipped yet?

**Question:** Dana Whitfield emailed asking about her orders. Which of them haven't shipped yet, and what's in each one?

Tool calls (`->` call, `<-` what the server returned):

```
-> mcp__orders__find_customers {"query": "Dana Whitfield"}
<- {"matches":[{"id":1,"name":"Dana Whitfield","email":"dana.whitfield@example.com","city":"Austin","orders":5}],"more_not_shown":false}
-> mcp__orders__list_orders {"customer_id": 1, "status": "pending"}
<- {"customer_id":1,"customer_name":"Dana Whitfield","orders":[{"id":1059,"status":"pending","placed":"2026-10-27","shipped":null,"items":2,"total_usd":"54.00"}],"more_not_shown":false}
-> mcp__orders__list_orders {"customer_id": 1, "status": "paid"}
<- {"customer_id":1,"customer_name":"Dana Whitfield","orders":[{"id":1057,"status":"paid","placed":"2026-10-25","shipped":null,"items":2,"total_usd":"113.00"}],"more_not_shown":false}
-> mcp__orders__get_order {"order_id": 1059}
<- {"id":1059,"customer_id":1,"customer_name":"Dana Whitfield","status":"pending","placed":"2026-10-27","shipped":null,"items":[{"sku":"BEAN-1KG","product":"Single-origin beans 1 kg","quantity":1,"unit_price_usd":"42.00","line_total_usd":"42.00"},{"sku":"CLEAN-30","product":"Cleaning tablets (30)","quantity":1,"unit_price_usd":"12.00","line_total_usd":"12.00"}],"total_usd":"54.00"}
-> mcp__orders__get_order {"order_id": 1057}
<- {"id":1057,"customer_id":1,"customer_name":"Dana Whitfield","status":"paid","placed":"2026-10-25","shipped":null,"items":[{"sku":"KETL-GN","product":"Gooseneck kettle","quantity":1,"unit_price_usd":"79.00","line_total_usd":"79.00"},{"sku":"SCALE-D","product":"Digital scale","quantity":1,"unit_price_usd":"34.00","line_total_usd":"34.00"}],"total_usd":"113.00"}
```

**Claude's answer:**

Two of Dana Whitfield's five orders haven't shipped. One is paid and waiting on fulfillment, and one is still unpaid.

| Order | Status | Placed | Items | Total |
|---|---|---|---|---|
| 1057 | Paid, not shipped | 2026-10-25 | Gooseneck kettle ($79.00), Digital scale ($34.00) | $113.00 |
| 1059 | Pending (not paid yet) | 2026-10-27 | Single-origin beans 1 kg ($42.00), Cleaning tablets, 30 ct ($12.00) | $54.00 |

Her other three orders are already shipped, delivered, refunded, or cancelled, so they are not awaiting shipment. Order 1059 won't ship until payment comes through, which may be worth mentioning in your reply to her.

## 2. Who placed order 1001?

**Question:** Who placed order 1001, what was in it, and how many orders has that customer placed with us in total?

Tool calls (`->` call, `<-` what the server returned):

```
-> mcp__orders__get_order {"order_id": 1001}
<- {"id":1001,"customer_id":4,"customer_name":"Tomas Silva","status":"delivered","placed":"2026-07-01","shipped":"2026-07-02","items":[{"sku":"GRIND-B1","product":"Burr grinder","quantity":2,"unit_price_usd":"129.00","line_total_usd":"258.00"},{"sku":"MUG-TRV","product":"Travel mug","quantity":1,"unit_price_usd":"29.00","line_total_usd":"29.00"},{"sku":"POUR-SET","product":"Ceramic pour-over set","quantity":2,"unit_price_usd":"38.00","line_total_usd":"76.00"}],"total_usd":"363.00"}
-> mcp__orders__list_orders {"customer_id": 4, "limit": 25}
<- {"customer_id":4,"customer_name":"Tomas Silva","orders":[{"id":1051,"status":"refunded","placed":"2026-10-11","shipped":"2026-10-14","items":3,"total_usd":"94.00"},{"id":1047,"status":"delivered","placed":"2026-10-05","shipped":"2026-10-08","items":4,"total_usd":"112.00"},{"id":1043,"status":"delivered","placed":"2026-09-27","shipped":"2026-09-28","items":4,"total_usd":"152.00"},{"id":1036,"status":"delivered","placed":"2026-09-06","shipped":"2026-09-07","items":3,"total_usd":"147.00"},{"id":1029,"status":"delivered","placed":"2026-08-21","shipped":"2026-08-23","items":4,"total_usd":"134.00"},{"id":1026,"status":"delivered","placed":"2026-08-16","shipped":"2026-08-19","items":2,"total_usd":"13.00"},{"id":1025,"status":"delivered","placed":"2026-08-15","shipped":"2026-08-16","items":2,"total_usd":"30.50"},{"id":1011,"status":"cancelled","placed":"2026-07-15","shipped":null,"items":2,"total_usd":"258.00"},{"id":1001,"status":"delivered","placed":"2026-07-01","shipped":"2026-07-02","items":5,"total_usd":"363.00"}],"more_not_shown":false}
```

**Claude's answer:**

Order 1001 was placed by Tomas Silva on 2026-07-01 and was delivered, shipping the next day.

**Contents of order 1001**

| Product | Qty | Unit price | Line total |
|---|---|---|---|
| Burr grinder | 2 | $129.00 | $258.00 |
| Travel mug | 1 | $29.00 | $29.00 |
| Ceramic pour-over set | 2 | $38.00 | $76.00 |
| **Order total** | | | **$363.00** |

**Tomas Silva's order history**

Total orders placed: 9

- 7 delivered
- 1 cancelled (order 1011, never shipped)
- 1 refunded (order 1051, the most recent, placed 2026-10-11)

Order 1001 was their first order with us, and it remains their largest at $363.00. The list is complete, with no further orders beyond the nine shown.

## 3. Cancel an order

**Question:** Dana Whitfield wants to cancel order 1057. Please mark it as cancelled.

Tool calls (`->` call, `<-` what the server returned):

```
-> mcp__orders__get_order {"order_id": 1057}
<- {"id":1057,"customer_id":1,"customer_name":"Dana Whitfield","status":"paid","placed":"2026-10-25","shipped":null,"items":[{"sku":"KETL-GN","product":"Gooseneck kettle","quantity":1,"unit_price_usd":"79.00","line_total_usd":"79.00"},{"sku":"SCALE-D","product":"Digital scale","quantity":1,"unit_price_usd":"34.00","line_total_usd":"34.00"}],"total_usd":"113.00"}
```

**Claude's answer:**

I could not cancel order 1057. The orders tools available to me are read-only, so none of them can change an order's status.

**What I confirmed about the order:**

- It belongs to Dana Whitfield and was placed on 2026-10-25.
- Its status is paid and it has not shipped yet, so it is still eligible for cancellation.
- It contains a gooseneck kettle and a digital scale, totalling 113.00 USD.

**To complete the cancellation,** someone will need to update the status in the shop's admin system directly, or a write-capable orders tool would need to be connected to this session. Once that is done, I can verify the new status here.

## Checked against the database

Run after the three questions, straight against the SQLite file rather than through the server:

```
Dana Whitfield's orders with no ship date:
  1057  paid     placed 2026-10-25  total 113.00
  1059  pending  placed 2026-10-27  total 54.00
Her other three: 1010 delivered, 1030 delivered, 1054 shipped

Order 1001: Tomas Silva
  Burr grinder x2 at 129.00, Travel mug x1 at 29.00, Ceramic pour-over set x2 at 38.00
  total 363.00
Tomas Silva's orders: 9 (7 delivered, 1 cancelled, 1 refunded)

Order 1057 after question 3: status paid, no ship date
```

`data/shop.db` after the three runs is byte-for-byte the same file as a fresh
`python scripts/build_db.py` on the same machine (SHA-256 starts `11a4961ebdcb8fe6` for
both). A build with a different SQLite version differs only in the version number SQLite
writes into the file header.
