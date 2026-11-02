import glob, json, os, re, sys, time
from collections import defaultdict
from extract import extract_receipt
from checks import check_receipt
from schemas import Receipt

DATA = "data/handwritten_receipts"
CACHE = "results_receipts.json"


def run(limit):
    results = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    files = sorted(glob.glob(f"{DATA}/images/*.jpg"))[:limit]
    for path in files:
        name = os.path.basename(path)
        if name in results:
            continue  # already done on an earlier run
        try:
            r, tries = extract_receipt(path)
            results[name] = {"ok": True, "tries": tries, "receipt": json.loads(r.model_dump_json())}
        except RuntimeError as e:  # model failed 3 times: a real result
            results[name] = {"ok": False, "error": str(e)[:200]}
        except Exception as e:     # API/network problem: not the model's fault
            print(f"API problem on {name}: {str(e)[:500]}\nStopping. Run again later; progress is saved.")
            break
        json.dump(results, open(CACHE, "w"), indent=2)
        print(name, "ok" if results[name]["ok"] else "FAILED")
        time.sleep(2)  # be gentle with rate limits
    return results


def clean(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def score(results):
    stats = defaultdict(lambda: defaultdict(int))
    misses = []
    for name, res in sorted(results.items()):
        t = json.load(open(f"{DATA}/truth/{name.replace('.jpg', '.json')}"))
        s = stats[t["photo_quality"]]
        s["n"] += 1
        if not res["ok"]:
            s["failed"] += 1
            continue
        r = res["receipt"]

        checks = {
            "vendor": clean(r["vendor"]) == clean(t["vendor"]),
            "date": r["date"] == t["date"],
            "total": abs(r["total"] - t["total_written"]) < 0.005,
            "lines": sorted(round(i["line_total"], 2) for i in r["items"])
                     == sorted(round(i["line_total_written"], 2) for i in t["items"]),
        }
        for field, ok in checks.items():
            s[field] += ok
            if not ok:
                misses.append((name, field))

        flagged = bool(check_receipt(Receipt.model_validate(r)))
        if t["has_error"]:
            s["real_errors"] += 1
            s["caught"] += flagged
        elif flagged:
            s["false_alarms"] += 1

    print(f"\n{'quality':8} {'n':>3} {'fail':>4} {'vendor':>7} {'date':>6} {'total':>6} {'lines':>6} {'caught':>8} {'false':>6}")
    for q in ("clean", "mild", "bad"):
        s = stats.get(q)
        if not s:
            continue
        done = s["n"] - s["failed"]
        pct = lambda k: f"{100 * s[k] / done:.0f}%" if done else "-"
        caught = f"{s['caught']}/{s['real_errors']}"
        print(f"{q:8} {s['n']:>3} {s['failed']:>4} {pct('vendor'):>7} {pct('date'):>6} "
              f"{pct('total'):>6} {pct('lines'):>6} {caught:>8} {s['false_alarms']:>6}")
    print("\nFirst misses (open these to see why):")
    for name, field in misses[:15]:
        print(f"  {name}: {field}")


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    score(run(limit))