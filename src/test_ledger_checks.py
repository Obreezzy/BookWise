from schemas import LedgerPage
from ledger_dates import fill_dates
from ledger_checks import check_ledger

def build(book_type, rows):
    return fill_dates(LedgerPage.model_validate({"book_type": book_type, "rows": rows}))

def codes(page):
    return [f.split(":")[0] for f in check_ledger(page)]

# 1. page_005 exactly as the AI read it (two digits dropped)
sales = build("sales_book", [
    {"row_type": "entry", "date_written": "23 Sep", "details": "Nails 1kg", "amount": 14.0},
    {"row_type": "entry", "details": "Cement bag", "amount": 13.5},
    {"row_type": "entry", "details": "Sand", "amount": 51.0},
    {"row_type": "entry", "details": "Nails 1kg", "amount": 5.6},
    {"row_type": "entry", "details": "Padlock", "amount": 5.0},      # truth 15.0
    {"row_type": "total", "amount": 99.1},
    {"row_type": "entry", "date_written": "24 Sep", "details": "Sand", "amount": 12.0},   # truth 120.0
    {"row_type": "entry", "details": "Nails 1kg", "amount": 5.6},
    {"row_type": "entry", "details": "Cement bag", "amount": 13.5},
    {"row_type": "total", "amount": 139.1},
    {"row_type": "entry", "date_written": "25 Sep", "details": "Cement 50kg", "amount": 24.0},
    {"row_type": "entry", "details": "Paint 5lt white", "amount": 18.5},
    {"row_type": "entry", "details": "Iron sheet", "amount": 34.5},
    {"row_type": "entry", "details": "Cement bag", "amount": 65.0},
    {"row_type": "total", "amount": 142.0},
])
assert codes(sales) == ["TOTAL_MISMATCH", "TOTAL_MISMATCH"]
assert "89.1" in check_ledger(sales)[0] and "23 Sep" in check_ledger(sales)[0]

# 2. cash book: one wrong running balance (row 4 should be 130.0)
cash = build("cash_book", [
    {"row_type": "balance_bf", "date_written": "1 Oct", "balance": 100.0},
    {"row_type": "entry", "details": "Sales", "money_in": 50.0, "balance": 150.0},
    {"row_type": "entry", "details": "Stock", "money_out": 30.0, "balance": 120.0},
    {"row_type": "entry", "details": "Sales", "money_in": 10.0, "balance": 140.0},
    {"row_type": "entry", "details": "Sales", "money_in": 5.0, "balance": 145.0},
    {"row_type": "total", "money_in": 65.0, "money_out": 30.0},
])
assert codes(cash) == ["BALANCE_MISMATCH"]

# 3. unreadable date: flagged once, and not repeated on the rows after it
bad = build("sales_book", [
    {"row_type": "entry", "date_written": "45/13", "details": "a", "amount": 1.0},
    {"row_type": "entry", "details": "b", "amount": 1.0},
    {"row_type": "total", "amount": 2.0},
])
assert codes(bad) == ["BAD_DATE"]

# 4. closing balance: matching is fine, a different figure is flagged
ok = build("credit_ledger", [
    {"row_type": "balance_bf", "balance": 10.0},
    {"row_type": "entry", "date_written": "1 Oct", "details": "Airtime", "owed": 5.0, "balance": 15.0},
    {"row_type": "total", "balance": 15.0},
])
assert codes(ok) == []

wrong = build("credit_ledger", [
    {"row_type": "balance_bf", "balance": 10.0},
    {"row_type": "entry", "date_written": "1 Oct", "details": "Airtime", "owed": 5.0, "balance": 15.0},
    {"row_type": "total", "balance": 20.0},
])
assert codes(wrong) == ["CLOSING_BALANCE_MISMATCH"]

# 5. page cut off before its total row
cut = build("sales_book", [
    {"row_type": "entry", "date_written": "1 Oct", "details": "a", "amount": 1.0},
])
assert codes(cut) == ["NO_TOTAL_ROW"]

# 6. page_039 shape: an entry with no amount, and a total typed as an entry
shifted = build("cash_book", [
    {"row_type": "balance_bf", "date_written": "28 Sep", "balance": 100.0},
    {"row_type": "entry", "details": "Cash sales", "balance": 100.0},
    {"row_type": "entry", "details": "Day sales", "money_in": 10.0, "balance": 110.0},
    {"row_type": "entry", "details": "TOTAL", "money_in": 5.0, "balance": 115.0},
    {"row_type": "total", "money_in": 15.0},
])
assert codes(shifted) == ["EMPTY_ENTRY", "TOTAL_LABEL_ON_ENTRY"]

# 7. a normal entry is not flagged by the new checks
fine = build("sales_book", [
    {"row_type": "entry", "date_written": "1 Oct", "details": "New paint", "amount": 3.0},
    {"row_type": "total", "amount": 3.0},
])
assert codes(fine) == []

print("All ledger check tests passed")