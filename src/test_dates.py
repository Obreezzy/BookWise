import datetime
from dates import parse_date

D = datetime.date
assert parse_date("10/09/2026") == D(2026, 9, 10)   # the receipt 003 case
assert parse_date("3/10") == D(2026, 10, 3)          # no year -> 2026
assert parse_date("03.10") == D(2026, 10, 3)
assert parse_date("5 Oct") == D(2026, 10, 5)
assert parse_date("28/09/26") == D(2026, 9, 28)
assert parse_date("31/02/2026") is None              # impossible date
assert parse_date(None) is None
print("All date tests passed")