from db import connect, save_receipt, confirm_receipt
from schemas import Receipt


def make(total):
    return Receipt.model_validate({"vendor": "tendai's braiding", "date": "2026-09-26",
                                   "items": [{"description": "gel nails", "line_total": total}],
                                   "total": total})


conn = connect(":memory:")
save_receipt(conn, "shop", "a.jpg", make(5.0), [])                      # passed checks
save_receipt(conn, "shop", "b.jpg", make(6.0), ["TOTAL_MISMATCH: x"])   # flagged


def row(name):
    return conn.execute("SELECT status, user_confirmed, confirmed_at, vendor "
                        "FROM receipts WHERE source_file = ?", (name,)).fetchone()


assert row("a.jpg")[:2] == ("passed_checks", 0)
assert row("a.jpg")[3] == "Tendai's Braiding"                           # no more "Tendai'S"
assert confirm_receipt(conn, "shop", "a.jpg") is True
status, confirmed, when, _ = row("a.jpg")
assert status == "passed_checks" and confirmed == 1 and when is not None
assert confirm_receipt(conn, "shop", "b.jpg") is False                  # flagged: cannot be confirmed
assert row("b.jpg")[1] == 0
assert confirm_receipt(conn, "shop", "missing.jpg") is False            # unknown receipt
save_receipt(conn, "shop", "a.jpg", make(5.5), [])                      # re-read with new numbers
assert row("a.jpg")[1] == 0                                             # old confirmation no longer applies
print("Confirmation tests passed")