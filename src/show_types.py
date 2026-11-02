import json

results = json.load(open("results_ledgers.json"))
for name, res in sorted(results.items()):
    t = json.load(open(f"data/ledger_pages/truth/{name}.json"))
    ai = res["page"]["book_type"] if res["ok"] else "FAILED"
    mark = "" if ai == t["book_type"] else "   <-- WRONG"
    print(f"{name} {t['photo_quality']:6} truth={t['book_type']:22} ai={ai}{mark}")