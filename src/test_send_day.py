import datetime
from send_day import local_send_date

UTC = datetime.timezone.utc

# 00:30 Harare on 4 Nov is 22:30 UTC on 3 Nov. The shop's date is the 4th.
late = datetime.datetime(2026, 11, 3, 22, 30, tzinfo=UTC)
assert local_send_date(late) == datetime.date(2026, 11, 4)

# Midday is the same date in both.
noon = datetime.datetime(2026, 11, 4, 10, 0, tzinfo=UTC)
assert local_send_date(noon) == datetime.date(2026, 11, 4)

print("send day tests passed")