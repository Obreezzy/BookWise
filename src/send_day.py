import datetime
from zoneinfo import ZoneInfo

SHOP_TIMEZONE = ZoneInfo("Africa/Harare")


def local_send_date(message_time):
    """Telegram gives the send time in UTC. Return the date in Harare."""
    return message_time.astimezone(SHOP_TIMEZONE).date()