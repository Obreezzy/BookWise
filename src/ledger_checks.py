from schemas import LedgerPage

TOLERANCE = 0.01
COLUMNS = ["amount", "money_in", "money_out", "owed", "paid"]


def label(row):
    return row.date.strftime("%d %b %Y") if row.date else "unknown date"


def check_ledger(page: LedgerPage) -> list[str]:
    flags = []
    sums = {c: 0.0 for c in COLUMNS}   # entries since the last total row
    prev_balance = None
    seen_date_text = False

    for n, row in enumerate(page.rows, start=1):
        if row.date_written:
            seen_date_text = True
            if row.date is None:
                flags.append(f"BAD_DATE: row {n}: could not understand '{row.date_written}'")

        if row.row_type == "balance_bf":
            prev_balance = row.balance
            continue

        if row.row_type == "entry":
            if row.date is None and not seen_date_text:
                flags.append(f"MISSING_DATE: row {n} ({row.details})")
            if row.money_in is not None and row.money_out is not None:
                flags.append(f"BOTH_IN_AND_OUT: row {n} ({row.details})")
            if all(getattr(row, c) is None for c in COLUMNS):
                flags.append(f"EMPTY_ENTRY: row {n} ({row.details}) has no amount")
            if (row.details or "").strip().lower().startswith("total"):
                flags.append(f"TOTAL_LABEL_ON_ENTRY: row {n} ({row.details}) looks like a total row")
            for c in COLUMNS:
                sums[c] += getattr(row, c) or 0

            if row.balance is not None:
                if prev_balance is not None:
                    if page.book_type == "cash_book":
                        expected = prev_balance + (row.money_in or 0) - (row.money_out or 0)
                    elif page.book_type == "credit_ledger":
                        expected = prev_balance + (row.owed or 0) - (row.paid or 0)
                    else:
                        expected = None
                    if expected is not None and abs(round(expected, 2) - row.balance) > TOLERANCE:
                        flags.append(f"BALANCE_MISMATCH: row {n} ({row.details}): "
                                     f"should be {round(expected, 2)} but page says {row.balance}")
                prev_balance = row.balance

        elif row.row_type == "total":
            for c in COLUMNS:
                written = getattr(row, c)
                if written is not None and abs(round(sums[c], 2) - written) > TOLERANCE:
                    flags.append(f"TOTAL_MISMATCH: row {n} ({label(row)}) {c}: "
                                 f"entries add up to {round(sums[c], 2)} but page says {written}")

            if row.balance is not None and prev_balance is not None \
                    and abs(row.balance - prev_balance) > TOLERANCE:
                flags.append(f"CLOSING_BALANCE_MISMATCH: row {n}: total row says {row.balance} "
                             f"but the last running balance was {prev_balance}")

            sums = {c: 0.0 for c in COLUMNS}

    entry_rows = [r for r in page.rows if r.row_type == "entry"]
    if entry_rows and page.rows[-1].row_type != "total":
        flags.append("NO_TOTAL_ROW: the page ends without a total row; "
                     "rows may be missing at the bottom")

    return flags