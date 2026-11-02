import glob, json, os

for path in sorted(glob.glob("data/ledger_pages/truth/*.json")):
    t = json.load(open(path))
    name = os.path.basename(path).replace(".json", "")
    totals = t["totals"] if isinstance(t["totals"], dict) else {}
    errs = [e.get("type", e) if isinstance(e, dict) else e for e in t["errors"]]
    print(f"{name} {t['book_type']:22} {t['photo_quality']:6} "
          f"balance_col={'Balance' in t['columns']!s:5} "
          f"b/f={totals.get('balance_bf')} errors={errs}")