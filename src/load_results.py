import json
from checks import check_receipt
from db import connect, save_receipt
from schemas import Receipt

BUSINESS = "demo_shop"

results = json.load(open("results_receipts.json"))
conn = connect()
saved = skipped = 0
for name, res in sorted(results.items()):
    if not res["ok"]:
        continue
    receipt = Receipt.model_validate(res["receipt"])
    flags = check_receipt(receipt)
    if save_receipt(conn, BUSINESS, name, receipt, flags):
        saved += 1
    else:
        skipped += 1
print(f"Saved {saved} new receipts, skipped {skipped} already in the database")