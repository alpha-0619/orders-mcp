# orders-mcp

A read-only MCP server that lets Claude look up customers and orders in a shop database.

It is a small, complete example of the kind of server I build: three tools, read-only at
the database connection, tested through a real MCP client, and tried on real questions in
Claude Code. The shop is fictional: a coffee-gear store with 20 customers and 60 orders,
built from a fixed seed.

## The tools

| Tool | What it answers |
|---|---|
| `find_customers` | Who is this? Searches part of a name or email. |
| `list_orders` | What has this customer ordered? Newest first, optionally one status. |
| `get_order` | What is in this order, and what did it come to? |

What each tool reads, and its limits: [TOOLS.md](TOOLS.md).

## Read-only

1. The database is opened with `mode=ro`, so SQLite itself refuses any write with
   `attempt to write a readonly database`. On Postgres or MySQL the same idea is a
   database user that only has SELECT.
2. Each tool runs one fixed SELECT with its inputs passed as parameters. No tool takes SQL.
3. Each tool carries `readOnlyHint`, so MCP clients can show it as read-only. That one is a
   label for the client, not a lock.

Asked to cancel an order, Claude answered: "I could not cancel order 1057. The orders
tools available to me are read-only, so none of them can change an order's status."
That and two other questions are in the [run log](runs/2026-10-29-three-support-questions.md).

## Try it

```
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -e .
python scripts/build_db.py
```

**Claude Code:** start `claude` in this folder with the venv active. It reads `.mcp.json`
and asks you to approve the server the first time.

**Claude Desktop:** add this to `claude_desktop_config.json` (Settings, Developer, Edit
Config) with the full path to your venv's Python, then restart Claude Desktop:

```json
{
  "mcpServers": {
    "orders": {
      "command": "C:\\path\\to\\orders-mcp\\.venv\\Scripts\\python.exe",
      "args": ["-m", "orders_mcp"]
    }
  }
}
```

## Checks

```
python -m unittest discover -s tests -t .   # 12 tests, each one through an MCP client
python scripts/mutation_check.py            # switches off 11 safeguards one at a time; the tests catch all 11
python scripts/ask_claude.py "<question>"   # asks Claude Code, with this server as its only tool
```

Built with Python, the official MCP Python SDK (`mcp` 2.3) and SQLite.
