import json
from evaluate import CACHE, DATA

results = json.load(open(CACHE))
rows = []
for name, res in sorted(results.items()):
    if not res["ok"]:
        continue
    t = json.load(open(f"{DATA}/truth/{name.replace('.jpg', '.json')}"))
    r = res["receipt"]
    lines_sum = round(sum(i["line_total"] for i in r["items"]), 2)
    if abs(r["total"] - t["total_written"]) >= 0.005:          # AI total differs from the page
        rows.append((name, t["photo_quality"], t["has_error"], r["total"],
                     t["total_written"], lines_sum, abs(r["total"] - lines_sum) < 0.005))

print("Receipts where the AI total differs from the total written on the page:")
for name, q, err, ai, written, s, eq in rows:
    print(f"  {name} {q:6} injected_error={err!s:5} AI total={ai} written={written} "
          f"AI lines add up to {s} same_as_lines={eq}")
print("\nAI total equals the sum of its own lines in", sum(1 for x in rows if x[6]), "of", len(rows))