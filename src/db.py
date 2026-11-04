import sqlite3
from string import capwords

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


def ensure_column(conn, table, column, definition):
    """Adds a column to an existing table if it is not there yet."""
    existing = [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def connect(path=DB_PATH):
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    ensure_column(conn, "receipts", "user_confirmed", "INTEGER NOT NULL DEFAULT 0")
    ensure_column(conn, "receipts", "confirmed_at", "TEXT")
    conn.commit()
    return conn


def cents(amount):
    return None if amount is None else round(amount * 100)


def clean_vendor(name: str | None) -> str | None:
    """Make vendor names consistent: collapse spaces and use Title Case."""
    if not name:
        return None
    return capwords(name)


def clean_description(text: str | None) -> str | None:
    """Make item descriptions consistent: collapse spaces and use Title Case."""
    if not text:
        return None
    return capwords(text)


def save_receipt(conn, business_id, source_file, receipt, flags):
    """Saves a receipt and its items, replacing any earlier version of the same file.
    A re-read receipt may have different numbers, so user_confirmed goes back to 0."""
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


def confirm_receipt(conn, business_id, source_file, soft_codes=()):
    """The shopkeeper said YES.
    A receipt that passed the checks can always be confirmed. A flagged receipt can be
    confirmed only if EVERY flag on it is in soft_codes (a question the shopkeeper can
    answer, such as an old date). Then status becomes 'passed_checks', because the only
    warnings were ones the shopkeeper resolved. The flag text stays in the flags column.
    Returns True if confirmed, False if the receipt is missing or has a hard flag."""
    row = conn.execute(
        "SELECT status, flags FROM receipts WHERE business_id = ? AND source_file = ?",
        (business_id, source_file)).fetchone()
    if row is None:
        return False
    status, flags = row
    if status != "passed_checks":
        codes = [f.partition(": ")[0] for f in (flags or "").split("; ") if f]
        if not codes or any(code not in soft_codes for code in codes):
            return False
    conn.execute(
        """UPDATE receipts SET user_confirmed = 1, confirmed_at = CURRENT_TIMESTAMP,
                               status = 'passed_checks'
           WHERE business_id = ? AND source_file = ?""",
        (business_id, source_file))
    conn.commit()
    return True




def find_duplicate(conn, business_id, source_file, receipt):
    """Returns (source_file, vendor, date, total_cents) of an already CONFIRMED receipt
    from the same business with the same vendor, date and total, or None.
    Receipts with no vendor or no readable date are never matched."""
    if receipt.date is None or not receipt.vendor:
        return None
    return conn.execute(
        """SELECT source_file, vendor, date, total_cents FROM receipts
           WHERE business_id = ? AND source_file != ? AND user_confirmed = 1
             AND vendor = ? AND date = ? AND total_cents = ?""",
        (business_id, source_file, clean_vendor(receipt.vendor),
         receipt.date.isoformat(), cents(receipt.total))).fetchone()