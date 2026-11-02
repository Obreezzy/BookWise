import base64, json, os, re, sys
from dotenv import load_dotenv
from groq import Groq
from pydantic import ValidationError
from schemas import Receipt
from checks import check_receipt
from dates import parse_date

load_dotenv()
client = Groq(api_key=os.environ["GROQ_API_KEY"])
MODEL = os.environ["GROQ_MODEL"]
MAX_TRIES = 3

_schema = Receipt.model_json_schema()
_schema["properties"].pop("date", None)   # the AI never fills this field

PROMPT = f"""You are reading a photo of a handwritten receipt from a small shop in Zimbabwe.
Return ONLY a JSON object that follows this schema:
{json.dumps(_schema)}

Rules:
- date_written: copy the date EXACTLY as written on the page (for example 10/09/2026 or 5 Oct). Do not convert, reorder or reformat it. Use null if there is no date.
- Copy numbers exactly as written on the page, even if they look wrong. Never fix, calculate or invent numbers.
- If something cannot be read, use null (only for fields that allow it).
- Currency is USD unless the page clearly says otherwise.
- No explanation and no markdown. JSON only."""

def image_to_data_url(path):
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:image/jpeg;base64,{b64}"


def find_json(text):
    """Models sometimes add chatter or thinking text. Keep only the JSON part."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object found in the reply")
    return json.loads(text[start:end + 1])


def extract_receipt(image_path):
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": PROMPT},
            {"type": "image_url", "image_url": {"url": image_to_data_url(image_path)}},
        ],
    }]
    for attempt in range(1, MAX_TRIES + 1):
        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0,
        )
        raw = resp.choices[0].message.content or ""
        try:
            receipt = Receipt.model_validate(find_json(raw))
            receipt.date = parse_date(receipt.date_written)   # our code decides the date
            return receipt, attempt
        except (ValueError, ValidationError) as e:
            print(f"  attempt {attempt} failed: {str(e)[:200]}")
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content":
                f"That answer was invalid:\n{e}\nFix it and return ONLY the corrected JSON."})
    raise RuntimeError(f"No valid receipt after {MAX_TRIES} tries: {image_path}")


if __name__ == "__main__":
    receipt, tries = extract_receipt(sys.argv[1])
    print(f"Succeeded on attempt {tries}")
    print(receipt.model_dump_json(indent=2))
    flags = check_receipt(receipt)
    if flags:
        print("\n⚠ NEEDS REVIEW:")
        for f in flags:
            print("  -", f)
    else:
        print("\n✓ All checks passed")