import datetime
from schemas import LedgerPage
from ledger_dates import fill_dates

D = datetime.date

def row(row_type, written=None):
    return {"row_type": row_type, "date_written": written}

page = LedgerPage.model_validate({"book_type": "sales_book", "rows": [
    row("entry", "23 Sep"),
    row("entry"),
    row("total"),
    row("entry", "24 Sep"),
    row("entry"),
    row("entry", "45/13"),   # unreadable date
    row("entry"),
    row("entry", "25 Sep"),
]})
fill_dates(page)
dates = [r.date for r in page.rows]

assert dates == [D(2026, 9, 23), D(2026, 9, 23), D(2026, 9, 23),
                 D(2026, 9, 24), D(2026, 9, 24),
                 None, None,
                 D(2026, 9, 25)]
print("All ledger date tests passed")