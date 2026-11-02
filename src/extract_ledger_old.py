import base64, json, os, re, sys
from dotenv import load_dotenv
from groq import Groq
from pydantic import ValidationError
from schemas import LedgerPage
from ledger_dates import fill_dates
from ledger_checks import check_ledger

load_dotenv()
client = Groq(api_key=os.environ["GROQ_API_KEY"])
MODEL = os.environ["GROQ_MODEL"]

print("extract_ledger.py loaded successfully")

def image_to_data_url(path):
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:image/jpeg;base64,{b64}"

PROMPT = """You are reading a photo of a handwritten cash book / ledger page from a small shop in Zimbabwe.
Return ONLY a JSON object with this structure:
{
  "book_type": "cash_book",
  "currency": "USD",
  "entries": [
    {
      "date_written": "2/10" or null if the date cell is blank,
      "details": "what was written in the details column",
      "money_in": number or null,
      "money_out": number or null
    }
  ],
  "total_in": number or null,
  "total_out": number or null
}

Rules:
- Only include the normal transaction rows in "entries".
- Do NOT include the "Balance b/f" row or the "TOTAL" row inside the entries list.
- Put the final TOTAL figures only in the top-level "total_in" and "total_out" fields.
- Copy every number EXACTLY as written. Do not calculate or correct anything.
- If a number has been struck out and rewritten, use the final corrected number.
- If the date cell is blank, put null for date_written.
- On each normal row only one of money_in or money_out should have a value.
- No explanation. JSON only.
"""

def extract_ledger(image_path, max_tries=3):
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": PROMPT},
            {"type": "image_url", "image_url": {"url": image_to_data_url(image_path)}}
        ]
    }]

    for attempt in range(1, max_tries + 1):
        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0
        )
        raw = resp.choices[0].message.content or ""
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL)

        try:
            start = raw.find("{")
            end = raw.rfind("}")
            if start == -1 or end == -1:
                raise ValueError("No JSON object found")
            data = json.loads(raw[start:end+1])
            page = LedgerPage.model_validate(data)
            page = fill_dates(page)
            return page, attempt
        except (ValueError, ValidationError) as e:
            print(f"  attempt {attempt} failed: {str(e)[:150]}")
            messages.append({"role": "assistant", "content": raw})
            messages.append({
                "role": "user",
                "content": f"That answer was invalid:\n{e}\nFix it and return ONLY the corrected JSON."
            })

    raise RuntimeError(f"No valid ledger page after {max_tries} tries: {image_path}")