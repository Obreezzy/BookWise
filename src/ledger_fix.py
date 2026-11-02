from schemas import LedgerPage

TOLERANCE = 0.01


def suggest_fixes(page: LedgerPage) -> list[str]:
    tips = []
    prev = None
    for n, row in enumerate(page.rows, start=1):
        if row.row_type == "balance_bf":
            prev = row.balance
            continue
        if row.row_type != "entry" or row.balance is None:
            continue
        if prev is not None and page.book_type in ("cash_book", "credit_ledger"):
            if page.book_type == "cash_book":
                plus, plus_name, minus, minus_name = row.money_in, "money in", row.money_out, "money out"
            else:
                plus, plus_name, minus, minus_name = row.owed, "owed", row.paid, "paid"
            expected = round(prev + (plus or 0) - (minus or 0), 2)
            gap = round(row.balance - expected, 2)
            if abs(gap) > TOLERANCE:
                options = [f"the balance should be {expected}"]
                if plus is not None:
                    options.append(f"the {plus_name} should be {round(plus + gap, 2)}")
                elif minus is not None:
                    options.append(f"the {minus_name} should be {round(minus - gap, 2)}")
                tips.append(f"row {n} ({row.details}): either " + " or ".join(options))
        prev = row.balance
    return tips