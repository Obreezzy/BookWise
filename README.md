# BookWise

An AI bookkeeping assistant for small shops in Zimbabwe (tuckshops, salons, informal traders). A shopkeeper photographs a handwritten receipt or a handwritten cash-book page. The system reads it, records it, and flags anything that does not add up.

**Status: work in progress.** The extraction and checking pipeline works on a generated test set, and a Telegram bot can read a receipt photo and ask the shopkeeper to confirm it. The bot has only been tried by hand on test receipts, never on real handwritten pages from a shop. Ledger pages are not connected to the bot yet, and there is no question answering.

## Core design rule

**The AI reads. Plain code checks and converts.**

Arithmetic, date logic and validation are done in code, never by the model. The model only copies what is written on the page, and the code decides whether it makes sense.

## What is built

- Vision-LLM extraction (Qwen3.8-27B on Groq's free tier) into Pydantic schemas, with a retry loop that feeds validation errors back to the model.
- **Receipts:** deterministic checks for totals, quantity x price, and date plausibility. Dates are copied as written by the model and converted by code (day always comes first).
- **Ledger pages** (cash book, sales book, credit ledger): rows are read in page order, blank dates inherit from the row above, and code checks per-day totals, running balances, closing balances, empty entries, and pages cut off before their total row. A helper suggests likely fixes to ask the shopkeeper about.
- SQLite storage with `business_id` on every table and money in cents. Re-sending the same file replaces the earlier version, and a receipt that matches an already confirmed one (same vendor, date and total) triggers a warning.
- Evaluation scripts that score results against truth files, split by photo quality, with caching and rate-limit-safe stopping.
- **Confirmation message:** turns a saved receipt into the question the shopkeeper would see, with the date written in words, what the model read, and plain-language notes.
- **Hard and soft flags.** Hard flags (totals that do not add up, a date after the day the photo was sent) block confirmation and ask for a clearer photo. Soft flags (a date more than 14 days before the send date, or a possible duplicate) are shown as a note, and the shopkeeper can still answer YES knowingly. The send-date thresholds (1 day after, 14 days before) are guesses until real send dates exist. Date errors within a day or two of the truth cannot be caught by any date rule.
- **Telegram bot** (`src/telegram_main.py`): receives a photo (normal or sent as a file), reads it, replies with the confirmation message, and turns YES into a `user_confirmed` record. The send date is taken from Telegram's message time and converted to Harare time. Each Telegram user gets their own `business_id`. Network timeouts to Telegram are retried, and a failed read gets a plain reply. The monthly report counts confirmed, passed-checks-only and flagged receipts separately.

## Results so far (generated test set only)

The test set is 50 receipts and 40 ledger pages drawn by script to look handwritten, at three photo-quality levels (clean, mild, bad). None are real shop documents, so these numbers describe how the pipeline behaves on that set, not how it would do in a shop.

**Receipts**, all 50, one run each (dates converted by code):

| Photo quality | Vendor | Date | Total | Line items | Injected errors caught |
|---|---|---|---|---|---|
| clean (12) | 92% | 100% | 100% | 100% | 0 of 0 |
| mild (20) | 100% | 95% | 100% | 95% | 3 of 3 |
| bad (18) | 94% | 44% | 61% | 44% | 3 of 3 |

An earlier version, where the model converted dates itself, scored 85% (mild) and 56% (bad) on dates. Moving the conversion into code helped on mild photos. On bad photos date accuracy fell from 56% to 44%, which is about two receipts out of 18, so run-to-run variation could explain it. The remaining date errors are misread digits, which code cannot fix.

**Does a flag mean something is wrong?** Looking only at the 44 receipts with no injected error:

- 10 were flagged, and all 10 had at least one wrong field (no false alarms).
- 34 were quiet. 29 were fully right and 5 had a silent miss: 3 wrong dates, 1 wrong vendor, and 1 receipt with a wrong date, total and line items that passed every arithmetic check.

**Ledger pages**, all 40, one run each:

| Photo quality | Pages | Amounts right | Balances right | Injected errors caught |
|---|---|---|---|---|
| clean | 8 | 98% | 100% | 3 of 3 |
| mild | 16 | 96% | 93% | 2 of 2 |
| bad | 16 | 65% | 68% | 4 of 4 |

Amounts and balances are scored only on pages where the number of rows matched the truth file (3 bad pages did not).

On bad photos the model sometimes shifts values one row down or misreads digits. The checks flagged every page with an injected error, but on bad photos some were flagged for the wrong reason.

**Does a flag mean something is wrong?** Looking only at the 31 pages with no injected error:

- 15 were flagged, and all 15 had wrong numbers (no false alarms).
- 16 were quiet. 13 were fully right, and 3 had a silent problem the checks cannot see: a misread quantity on a sales book, a garbled description, and a misread date (11 Sep read as 01 Sep) with a garbled description.

A check that compared the unit price of repeated items was tried and removed. It caught one real misread quantity but raised three false alarms, because prices change between days.

On the two pages with struck-out corrections, the model read the crossed-out number on at least one run, despite a prompt rule to use the rewritten one. The checks flagged both pages. The same photo can also read differently between runs, even at temperature 0, so one run per page is weak evidence.

## Known limits

- All test data is **generated**. Real-world accuracy is untested, including the bot itself.
- Bad photos are unreliable. Digit misreads and row shifts can pass the arithmetic checks.
- Silent errors (a valid but wrong date, or a self-consistent wrong line) cannot be caught by code. They need human confirmation.
- On bad photos the model sometimes appears to compute a total from its own line items instead of copying the written one. In 3 of the 7 receipts with a wrong total, the model's total equals the sum of its own (wrong) lines. That hides misread lines from the total check. One such receipt passed every check.
- "Passed checks" does not mean "verified".
- The duplicate warning is only a warning. A shopkeeper who answers YES out of habit records the receipt twice, and the report cannot tell the two apart.
- The bot cannot take corrections yet: the shopkeeper can only confirm or send a clearer photo. The waiting-for-YES state is kept in memory and is lost when the bot restarts.
- Telegram recompresses normal photos. Whether that lowers reading accuracy compared with sending as a file has not been measured.
- The bot runs only while the script runs on one computer (it polls Telegram). Photos it downloads are kept in `incoming/` with no retention policy yet.
- Groq's free tier limits tokens per day and output tokens per minute, so only a few dozen photos can be processed per day.

## Data

The `data/` folder is **not** in this repository. It holds the generated handwritten receipts and ledger pages, made with Python and PIL, plus truth files with the correct values. Without it, the evaluation scripts cannot be re-run, but the saved results are included:

- `results_receipts.json`, `results_ledgers.json`: the model's reads of the generated pages.
- `baseline_*.json`: earlier runs kept for before/after comparison.

The database (`bookwise.db`), the `.env` file and the `incoming/` photo folder are private and are never committed.

## Setup

1. Install Python 3.13 and create a virtual environment.
2. Install dependencies: `pip install groq python-dotenv pydantic python-telegram-bot tzdata`
3. Create a `.env` file in the project root (never commit it):

```
GROQ_API_KEY=your_key_here
GROQ_MODEL=qwen/qwen3.8-27b
TELEGRAM_TOKEN=your_bot_token_here
```

4. Run on one image: `python src/extract.py path/to/receipt.jpg` or `python src/extract_ledger.py path/to/page.jpg`
5. Check the Telegram token: `python src/telegram_check.py`
6. Run the bot: `python src/telegram_main.py`

Each photo costs about 3,000 tokens of the free daily budget.

## Layout

- `src/schemas.py`: Pydantic models for receipts and ledger rows
- `src/dates.py`, `src/ledger_dates.py`: date parsing and date filling, done in code
- `src/checks.py`, `src/ledger_checks.py`: deterministic validators
- `src/ledger_fix.py`: suggests likely fixes to ask the shopkeeper about
- `src/confirm.py`, `src/sent_date.py`, `src/send_day.py`: the confirmation message, the send-date rule, and the Harare send date
- `src/bot.py`: the bot's logic for photos and replies, without any messaging platform
- `src/telegram_main.py`, `src/telegram_check.py`: the Telegram runner and a token check
- `src/trust_report.py`, `src/trust_receipts.py`, `src/total_source.py`, `src/date_gaps.py`: analysis scripts behind the numbers above
- `src/extract.py`, `src/extract_ledger.py`: model calls
- `src/evaluate.py`, `src/evaluate_ledger.py`: scoring against truth files
- `src/db.py`, `src/load_results.py`, `src/queries.py`, `src/show_confirmed.py`: SQLite storage, reports and inspection
- `src/test_*.py`: tests on made-up rows, no API calls

## Planned

- Corrections ("tell me what to change") and keeping the waiting-for-YES state in the database.
- Ledger pages through the bot, and a ledger entries table.
- Question answering through safe SQL functions, not by letting the model invent numbers.
- Better reading of bad photos (image preprocessing, reading twice and comparing), and measuring normal photos against sent-as-file.
- A photo retention policy.
- A WhatsApp adapter.
- Testing on real handwritten pages.