import re
from collections import defaultdict
from db import connect

BUSINESS = "demo_shop"
conn = connect()


def normalize(text):
    """'Dress (sewn)' and 'dress sewn' become the same key."""
    letters = re.sub(r"[^a-z0-9 ]", " ", (text or "").lower())
    return re.sub(r"\s+", " ", letters).strip()


print("Spending per month (confirmed by you | passed checks, not confirmed | waiting for review):")
for month, n_c, c, n_p, p, n_r, r in conn.execute("""
        SELECT COALESCE(substr(date, 1, 7), 'no date'),
               SUM(user_confirmed = 1),
               COALESCE(SUM(CASE WHEN user_confirmed = 1 THEN total_cents END), 0) / 100.0,
               SUM(status = 'passed_checks' AND user_confirmed = 0),
               COALESCE(SUM(CASE WHEN status = 'passed_checks' AND user_confirmed = 0
                                 THEN total_cents END), 0) / 100.0,
               SUM(status = 'needs_review'),
               COALESCE(SUM(CASE WHEN status = 'needs_review' THEN total_cents END), 0) / 100.0
        FROM receipts WHERE business_id = ?
        GROUP BY 1 ORDER BY 1""", (BUSINESS,)):
    print(f"  {month}: confirmed {n_c} ${c:,.2f}  |  passed checks {n_p} ${p:,.2f}"
          f"  |  waiting for review {n_r} ${r:,.2f}")

print("\nTop 5 things bought (receipts that passed checks, confirmed or not):")
totals = defaultdict(float)
for description, cents in conn.execute("""
        SELECT i.description, i.line_total_cents
        FROM items i JOIN receipts r ON r.id = i.receipt_id
        WHERE r.business_id = ? AND r.status = 'passed_checks'""", (BUSINESS,)):
    totals[normalize(description)] += cents / 100.0
for item, total in sorted(totals.items(), key=lambda kv: -kv[1])[:5]:
    print(f"  {item}: ${total:,.2f}")

print("\nReceipts needing review:")
for file, vendor, flags in conn.execute("""
        SELECT source_file, vendor, flags FROM receipts
        WHERE business_id = ? AND status = 'needs_review' ORDER BY source_file""", (BUSINESS,)):
    print(f"  {file} ({vendor}): {flags}")