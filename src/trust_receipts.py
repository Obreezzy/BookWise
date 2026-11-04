import json
from evaluate import CACHE, DATA, clean, check_receipt
from schemas import Receipt

results = json.load(open(CACHE))
tally = {}
quiet = []
for name, res in sorted(results.items()):
    if not res["ok"]:
        continue
    t = json.load(open(f"{DATA}/truth/{name.replace('.jpg', '.json')}"))
    if t["has_error"]:
        continue                      # skip receipts with injected errors
    r = res["receipt"]
    ok = {
        "vendor": clean(r["vendor"]) == clean(t["vendor"]),
        "date": r["date"] == t["date"],
        "total": abs(r["total"] - t["total_written"]) < 0.005,
        "lines": sorted(round(i["line_total"], 2) for i in r["items"])
                 == sorted(round(i["line_total_written"], 2) for i in t["items"]),
    }
    flagged = bool(check_receipt(Receipt.model_validate(r)))
    wrong = [k for k, v in ok.items() if not v]
    key = (t["photo_quality"], "flagged" if flagged else "quiet", "right" if not wrong else "wrong")
    tally[key] = tally.get(key, 0) + 1
    if not flagged and wrong:
        quiet.append((name, t["photo_quality"], wrong))

for key in sorted(tally):
    print(key, tally[key])
print("\nQuiet but wrong (silent misses):")
for name, q, wrong in quiet:
    print(f"  {name} {q:6} wrong: {', '.join(wrong)}")