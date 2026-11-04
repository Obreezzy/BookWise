from db import connect

conn = connect()
rows = conn.execute(
    """SELECT business_id, source_file, status, user_confirmed, confirmed_at
       FROM receipts WHERE business_id LIKE 'tg_%'"""
).fetchall()
for r in rows:
    print(tuple(r))
if not rows:
    print("nothing stored for Telegram users yet")
conn.close()
