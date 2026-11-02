import json, sys

name = sys.argv[1]          # for example page_001
truth = json.load(open(f"data/ledger_pages/truth/{name}.json"))

print("book_type:", truth["book_type"], "| photo:", truth["photo_quality"])
print("columns:", truth["columns"])
print("totals:", truth["totals"])
print("errors:", truth["errors"])
print("corrections:", truth["corrections"])
print("\nentries in the truth file:", len(truth["entries"]))
for e in truth["entries"]:
    print("  ", json.dumps(e))