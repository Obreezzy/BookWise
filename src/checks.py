import datetime
from schemas import Receipt

TOLERANCE = 0.01      # allow 1 cent for rounding
MAX_AGE_DAYS = 400    # a receipt older than this is probably a misread date


def check_receipt(r: Receipt, today: datetime.date | None = None) -> list[str]:
    """Return a list of problems. An empty list means the receipt looks fine."""
    today = today or datetime.date.today()
    flags = []

    # 1. Do the line items add up to the written total?
    items_sum = round(sum(i.line_total for i in r.items), 2)
    if abs(items_sum - r.total) > TOLERANCE:
        flags.append(f"TOTAL_MISMATCH: items add up to {items_sum} but total says {r.total}")

    # 2. Does quantity x price equal each line's amount?
    for n, item in enumerate(r.items, start=1):
        if item.unit_price is not None:
            expected = round(item.quantity * item.unit_price, 2)
            if abs(expected - item.line_total) > TOLERANCE:
                flags.append(
                    f"LINE_MISMATCH: row {n} ({item.description}): "
                    f"{item.quantity} x {item.unit_price} = {expected}, but line says {item.line_total}"
                )

    # 3. Is the date present and believable?
    if r.date is None:
        if r.date_written:
            flags.append(f"BAD_DATE: could not understand '{r.date_written}'")
        else:
            flags.append("MISSING_DATE")
    elif r.date > today + datetime.timedelta(days=1):
        flags.append(f"DATE_IN_FUTURE: {r.date}")
    elif (today - r.date).days > MAX_AGE_DAYS:
        flags.append(f"DATE_TOO_OLD: {r.date}")

    if r.vendor is None:
        flags.append("MISSING_VENDOR")

    return flags