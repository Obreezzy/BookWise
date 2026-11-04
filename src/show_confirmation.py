import datetime, json, sys
from evaluate import CACHE, DATA
from schemas import Receipt
from confirm import confirmation_message

results = json.load(open(CACHE))
for name in sys.argv[1:]:
    truth = json.load(open(f"{DATA}/truth/{name}.json"))
    sent_on = datetime.date.fromisoformat(truth["date"])    # SIMULATED: pretend it was sent on the true date
    print(f"--- {name} (simulated send date: {sent_on}) ---")
    print(confirmation_message(Receipt.model_validate(results[name + ".jpg"]["receipt"]), sent_on))
    print()