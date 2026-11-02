from schemas import LedgerPage
from ledger_fix import suggest_fixes

page = LedgerPage.model_validate({"book_type": "cash_book", "rows": [
    {"row_type": "balance_bf", "balance": 37.74},
    {"row_type": "entry", "details": "Sales", "money_in": 23.81, "balance": 61.55},
    {"row_type": "entry", "details": "Sold stock", "money_in": 36.08, "balance": 98.63},
    {"row_type": "entry", "details": "Rent", "money_out": 10.0, "balance": 88.63},
]})
tips = suggest_fixes(page)
assert len(tips) == 1
assert "row 3" in tips[0] and "97.63" in tips[0] and "37.08" in tips[0]
print("Fix suggestion test passed")