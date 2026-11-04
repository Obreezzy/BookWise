import datetime, json
from evaluate import CACHE, DATA
from schemas import Receipt
from checks import check_receipt

results = json.load(open(CACHE))
rows = []
for name, res in sorted(results.items()):
    if not res["ok"]:
        continue
    t = json.load(open(f"{DATA}/truth/{name.replace('.jpg', '.json')}"))
    r = res["receipt"]
    if r["date"] == t["date"]:
        continue
    gap = None
    if r["date"]:
        gap = (datetime.date.fromisoformat(r["date"]) - datetime.date.fromisoformat(t["date"])).days
    flagged = bool(check_receipt(Receipt.model_validate(r)))
    rows.append((name, t["photo_quality"], r["date"], t["date"], gap, flagged))

print("Receipts where the AI date is not the true date:")
for name, q, ai, truth, gap, flagged in rows:
    print(f"  {name} {q:6} AI={ai} truth={truth} gap={gap} days  flagged_by_checks={flagged}")
print(f"\n{len(rows)} receipts with a wrong date;",
      sum(1 for x in rows if not x[5]), "were not flagged by the existing checks")