import datetime
from schemas import Receipt
from sent_date import check_sent_date

D = datetime.date


def receipt(date):
    return Receipt.model_validate({"vendor": "x", "date": date,
                                   "items": [{"description": "a", "line_total": 1.0}], "total": 1.0})


def codes(date, sent):
    return [f.split(":")[0] for f in check_sent_date(receipt(date), sent)]


assert codes("2026-09-26", D(2026, 9, 27)) == []                       # normal: sent the day after
assert codes("2026-09-20", D(2026, 9, 27)) == []                       # a week old is fine
assert codes("2026-10-26", D(2026, 9, 27)) == ["DATE_AFTER_SENT"]      # receipt_040: a month ahead
assert codes("2026-01-07", D(2026, 10, 7)) == ["DATE_FAR_FROM_SENT"]   # receipt_048: 273 days old
assert codes("2026-09-26", D(2026, 9, 6)) == ["DATE_AFTER_SENT"]       # receipt_015, sent on the true date
assert codes("2026-10-09", D(2026, 10, 7)) == ["DATE_AFTER_SENT"]      # receipt_046, sent the same day
assert codes("2026-10-09", D(2026, 10, 8)) == []                       # receipt_046 sent a day later: NOT caught
assert check_sent_date(receipt(None), D(2026, 9, 27)) == []            # no date: nothing to compare
print("Sent-date tests passed")