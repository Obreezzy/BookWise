import datetime
from checks import check_receipt
from schemas import Receipt

TODAY = datetime.date(2026, 10, 22)


def make(date, total=15.26, written="x"):
    return Receipt(
        vendor="Shop", date_written=written, date=date, total=total,
        items=[
            {"description": "a", "quantity": 1, "unit_price": 1.51, "line_total": 1.51},
            {"description": "b", "quantity": 1, "unit_price": 13.75, "line_total": 13.75},
        ],
    )


def codes(r):
    return [f.split(":")[0] for f in check_receipt(r, today=TODAY)]


assert codes(make(datetime.date(2026, 10, 1))) == []                       # healthy receipt
assert "DATE_TOO_OLD" in codes(make(datetime.date(2024, 10, 1)))           # the 2024 case
assert "DATE_IN_FUTURE" in codes(make(datetime.date(2027, 3, 1)))
assert "TOTAL_MISMATCH" in codes(make(datetime.date(2026, 10, 1), total=25.26))
assert "BAD_DATE" in codes(make(None, written="45/13/26"))                 # unreadable date text
assert "MISSING_DATE" in codes(make(None, written=None))                   # no date at all
print("All check tests passed")