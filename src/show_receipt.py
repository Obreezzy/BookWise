import json, sys
from evaluate import CACHE, DATA

name = sys.argv[1]
res = json.load(open(CACHE))[name + ".jpg"]
t = json.load(open(f"{DATA}/truth/{name}.json"))
r = res["receipt"]

print("AI read:", {k: v for k, v in r.items() if k != "items"})
for i in r["items"]:
    print("  ", i)
print("\nTruth:", {k: v for k, v in t.items() if k != "items"})
for i in t["items"]:
    print("  ", i)