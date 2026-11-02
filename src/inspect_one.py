import json, sys

name = sys.argv[1]  # for example: receipt_018
res = json.load(open("results_receipts.json"))[name + ".jpg"]
truth = json.load(open(f"data/handwritten_receipts/truth/{name}.json"))

print("PHOTO QUALITY:", truth["photo_quality"])
print("\n--- TRUTH ---")
print("vendor:", truth["vendor"], "| date:", truth["date"], "| written as:", truth["date_written_format"])
for i in truth["items"]:
    print("  ", i["description"], i["quantity"], "x", i["unit_price"], "=", i["line_total_written"])
print("   total:", truth["total_written"])
print("   struck-out corrections on page:", truth["corrections"])

print("\n--- WHAT THE AI READ ---")
if not res["ok"]:
    sys.exit("FAILED")
r = res["receipt"]
print("vendor:", r["vendor"], "| date:", r["date"], "| date_written:", r.get("date_written"))
for i in r["items"]:
    print("  ", i["description"], i["quantity"], "x", i["unit_price"], "=", i["line_total"])
print("   total:", r["total"])
