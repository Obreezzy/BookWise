import datetime
from schemas import Receipt

MAX_DAYS_BEFORE = 14   # receipts older than this are unusual
MAX_DAYS_AFTER = 1     # a receipt dated after the day it was sent is almost always a misread


def check_sent_date(receipt: Receipt, sent_on: datetime.date) -> list[str]:
    if receipt.date is None:
        return []
    days = (sent_on - receipt.date).days
    shown = receipt.date.strftime("%d %b %Y")
    if days < -MAX_DAYS_AFTER:
        return [f"DATE_AFTER_SENT: the date {shown} is {-days} days after the day you sent this photo"]
    if days > MAX_DAYS_BEFORE:
        return [f"DATE_FAR_FROM_SENT: the date {shown} is {days} days before the day you sent this photo"]
    return []