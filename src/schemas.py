import datetime
from typing import Literal
from pydantic import BaseModel, Field

class LineItem(BaseModel):
    description: str
    quantity: float = 1
    unit_price: float | None = None
    line_total: float


class Receipt(BaseModel):
    vendor: str | None = None
    date_written: str | None = None        # the AI copies this exactly as written
    date: datetime.date | None = None      # our code fills this in, not the AI
    currency: str = "USD"
    items: list[LineItem] = Field(min_length=1)
    total: float

class LedgerRow(BaseModel):
    row_type: Literal["entry", "total", "balance_bf"]
    date_written: str | None = None    # AI copies exactly as written, null if the cell is blank
    date: datetime.date | None = None  # our code fills this, never the AI
    details: str | None = None
    qty: float | None = None           # sales book
    amount: float | None = None        # sales book
    money_in: float | None = None      # cash book
    money_out: float | None = None     # cash book
    owed: float | None = None          # credit ledger
    paid: float | None = None          # credit ledger
    balance: float | None = None       # cash book and credit ledger

class LedgerPage(BaseModel):
    book_type: Literal["cash_book", "sales_book", "credit_ledger"]
    currency: str = "USD"
    rows: list[LedgerRow] = Field(min_length=1)