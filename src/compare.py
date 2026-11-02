import json
from evaluate import score

old = json.load(open("baseline_v1.json"))
new = json.load(open("results_receipts.json"))
common = {k for k in old if k in new}
print(f"Comparing {len(common)} receipts that both runs finished\n")

print("=== BEFORE (baseline_v1) ===")
score({k: old[k] for k in common})
print("\n=== AFTER (date fix) ===")
score({k: new[k] for k in common})