import datetime
from schemas import Receipt
from checks import check_receipt
from sent_date import check_sent_date

# Soft flags are a question for the shopkeeper, not a reading failure.
# The shopkeeper can answer YES to them. Every other flag is hard.
SOFT_FLAGS = {"DATE_FAR_FROM_SENT", "DATE_TOO_OLD", "POSSIBLE_DUPLICATE"}


def money(x, currency="USD"):
    sign = "$" if currency == "USD" else currency + " "
    return f"{sign}{x:,.2f}"


def flag_code(flag):
    return flag.partition(": ")[0]


def hard_flags(flags):
    return [f for f in flags if flag_code(f) not in SOFT_FLAGS]


def soft_flags(flags):
    return [f for f in flags if flag_code(f) in SOFT_FLAGS]


def friendly(flag):
    """Turns 'TOTAL_MISMATCH: items add up to ...' into plain words."""
    code, _, rest = flag.partition(": ")
    if code == "DATE_TOO_OLD":
        return f"the date {rest} looks too old"
    return rest or code


def all_flags(receipt: Receipt, sent_on: datetime.date | None = None) -> list[str]:
    """The receipt checks plus, when we know the send date, the send-date rule."""
    flags = check_receipt(receipt)
    if sent_on is not None:
        sent_flags = check_sent_date(receipt, sent_on)
        if sent_flags:
            flags = [f for f in flags if not f.startswith("DATE_TOO_OLD")] + sent_flags
    return flags


def duplicate_flag(receipt, match):
    """match is the row from db.find_duplicate: (source_file, vendor, date, total_cents)."""
    shown = datetime.date.fromisoformat(match[2]).strftime("%d %b %Y")
    amount = money(match[3] / 100, receipt.currency)
    return (f"POSSIBLE_DUPLICATE: you already confirmed a receipt from {match[1]} "
            f"dated {shown} for {amount} (reply YES only if this is a different receipt)")


def confirmation_message(receipt: Receipt, sent_on: datetime.date | None = None,
                         flags: list[str] | None = None) -> str:
    """flags: pass the full list (including a duplicate flag) if you have it.
    If left out, the receipt checks and the send-date rule are used."""
    lines = [f"I read this receipt from {receipt.vendor or 'an unknown shop'}:"]
    if receipt.date:
        read = f" (I read: {receipt.date_written})" if receipt.date_written else ""
        lines.append(f"Date: {receipt.date.strftime('%d %b %Y')}{read}")
    else:
        lines.append(f"Date: I could not understand it (I read: {receipt.date_written or 'nothing'})")

    for item in receipt.items:
        if item.unit_price is not None:
            lines.append(f"- {item.description}: {item.quantity:g} x {money(item.unit_price, receipt.currency)}"
                         f" = {money(item.line_total, receipt.currency)}")
        else:
            lines.append(f"- {item.description}: {money(item.line_total, receipt.currency)}")
    lines.append(f"Total: {money(receipt.total, receipt.currency)}")

    if flags is None:
        flags = all_flags(receipt, sent_on)
    lines.append("")
    if hard_flags(flags):
        lines.append("Something does not add up:")
        for f in flags:
            lines.append(f"- {friendly(f)}")
        lines.append("Please send a clearer photo.")
    else:
        lines.append("Please check the date and total against your paper.")
        for f in soft_flags(flags):
            lines.append(f"Note: {friendly(f)}.")
        lines.append("Is this right? Reply YES, or send a clearer photo.")
    return "\n".join(lines)