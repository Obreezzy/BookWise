from db import connect

BUSINESS = "demo_shop"
conn = connect()

print("Spending per month (passed checks vs waiting for review):")
for month, n_ok, ok, n_rev, rev in conn.execute("""
        SELECT COALESCE(substr(date, 1, 7), 'no date'),
               SUM(status = 'passed_checks'),
               COALESCE(SUM(CASE WHEN status = 'passed_checks' THEN total_cents END), 0) / 100.0,
               SUM(status = 'needs_review'),
               COALESCE(SUM(CASE WHEN status = 'needs_review' THEN total_cents END), 0) / 100.0
        FROM receipts WHERE business_id = ?
        GROUP BY 1 ORDER BY 1""", (BUSINESS,)):
    print(f"  {month}: {n_ok} passed checks ${ok:,.2f}  |  {n_rev} waiting for review ${rev:,.2f}")

print("\nTop 5 things bought (passed checks only):")
for item, total in conn.execute("""
        SELECT lower(i.description), SUM(i.line_total_cents) / 100.0
        FROM items i JOIN receipts r ON r.id = i.receipt_id
        WHERE r.business_id = ? AND r.status = 'passed_checks'
        GROUP BY lower(i.description) ORDER BY 2 DESC LIMIT 5""", (BUSINESS,)):
    print(f"  {item}: ${total:,.2f}")

print("\nReceipts needing review:")
for file, vendor, flags in conn.execute("""
        SELECT source_file, vendor, flags FROM receipts
        WHERE business_id = ? AND status = 'needs_review' ORDER BY source_file""", (BUSINESS,)):
    print(f"  {file} ({vendor}): {flags}")