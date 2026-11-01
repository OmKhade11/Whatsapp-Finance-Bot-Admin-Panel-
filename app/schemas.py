from datetime import date, datetime
from decimal import Decimal
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

class IncomeIn(BaseModel):
    amount: Decimal = Field(gt=0)
    entry_date: date

class ExpenseIn(BaseModel):
    category: str = Field(min_length=1, max_length=120)
    amount: Decimal = Field(gt=0)
    entry_date: date
    note: str | None = None

class RecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; amount: Decimal; entry_date: date

class ExpenseOut(RecordOut):
    category: str; note: str | None = None

class AllocationIn(BaseModel):
    monthly_income: Decimal = Field(ge=0)
    needs_percent: Decimal = Decimal('50')
    investment_percent: Decimal = Decimal('30')
    savings_percent: Decimal = Decimal('20')

class PricingIn(BaseModel):
    total_cost: Decimal = Field(gt=0)
    percentage: Decimal = Field(ge=0)

class CapitalIn(BaseModel):
    costs: dict[str, Decimal]
    assumptions: list[str] = []

class WhatsAppIn(BaseModel):
    phone_number: str
    message: str = Field(min_length=1)
    message_id: str | None = None
    session_id: str | None = None

class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; message: str; read: bool; created_at: datetime
