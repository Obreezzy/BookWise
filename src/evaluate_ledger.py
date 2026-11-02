import json, os, sys, time
from collections import defaultdict
from extract_ledger import extract_ledger
from ledger_checks import check_ledger
from schemas import LedgerPage

DATA = "data/ledger_pages"
CACHE = "results_ledgers.json"
AMOUNTS = ["money_in", "money_out", "amount", "qty", "owed", "paid"]
TYPE_NAMES = {"credit_customer_ledger": "credit_ledger"}   # truth files use the long name


def run(names):
    results = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    for name in names:
        if name in results:
            continue
        try:
            page, tries = extract_ledger(f"{DATA}/images/{name}.jpg")
            results[name] = {"ok": True, "tries": tries, "page": json.loads(page.model_dump_json())}
        except RuntimeError as e:
            results[name] = {"ok": False, "error": str(e)[:200]}
        except Exception as e:
            print(f"API problem on {name}: {str(e)[:500]}\nStopping. Run again later; progress is saved.")
            break
        json.dump(results, open(CACHE, "w"), indent=2)
        print(name, "ok" if results[name]["ok"] else "FAILED")
        time.sleep(2)
    return results


def same(a, b):
    return (a is None and b is None) or (a is not None and b is not None and abs(a - b) < 0.005)


def score(results):
    stats = defaultdict(lambda: defaultdict(int))
    for name, res in sorted(results.items()):
        t = json.load(open(f"{DATA}/truth/{name}.json"))
        s = stats[t["photo_quality"]]
        s["n"] += 1
        if not res["ok"]:
            s["failed"] += 1
            continue
        page = LedgerPage.model_validate(res["page"])
        truth_type = TYPE_NAMES.get(t["book_type"], t["book_type"])
        s["type_ok"] += page.book_type == truth_type
        truth_rows = [e for e in t["entries"] if e["type"] == "entry"]
        ai_rows = [r.model_dump() for r in page.rows if r.row_type == "entry"]
        if len(truth_rows) == len(ai_rows):
            s["count_ok"] += 1
            for te, ar in zip(truth_rows, ai_rows):
                s["rows"] += 1
                s["amounts_ok"] += all(same(te.get(f), ar.get(f)) for f in AMOUNTS if f in te)
                if "balance_written" in te:
                    s["bal_rows"] += 1
                    s["bal_ok"] += same(te["balance_written"], ar["balance"])
        flagged = bool(check_ledger(page))
        if t["errors"]:
            s["real_errors"] += 1
            s["caught"] += flagged
        elif flagged:
            s["flagged_clean"] += 1

    print(f"\n{'quality':8} {'n':>3} {'fail':>4} {'type':>6} {'count':>6} {'amounts':>8} "
          f"{'balances':>9} {'caught':>8} {'flag-no-err':>12}")
    for q in ("clean", "mild", "bad"):
        s = stats.get(q)
        if not s:
            continue
        done = s["n"] - s["failed"]
        pct = lambda a, b: f"{100 * s[a] / s[b]:.0f}%" if s[b] else "-"
        caught = f"{s['caught']}/{s['real_errors']}"
        print(f"{q:8} {s['n']:>3} {s['failed']:>4} {s['type_ok']:>3}/{done:<2} "
              f"{s['count_ok']:>3}/{done:<2} {pct('amounts_ok', 'rows'):>8} "
              f"{pct('bal_ok', 'bal_rows'):>9} {caught:>8} {s['flagged_clean']:>12}")


if __name__ == "__main__":
    names = sys.argv[1:]
    score(run(names) if names else json.load(open(CACHE)))