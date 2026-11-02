import sqlite3

DB_PATH = "bookwise.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS receipts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id   TEXT NOT NULL,
    source_file   TEXT NOT NULL,
    vendor        TEXT,
    date_written  TEXT,
    date          TEXT,
    currency      TEXT NOT NULL DEFAULT 'USD',
    total_cents   INTEGER NOT NULL,
    status        TEXT NOT NULL DEFAULT 'needs_review',
    flags         TEXT,
    created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (business_id, source_file)
);
CREATE TABLE IF NOT EXISTS items (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id       INTEGER NOT NULL REFERENCES receipts(id),
    description      TEXT,
    quantity         REAL,
    unit_price_cents INTEGER,
    line_total_cents INTEGER NOT NULL
);
"""


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def cents(amount):
    return None if amount is None else round(amount * 100)


def clean_vendor(name: str | None) -> str | None:
    """Make vendor names consistent: strip spaces and use Title Case."""
    if not name:
        return None
    return " ".join(name.strip().split()).title()

def clean_description(text: str | None) -> str | None:
    """Make item descriptions consistent: strip extra spaces and use Title Case."""
    if not text:
        return None
    return " ".join(text.strip().split()).title()


def save_receipt(conn, business_id, source_file, receipt, flags):
    """Save one receipt and its items. Returns False if it was already saved."""
    # Delete any previous version of this receipt so we can re-insert the latest data
    conn.execute(
        "DELETE FROM items WHERE receipt_id IN "
        "(SELECT id FROM receipts WHERE business_id = ? AND source_file = ?)",
        (business_id, source_file))
    conn.execute(
    "DELETE FROM receipts WHERE business_id = ? AND source_file = ?",
    (business_id, source_file))
    cur = conn.execute(
        """INSERT INTO receipts (business_id, source_file, vendor, date_written, date,
                         currency, total_cents, status, flags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    (business_id, source_file, clean_vendor(receipt.vendor), receipt.date_written,
    receipt.date.isoformat() if receipt.date else None,
    receipt.currency, cents(receipt.total),
    "needs_review" if flags else "passed_checks",
    "; ".join(flags)))
    receipt_id = cur.lastrowid
    for item in receipt.items:
        conn.execute(
            """INSERT INTO items (receipt_id, description, quantity, unit_price_cents, line_total_cents)
               VALUES (?, ?, ?, ?, ?)""",
            (receipt_id, clean_description(item.description), item.quantity,
             cents(item.unit_price), cents(item.line_total)))
    conn.commit()
    return True