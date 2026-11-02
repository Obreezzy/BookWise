# BookWise

An AI bookkeeping assistant for small shops in Zimbabwe (tuckshops, salons, informal traders). A shopkeeper photographs a handwritten receipt or a handwritten cash-book page. The system reads it, records it, and flags anything that does not add up.

**Status: work in progress.**

## Core design rule

**The AI reads. Plain code checks and converts.**

Arithmetic, date logic and validation are done in code, never by the model. The model only copies what is written on the page, and the code decides whether it makes sense.

## What is built

- Vision-LLM extraction (Qwen3.8-27B on Groq's free tier) into Pydantic schemas, with a retry loop that feeds validation errors back to the model.
- **Receipts:** deterministic checks for totals, quantity x price, and date plausibility. Dates are copied as written by the model and converted by code (day always comes first).
- **Ledger pages** (cash book, sales book, credit ledger): rows are read in page order, blank dates inherit from the row above, and code checks per-day totals, running balances, closing balances, empty entries, and pages cut off before their total row. A helper suggests likely fixes to ask the shopkeeper about.
- SQLite storage with `business_id` on every table, money in cents, and duplicate protection.
- Evaluation scripts that score results against truth files, split by photo quality, with caching and rate-limit-safe stopping.

## Results so far 

**Receipts**, first pipeline, all 50 handwritten receipts:

| Photo quality | Vendor | Date | Total | Line items | Injected errors caught |
|---|---|---|---|---|---|
| clean (12) | 92% | 100% | 100% | 100% | 0 of 0 |
| mild (20) | 100% | 85% | 100% | 95% | 3 of 3 |
| bad (18) | 94% | 56% | 61% | 44% | 3 of 3 |

Moving date conversion from the model into code raised mild-photo date accuracy from 80% to 100% on the same 33 receipts. Bad-photo dates stayed around 50%, because the remaining errors are misread digits.

**Ledger pages**, 14 of 40 pages run so far:

| Photo quality | Pages | Amounts right | Balances right |
|---|---|---|---|
| clean | 1 | 100% | 100% |
| mild | 5 | 98% | 86% |
| bad | 8 | 55% | 62% |

On bad photos the model sometimes shifts values one row down or misreads digits. The checks flagged every bad page with an injected error, but some were flagged for the wrong reason.

## Known limits

- All test data is **synthetic**. Real-world accuracy is untested.
- Bad photos are unreliable. Digit misreads and row shifts can pass the arithmetic checks.
- Silent errors (a valid but wrong date, or a self-consistent wrong line) cannot be caught by code. They need human confirmation.
- "Passed checks" does not mean "verified".
- Groq's free tier limits tokens per day and output tokens per minute, so only a few pages can be processed per run.

## Data

The `data/` folder is **not** in this repository. It holds synthetic handwritten receipts and ledger pages, generated with Python and PIL, plus truth files with the correct values. Without it, the evaluation scripts cannot be re-run, but the saved results are included:

- `results_receipts.json`, `results_ledgers.json`: the model's reads of the synthetic pages.
- `baseline_*.json`: earlier runs kept for before/after comparison.

## Setup

1. Install Python 3.13 and create a virtual environment.
2. Install dependencies: `pip install groq python-dotenv pydantic`
3. Create a `.env` file in the project root (never commit it):

```
GROQ_API_KEY=your_key_here
GROQ_MODEL=qwen/qwen3.8-27b
```

4. Run on one image: `python src/extract.py path/to/receipt.jpg` or `python src/extract_ledger.py path/to/page.jpg`

Each call costs about 3,000 tokens of the free daily budget.

## Layout

- `src/schemas.py`: Pydantic models for receipts and ledger rows
- `src/dates.py`, `src/ledger_dates.py`: date parsing and date filling, done in code
- `src/checks.py`, `src/ledger_checks.py`: deterministic validators
- `src/ledger_fix.py`: suggests likely fixes to ask the shopkeeper about
- `src/extract.py`, `src/extract_ledger.py`: model calls
- `src/evaluate.py`, `src/evaluate_ledger.py`: scoring against truth files
- `src/db.py`, `src/load_results.py`, `src/queries.py`: SQLite storage and reports
- `src/test_*.py`: tests on made-up rows, no API calls

## Planned

- Finish the remaining ledger pages and the last 17 receipts.
- Human confirmation of each recorded item, and "retake the photo" requests when checks fail.
- Better reading of bad photos (image preprocessing, reading twice and comparing).
- Question answering through safe SQL functions, not by letting the model invent numbers.
- Telegram bot first, then a WhatsApp adapter.
- Testing on real handwritten pages.
