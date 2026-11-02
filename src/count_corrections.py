import glob, json, os

total = 0
for path in sorted(glob.glob("data/ledger_pages/truth/*.json")):
    t = json.load(open(path))
    if t["corrections"]:
        total += 1
        print(os.path.basename(path).replace(".json", ""), t["book_type"], t["photo_quality"], t["corrections"])
print("pages with corrections:", total)