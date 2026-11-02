import json
from schemas import LedgerPage
from ledger_checks import check_ledger

results = json.load(open("results_ledgers.json"))
for name, res in sorted(results.items()):
    if not res["ok"]:
        continue
    t = json.load(open(f"data/ledger_pages/truth/{name}.json"))
    if t["errors"]:
        continue
    flags = check_ledger(LedgerPage.model_validate(res["page"]))
    if flags:
        print(f"{name} {t['photo_quality']} {t['book_type']}")
        for f in flags:
            print("   ", f[:160])