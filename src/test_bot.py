import datetime, json, os
from evaluate import CACHE
from schemas import Receipt
from db import connect
import bot

D = datetime.date
results = json.load(open(CACHE))


def fake_extract(path):
    return Receipt.model_validate(results[os.path.basename(path)]["receipt"]), 1


def broken_extract(path):
    raise RuntimeError("could not read")


def row(conn, name):
    return conn.execute("SELECT status, user_confirmed FROM receipts WHERE source_file = ?",
                        (name,)).fetchone()


conn = connect(":memory:")
bot.PENDING.clear()

# 1. a normal receipt: asked to confirm, then YES confirms it
reply = bot.handle_photo(conn, "shop", "u1", "photos/receipt_001.jpg", D(2026, 10, 2), fake_extract)
assert "Is this right?" in reply and bot.PENDING["u1"] == "receipt_001.jpg"
assert "confirmed" in bot.handle_text(conn, "shop", "u1", "YES")
assert row(conn, "receipt_001.jpg") == ("passed_checks", 1) and "u1" not in bot.PENDING

# 2. a flagged receipt: YES is refused and nothing is confirmed
reply = bot.handle_photo(conn, "shop", "u2", "photos/receipt_025.jpg", D(2026, 10, 9), fake_extract)
assert "Something does not add up" in reply
assert "cannot confirm" in bot.handle_text(conn, "shop", "u2", "yes")
assert row(conn, "receipt_025.jpg") == ("needs_review", 0)

# 3. receipt_040 passed every receipt check, but the send-date rule flags it
reply = bot.handle_photo(conn, "shop", "u3", "photos/receipt_040.jpg", D(2026, 9, 26), fake_extract)
assert "30 days after" in reply
assert row(conn, "receipt_040.jpg") == ("needs_review", 0)

# 4. a text with nothing waiting
assert "nothing waiting" in bot.handle_text(conn, "shop", "nobody", "yes")

# 5. a photo the model cannot read
assert "could not read" in bot.handle_photo(conn, "shop", "u4", "photos/x.jpg", D(2026, 10, 2), broken_extract)
assert "u4" not in bot.PENDING

print("Bot tests passed")