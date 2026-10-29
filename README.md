# orders-mcp

A read-only MCP server that lets Claude look up customers and orders in a shop database.

It is a small, complete example of the kind of server I build: three tools, read-only at
the database connection, covered by tests, and tried in Claude Code on three support-style
questions. The shop is made up: a coffee-gear store with 20 customers and 60 orders,
built from a fixed seed.

## The tools

| Tool | What it answers |
|---|---|
| `find_customers` | Who is this? Searches part of a name or email. |
| `list_orders` | What has this customer ordered? Newest first, optionally one status. |
| `get_order` | What is in this order, and what did it come to? |

What each tool reads, and its limits: [TOOLS.md](TOOLS.md).

## Read-only

1. There is no tool that writes. The tools only run SELECT statements written in the code,
   with their inputs passed as parameters, and no tool takes SQL.
2. The database is opened with `mode=ro`, so if a later change ever tried to write, SQLite
   itself would refuse with `attempt to write a readonly database`. On Postgres or MySQL,
   the same job is done by a database login that is only granted SELECT.
3. Each tool carries `readOnlyHint`, which tells MCP clients it changes nothing. That is
   information for the client; it doesn't block anything by itself.

Asked to cancel an order, Claude answered: "I could not cancel the order. The orders tools
available to me are read-only, so none of them can change an order's status." That run and
two others are in the [run log](runs/2026-10-29-three-questions.md).

## Try it

Needs Python 3.11 or newer.

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
python -m unittest discover -s tests -t .   # 15 tests
python scripts/mutation_check.py            # breaks 14 safeguards one at a time; the tests catch all 14
python scripts/check_answers.py             # the run log's answers, read straight from the database
```

14 of the 15 tests call the tools through an MCP client, one of them with the server
started as its own process over stdio, the way Claude Code starts it. The other test
writes to the database connection directly, to check that it refuses.

`python scripts/ask_claude.py "<question>"` asks Claude Code a question with this server as
its only MCP server and prints every tool call. It needs Claude Code installed and logged
in, and it uses your own Claude usage.

Built with Python, the official MCP Python SDK (`mcp` 2.3) and SQLite.
