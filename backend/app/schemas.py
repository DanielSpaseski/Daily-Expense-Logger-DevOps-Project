from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class ExpenseCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    category: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    spent_on: Optional[date] = None


class ExpenseOut(BaseModel):
    id: int
    amount: Decimal
    category: str
    description: Optional[str]
    spent_on: date
    created_at: datetime

    class Config:
        from_attributes = True


class CategorySummary(BaseModel):
    category: str
    total: Decimal
    count: int


class Summary(BaseModel):
    total: Decimal
    count: int
    by_category: list[CategorySummary]
