import base64, json, os, re, sys
from dotenv import load_dotenv
from groq import Groq
from pydantic import ValidationError
from schemas import LedgerPage
from ledger_dates import fill_dates
from ledger_checks import check_ledger
from ledger_fix import suggest_fixes

load_dotenv()
client = Groq(api_key=os.environ["GROQ_API_KEY"])
MODEL = os.environ["GROQ_MODEL"]
MAX_TRIES = 3

_schema = LedgerPage.model_json_schema()
_schema["$defs"]["LedgerRow"]["properties"].pop("date", None)   # the AI never fills "date"

PROMPT = f"""You are reading a photo of a handwritten ledger page from a small shop in Zimbabwe.
Return ONLY a JSON object that follows this schema:
{json.dumps(_schema)}

First decide book_type from the column headings on the page:
- cash_book: Date | Details | Money In | Money Out (maybe Balance). Use money_in, money_out, balance.
- sales_book: Date | Details | Qty | Amount. Use qty and amount.
- credit_ledger: Date | Items | Owed | Paid | Balance. Use owed, paid, balance.
Leave columns that the page does not have as null.

Rules:
- "rows" must contain EVERY row on the page, in the same order as on the page, top to bottom.
- row_type "entry" = a normal transaction row.
- row_type "total" = any row that is a written TOTAL (including a total after each day). Put its figures in the same columns as the entries. Do not skip it and do not merge it into the entries.
- row_type "balance_bf" = a "Balance b/f" (brought forward) row. Put its figure in balance.
- date_written: copy the date EXACTLY as written (for example 23 Sep or 2/10). If the date cell on that row is BLANK, use null. Never repeat a date from the row above, and never add one that is not written.
- details: copy as written. If a details cell has a ditto mark, copy the details from the row above.
- Copy numbers exactly as written, even if they look wrong. Never calculate, fix or invent numbers.
- If a number was struck out and rewritten, use the final rewritten number.
- Currency is USD unless the page clearly says otherwise.
- No explanation and no markdown. JSON only.
- Money amounts and balances always have two decimal places (for example 28.27, 5.50, 0.00). Copy both decimal digits exactly; never drop the last digit.
- balance: copy the balance number that is PRINTED in the Balance column of that row. NEVER work it out from the previous balance. If the balance cell is unreadable, use null.
- Keep the JSON short: leave out any field whose value is null (do not write "qty": null). Only write fields that have a value. Do not write the "currency" field unless it is not USD."""

def image_to_data_url(path):
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:image/jpeg;base64,{b64}"

def find_json(text):
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object found in the reply")
    return json.loads(text[start:end + 1])

def extract_ledger(image_path):
    messages = [{"role": "user", "content": [
        {"type": "text", "text": PROMPT},
        {"type": "image_url", "image_url": {"url": image_to_data_url(image_path)}}]}]
    for attempt in range(1, MAX_TRIES + 1):
        resp = client.chat.completions.create(model=MODEL, messages=messages,
            response_format={"type": "json_object"}, temperature=0, max_tokens=900)
        raw = resp.choices[0].message.content or ""
        if resp.choices[0].finish_reason == "length":
            print("  WARNING: reply was cut off by max_tokens, rows may be missing")
        try:
            page = LedgerPage.model_validate(find_json(raw))
            return fill_dates(page), attempt      # our code decides every date
        except (ValueError, ValidationError) as e:
            print(f"  attempt {attempt} failed: {str(e)[:200]}")
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content":
                f"That answer was invalid:\n{e}\nFix it and return ONLY the corrected JSON."})
    raise RuntimeError(f"No valid ledger page after {MAX_TRIES} tries: {image_path}")

if __name__ == "__main__":
    page, tries = extract_ledger(sys.argv[1])
    print(f"Succeeded on attempt {tries}")
    print(f"book_type: {page.book_type}")
    for n, r in enumerate(page.rows, start=1):
        print(f"{n:>3} {r.row_type:10} {str(r.date):10} {r.details or '':22} "
              f"qty={r.qty} amt={r.amount} in={r.money_in} out={r.money_out} "
              f"owed={r.owed} paid={r.paid} bal={r.balance}")
    flags = check_ledger(page)
    if flags:
        print("\nNEEDS REVIEW:")
        for f in flags:
            print("  -", f)
        tips = suggest_fixes(page)
        if tips:
            print("\nPOSSIBLE FIXES (ask the shopkeeper):")
            for t in tips:
                print("  -", t)
    else:
        print("\nAll checks passed")