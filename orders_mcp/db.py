"""The shop database: a read-only connection, and the fictional demo data."""
from __future__ import annotations

import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "shop.db"


def connect_readonly(path: str | Path) -> sqlite3.Connection:
    """Open the database so that SQLite itself refuses every write.

    With mode=ro, an INSERT, UPDATE or DELETE on this connection fails with
    "attempt to write a readonly database". The tools never send one, and this
    is what stops them if a later change ever tries.
    """
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"No database at {path}. Build it with: python scripts/build_db.py")
    conn = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def cents_to_usd(cents: int) -> str:
    """Exact dollars from integer cents, without going through a float."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}{cents // 100}.{cents % 100:02d}"


SCHEMA = """
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    city TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    price_cents INTEGER NOT NULL
);
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    status TEXT NOT NULL CHECK (status IN ('pending', 'paid', 'shipped', 'delivered', 'refunded', 'cancelled')),
    placed_at TEXT NOT NULL,
    shipped_at TEXT
);
CREATE TABLE order_items (
    order_id INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_cents INTEGER NOT NULL,
    PRIMARY KEY (order_id, product_id)
);
"""

# Fictional people at example.com, a domain reserved for examples.
CUSTOMERS = [
    ("Dana Whitfield", "Austin"), ("Marcus Okafor", "Leeds"), ("Priya Raman", "Toronto"),
    ("Tomas Silva", "Lisbon"), ("Lena Brandt", "Hamburg"), ("Owen Mercer", "Denver"),
    ("Hana Sato", "Osaka"), ("Felix Lindqvist", "Malmo"), ("Grace Adeyemi", "Dublin"),
    ("Ivo Petrak", "Brno"), ("Nora Calloway", "Portland"), ("Sam Reyes", "San Diego"),
    ("Ada Novak", "Zagreb"), ("Leo Hartmann", "Vienna"), ("Mia Duarte", "Porto"),
    ("Ravi Iyer", "Pune"), ("Zoe Fischer", "Melbourne"), ("Eli Mensah", "Accra"),
    ("Ines Moreau", "Lyon"), ("Kofi Kowalczyk", "Krakow"),
]

PRODUCTS = [
    ("POUR-SET", "Ceramic pour-over set", 3800), ("GRIND-B1", "Burr grinder", 12900),
    ("CARAFE-6", "Glass carafe 600 ml", 2400), ("FILT-100", "Paper filters (100)", 650),
    ("KETL-GN", "Gooseneck kettle", 7900), ("MUG-TRV", "Travel mug", 2900),
    ("CUP-ESP2", "Espresso cups (set of 2)", 1800), ("SCALE-D", "Digital scale", 3400),
    ("CLEAN-30", "Cleaning tablets (30)", 1200), ("BEAN-1KG", "Single-origin beans 1 kg", 4200),
]

# Dana Whitfield's orders are fixed so the example questions in the README have stable answers:
# (status, placed, days to ship or None, [(sku, quantity)])
PINNED = [
    ("delivered", "2026-07-14", 2, [("POUR-SET", 1), ("FILT-100", 2)]),
    ("delivered", "2026-08-22", 1, [("BEAN-1KG", 2)]),
    ("shipped", "2026-10-21", 2, [("GRIND-B1", 1)]),
    ("paid", "2026-10-25", None, [("KETL-GN", 1), ("SCALE-D", 1)]),
    ("pending", "2026-10-27", None, [("BEAN-1KG", 1), ("CLEAN-30", 1)]),
]
TODAY = date(2026, 10, 28)  # the data is a snapshot as of this day


def _status_for_age(rng: random.Random, age_days: int) -> str:
    """Older orders have finished; only recent ones can still be waiting."""
    if age_days <= 3:
        return rng.choice(["pending", "paid", "paid", "shipped"])
    if age_days <= 10:
        return rng.choices(["paid", "shipped", "delivered", "cancelled"], [2, 4, 3, 1])[0]
    return rng.choices(["delivered", "refunded", "cancelled"], [17, 2, 1])[0]


def build_demo_db(path: str | Path, seed: int = 7) -> Path:
    """Write the fictional shop database. The same seed always gives the same data."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    rng = random.Random(seed)
    conn = sqlite3.connect(path)
    try:
        conn.executescript(SCHEMA)
        for i, (name, city) in enumerate(CUSTOMERS, 1):
            first, last = name.lower().split()
            created = date(2026, 6, 1) + timedelta(days=rng.randrange(0, 30))
            conn.execute("INSERT INTO customers VALUES (?, ?, ?, ?, ?)",
                         (i, name, f"{first}.{last}@example.com", city, created.isoformat()))
        for i, (sku, name, cents) in enumerate(PRODUCTS, 1):
            conn.execute("INSERT INTO products VALUES (?, ?, ?, ?)", (i, sku, name, cents))
        product_id = {sku: i for i, (sku, _, _) in enumerate(PRODUCTS, 1)}
        price = {sku: cents for sku, _, cents in PRODUCTS}

        # (placed, customer, status, days to ship, lines), numbered by date afterwards
        orders = [(date.fromisoformat(placed), 1, status, ship_days, lines)
                  for status, placed, ship_days, lines in PINNED]
        first_day = date(2026, 7, 1)
        for _ in range(55):
            placed = first_day + timedelta(days=rng.randrange(0, (TODAY - first_day).days + 1))
            status = _status_for_age(rng, (TODAY - placed).days)
            skus = rng.sample(list(price), rng.randrange(1, 4))
            orders.append((placed, rng.randrange(2, len(CUSTOMERS) + 1), status, rng.randrange(1, 4),
                           [(sku, rng.randrange(1, 3)) for sku in skus]))
        orders.sort(key=lambda o: (o[0], o[1]))

        for order_id, (placed, customer_id, status, ship_days, lines) in enumerate(orders, 1001):
            shipped = None
            if status in ("shipped", "delivered", "refunded") and ship_days is not None:
                shipped = min(placed + timedelta(days=ship_days), TODAY).isoformat()
            conn.execute("INSERT INTO orders VALUES (?, ?, ?, ?, ?)",
                         (order_id, customer_id, status, placed.isoformat(), shipped))
            for sku, qty in lines:
                conn.execute("INSERT INTO order_items VALUES (?, ?, ?, ?)",
                             (order_id, product_id[sku], qty, price[sku]))
        conn.commit()
    finally:
        conn.close()
    return path
