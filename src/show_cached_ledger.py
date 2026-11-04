import json, sys
from schemas import LedgerPage
from ledger_checks import check_ledger

name = sys.argv[1]
res = json.load(open("results_ledgers.json"))[name]
page = LedgerPage.model_validate(res["page"])
print("book_type:", page.book_type, "| rows:", len(page.rows))
for n, r in enumerate(page.rows, start=1):
    print(f"{n:>3} {r.row_type:10} {str(r.date):10} {r.details or '':22} "
          f"qty={r.qty} amt={r.amount} in={r.money_in} out={r.money_out} "
          f"owed={r.owed} paid={r.paid} bal={r.balance}")
print("flags:", check_ledger(page))