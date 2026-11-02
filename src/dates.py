import datetime
import re

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}


def parse_date(text, default_year=2026):
    """Turn a date as written on the page into a real date. Day always comes first."""
    if not text:
        return None
    t = text.strip().lower()
    day = month = year = None

    m = re.match(r"^(\d{1,2})[/.\-](\d{1,2})(?:[/.\-](\d{2,4}))?$", t)   # 10/09/2026, 3/10, 03.10
    if m:
        day, month, year = int(m[1]), int(m[2]), m[3]
    else:
        m = re.match(r"^(\d{1,2})\s*([a-z]{3})[a-z]*\.?,?\s*(\d{2,4})?$", t)  # 5 Oct, 5 October 2026
        if m and m[2] in MONTHS:
            day, month, year = int(m[1]), MONTHS[m[2]], m[3]
    if day is None:
        return None

    year = default_year if year is None else int(year)
    if year < 100:
        year += 2000
    try:
        return datetime.date(year, month, day)
    except ValueError:      # for example 31/02/2026 does not exist
        return None