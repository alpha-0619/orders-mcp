"""Run the server over stdio: python -m orders_mcp [--db PATH]"""
from __future__ import annotations

import argparse
import os

from .db import DEFAULT_DB
from .server import create_server


def main() -> None:
    parser = argparse.ArgumentParser(prog="orders-mcp", description=__doc__)
    parser.add_argument("--db", default=os.environ.get("ORDERS_DB", str(DEFAULT_DB)),
                        help="SQLite file to read (default: data/shop.db in this repo, or $ORDERS_DB)")
    create_server(parser.parse_args().db).run()


if __name__ == "__main__":
    main()
