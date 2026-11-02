import glob, json, os

for path in sorted(glob.glob("data/ledger_pages/truth/*.json")):
    t = json.load(open(path))
    for e in t["errors"]:
        if e["type"] == "balance_error":
            print(os.path.basename(path).replace(".json", ""), t["photo_quality"], "delta:", e["delta"])