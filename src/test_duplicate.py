import datetime
from types import SimpleNamespace as NS

from confirm import SOFT_FLAGS, duplicate_flag, soft_flags
from db import connect, save_receipt, confirm_receipt, find_duplicate


def make(vendor="stitch perfect", date=datetime.date(2026, 9, 22), total=40.05):
    item = NS(description="Zip", quantity=1, unit_price=total, line_total=total)
    return NS(vendor=vendor, date_written="22/09/26", date=date,
              currency="USD", total=total, items=[item])


conn = connect(":memory:")
save_receipt(conn, "b", "first.jpg", make(), [])

# 1. An unconfirmed earlier receipt is not a duplicate.
assert find_duplicate(conn, "b", "second.jpg", make()) is None

# 2. Once confirmed, the same vendor, date and total is a duplicate.
assert confirm_receipt(conn, "b", "first.jpg") is True
match = find_duplicate(conn, "b", "second.jpg", make())
assert match is not None and match[0] == "first.jpg"

# 3. A different total, date, vendor or business is not.
assert find_duplicate(conn, "b", "second.jpg", make(total=40.06)) is None
assert find_duplicate(conn, "b", "second.jpg", make(date=datetime.date(2026, 9, 23))) is None
assert find_duplicate(conn, "b", "second.jpg", make(vendor="Other Shop")) is None
assert find_duplicate(conn, "other_business", "second.jpg", make()) is None

# 4. The same file is never a duplicate of itself.
assert find_duplicate(conn, "b", "first.jpg", make()) is None

# 5. No date or no vendor: never matched.
assert find_duplicate(conn, "b", "second.jpg", make(date=None)) is None
assert find_duplicate(conn, "b", "second.jpg", make(vendor=None)) is None

# 6. The flag text names the earlier receipt and is soft.
flag = duplicate_flag(make(), match)
assert flag.startswith("POSSIBLE_DUPLICATE")
assert "Stitch Perfect" in flag and "22 Sep 2026" in flag and "$40.05" in flag
assert soft_flags([flag]) == [flag]

# 7. A duplicate with only that flag can be confirmed by the shopkeeper.
save_receipt(conn, "b", "second.jpg", make(), [flag])
assert confirm_receipt(conn, "b", "second.jpg") is False
assert confirm_receipt(conn, "b", "second.jpg", SOFT_FLAGS) is True

print("duplicate tests passed")