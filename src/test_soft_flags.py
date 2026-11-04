import datetime
from types import SimpleNamespace as NS

from confirm import SOFT_FLAGS, hard_flags, soft_flags
from db import connect, save_receipt, confirm_receipt

item = NS(description="Zip", quantity=1, unit_price=1.48, line_total=1.48)
receipt = NS(vendor="Shop", date_written="22/09/26", date=datetime.date(2026, 9, 22),
             currency="USD", total=1.48, items=[item])

OLD = "DATE_FAR_FROM_SENT: the date 22 Sep 2026 is 43 days before the day you sent this photo"
BAD = "TOTAL_MISMATCH: items add up to 1.48 but the total says 9.99"


def state(conn):
    return conn.execute("SELECT status, user_confirmed FROM receipts").fetchone()


# 1. Only a soft flag: blocked without soft_codes, allowed with them.
conn = connect(":memory:")
save_receipt(conn, "b", "a.jpg", receipt, [OLD])
assert confirm_receipt(conn, "b", "a.jpg") is False
assert confirm_receipt(conn, "b", "a.jpg", SOFT_FLAGS) is True
assert state(conn) == ("passed_checks", 1)

# 2. A hard flag can never be confirmed.
conn = connect(":memory:")
save_receipt(conn, "b", "a.jpg", receipt, [BAD])
assert confirm_receipt(conn, "b", "a.jpg", SOFT_FLAGS) is False
assert state(conn) == ("needs_review", 0)

# 3. A soft flag together with a hard one cannot be confirmed.
conn = connect(":memory:")
save_receipt(conn, "b", "a.jpg", receipt, [OLD, BAD])
assert confirm_receipt(conn, "b", "a.jpg", SOFT_FLAGS) is False

# 4. No flags: confirmed as before.
conn = connect(":memory:")
save_receipt(conn, "b", "a.jpg", receipt, [])
assert confirm_receipt(conn, "b", "a.jpg") is True

# 5. The flag split.
assert soft_flags([OLD, BAD]) == [OLD]
assert hard_flags([OLD, BAD]) == [BAD]

print("soft flag tests passed")