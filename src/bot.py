import os
from confirm import (SOFT_FLAGS, all_flags, confirmation_message,
                     duplicate_flag)
from db import confirm_receipt, find_duplicate, save_receipt

PENDING = {}    # user_id -> source_file waiting for a YES (lost if the program restarts)
YES_WORDS = {"yes", "y", "yeah", "correct", "right", "ok", "okay"}


def handle_photo(conn, business_id, user_id, image_path, sent_on, extract):
    """extract(image_path) must return (Receipt, tries) or raise RuntimeError."""
    try:
        receipt, _ = extract(image_path)
    except RuntimeError:
        return "I could not read that photo. Please send a clearer one."
    source_file = os.path.basename(image_path)
    flags = all_flags(receipt, sent_on)
    match = find_duplicate(conn, business_id, source_file, receipt)
    if match:
        flags = flags + [duplicate_flag(receipt, match)]
    save_receipt(conn, business_id, source_file, receipt, flags)
    PENDING[user_id] = source_file
    return confirmation_message(receipt, sent_on, flags)


def handle_text(conn, business_id, user_id, text):
    source_file = PENDING.get(user_id)
    if source_file is None:
        return "I have nothing waiting for you. Send me a photo of a receipt."
    if text.strip().lower() in YES_WORDS:
        if confirm_receipt(conn, business_id, source_file, SOFT_FLAGS):
            del PENDING[user_id]
            return "Thank you. That receipt is saved and confirmed."
        return ("That receipt has warnings, so I cannot confirm it yet. "
                "Please send a clearer photo.")
    return "I cannot change details yet. Please send a clearer photo."