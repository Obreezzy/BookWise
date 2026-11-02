from pydantic import ValidationError
from schemas import Receipt

good = {
    "vendor": "Stitch Perfect",
    "date": "2026-10-01",
    "currency": "USD",
    "items": [
        {"description": "Zip replace", "quantity": 1, "unit_price": 1.51, "line_total": 1.51},
        {"description": "School uniform", "quantity": 1, "unit_price": 13.75, "line_total": 13.75},
    ],
    "total": 15.26,
}

r = Receipt.model_validate(good)
print("GOOD:", r.vendor, r.date, r.total)
print("date is now a real date object:", type(r.date))

bad = {"vendor": "X", "date": "not a date", "items": [], "total": "fifteen"}
try:
    Receipt.model_validate(bad)
except ValidationError as e:
    print("\nBAD data was rejected:")
    print(e)