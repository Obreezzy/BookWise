import json
from schemas import LedgerPage
from ledger_checks import check_ledger

results = json.load(open("results_ledgers.json"))
counts = {}
for name, res in sorted(results.items()):
    if not res["ok"]:
        continue
    t = json.load(open(f"data/ledger_pages/truth/{name}.json"))
    codes = {f.split(":")[0] for f in check_ledger(LedgerPage.model_validate(res["page"]))}
    shifted = bool(codes & {"EMPTY_ENTRY", "TOTAL_LABEL_ON_ENTRY"})
    counts.setdefault(t["photo_quality"], [0, 0])
    counts[t["photo_quality"]][0] += 1
    counts[t["photo_quality"]][1] += shifted
for q, (n, s) in counts.items():
    print(f"{q:6} pages={n} with_shift_signature={s}")