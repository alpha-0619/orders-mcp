"""Ask Claude Code one question with this server as its only tool, and print every tool call.

Claude gets no built-in tools (no shell, no file reading), so everything it knows about
the shop has to come through the three MCP tools. Needs the claude CLI, logged in.
Usage: python scripts/ask_claude.py "Which of Dana Whitfield's orders haven't shipped yet?" [--workdir DIR]
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def ask(question: str, workdir: Path) -> list[str]:
    config = {"mcpServers": {"orders": {
        "command": sys.executable, "args": ["-m", "orders_mcp", "--db", str(ROOT / "data" / "shop.db")]}}}
    config_file = workdir / "mcp.json"
    config_file.write_text(json.dumps(config), encoding="utf-8")
    cmd = [shutil.which("claude") or "claude", "-p", question,  # which() finds claude.cmd on Windows
           "--mcp-config", str(config_file), "--strict-mcp-config",  # this server and nothing else
           "--tools", "",  # no built-in tools
           "--allowedTools", "mcp__orders",  # its tools may run without a prompt
           "--setting-sources", "project",  # skip personal settings and hooks
           "--no-session-persistence", "--output-format", "stream-json", "--verbose"]
    run = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        sys.exit(run.stderr or run.stdout)
    out = []
    for line in run.stdout.splitlines():
        event = json.loads(line)
        if event.get("type") == "system" and event.get("subtype") == "init":
            servers = ", ".join(f"{s['name']} ({s['status']})" for s in event.get("mcp_servers", []))
            out.append(f"Model: {event.get('model')}. MCP servers: {servers}. Tools: {', '.join(event.get('tools', []))}")
        elif event.get("type") == "assistant":
            for part in event["message"]["content"]:
                if part.get("type") == "tool_use":
                    out.append(f"-> {part['name']} {json.dumps(part['input'])}")
        elif event.get("type") == "user":
            for part in event["message"]["content"]:
                if isinstance(part, dict) and part.get("type") == "tool_result":
                    content = part.get("content")
                    text = content if isinstance(content, str) else " ".join(c.get("text", "") for c in content or [])
                    flag = "ERROR " if part.get("is_error") else ""
                    out.append(f"<- {flag}{text}")
        elif event.get("type") == "result":
            out.append(f"Answer:\n{event.get('result', '').strip()}")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question")
    parser.add_argument("--workdir", type=Path, help="empty folder to run Claude in (default: a new temp folder)")
    args = parser.parse_args()
    if args.workdir:
        args.workdir.mkdir(parents=True, exist_ok=True)
        print("\n".join(ask(args.question, args.workdir)))
    else:
        with tempfile.TemporaryDirectory() as tmp:
            print("\n".join(ask(args.question, Path(tmp))))


if __name__ == "__main__":
    main()
