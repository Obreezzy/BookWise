import json, re
from schemas import LedgerPage
from ledger_checks import check_ledger

AMOUNTS = ["money_in", "money_out", "amount", "qty", "owed", "paid"]


def same(a, b):
    return (a is None and b is None) or (a is not None and b is not None and abs(a - b) < 0.005)


def clean(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def compare(page, t):
    """Returns (amounts_ok, dates_ok, details_ok) for the entry rows."""
    truth_rows = [e for e in t["entries"] if e["type"] == "entry"]
    ai_rows = [r for r in page.rows if r.row_type == "entry"]
    if len(truth_rows) != len(ai_rows):
        return False, False, False
    amounts_ok = dates_ok = details_ok = True
    for te, ar in zip(truth_rows, ai_rows):
        d = ar.model_dump()
        if not all(same(te.get(f), d.get(f)) for f in AMOUNTS if f in te):
            amounts_ok = False
        if "balance_written" in te and not same(te["balance_written"], d["balance"]):
            amounts_ok = False
        if str(ar.date) != te["date"]:
            dates_ok = False
        if clean(ar.details) != clean(te["details"]):
            details_ok = False
    return amounts_ok, dates_ok, details_ok


results = json.load(open("results_ledgers.json"))
tally = {}
quiet = []
for name, res in sorted(results.items()):
    if not res["ok"]:
        continue
    t = json.load(open(f"data/ledger_pages/truth/{name}.json"))
    if t["errors"]:
        continue                      # skip pages with injected errors
    page = LedgerPage.model_validate(res["page"])
    flagged = bool(check_ledger(page))
    amounts_ok, dates_ok, details_ok = compare(page, t)
    key = (t["photo_quality"], "flagged" if flagged else "quiet", "right" if amounts_ok else "wrong")
    tally[key] = tally.get(key, 0) + 1
    if not flagged:
        quiet.append((name, t["photo_quality"], amounts_ok, dates_ok, details_ok))

for key in sorted(tally):
    print(key, tally[key])
print("\nQuiet pages (no flag): amounts / dates / descriptions right?")
for name, q, a, d, s in quiet:
    print(f"  {name} {q:6} amounts={a} dates={d} descriptions={s}")