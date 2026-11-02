import json
from schemas import LedgerPage

res = json.load(open("results_ledgers.json"))["page_007"]
full = json.dumps(res["page"])

def compact(row):
    return {k: v for k, v in row.items() if v is not None and k != "date"}

short = json.dumps({"book_type": res["page"]["book_type"],
                    "rows": [compact(r) for r in res["page"]["rows"]]},
                   separators=(",", ":"))

print("rows:", len(res["page"]["rows"]))
print("full JSON characters: ", len(full))
print("short JSON characters:", len(short))
print("saving: {:.0f}%".format(100 * (1 - len(short) / len(full))))