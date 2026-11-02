from schemas import LedgerPage
from dates import parse_date


def fill_dates(page: LedgerPage) -> LedgerPage:
    """The AI only copies date_written. This code decides every date."""
    last_date = None
    for row in page.rows:
        if row.date_written:                    # a date was written on this row
            last_date = parse_date(row.date_written)   # None if unreadable
        row.date = last_date                    # blank cell = same day as the row above
    return page