import logging
import time
from contextlib import asynccontextmanager
from datetime import date, timedelta
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Expense
from .schemas import CategorySummary, ExpenseCreate, ExpenseOut, Summary

logger = logging.getLogger("uvicorn.error")


def init_db(retries: int = 30, delay: float = 2.0):
    """Wait for Postgres to be reachable, then create tables."""
    for attempt in range(1, retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database initialized")
            return
        except OperationalError as e:
            logger.warning("DB not ready (attempt %d/%d): %s", attempt, retries, e)
            time.sleep(delay)
    raise RuntimeError("Could not connect to database after retries")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Daily Expense Logger", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/expenses", response_model=list[ExpenseOut])
def list_expenses(
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
):
    return (
        db.query(Expense)
        .order_by(Expense.spent_on.desc(), Expense.id.desc())
        .limit(limit)
        .all()
    )


@app.post("/api/expenses", response_model=ExpenseOut, status_code=201)
def create_expense(payload: ExpenseCreate, db: Session = Depends(get_db)):
    expense = Expense(
        amount=payload.amount,
        category=payload.category.strip(),
        description=(payload.description or "").strip() or None,
        spent_on=payload.spent_on or date.today(),
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@app.delete("/api/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(expense)
    db.commit()


@app.get("/api/summary", response_model=Summary)
def get_summary(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    cutoff = date.today() - timedelta(days=days)

    rows = (
        db.query(
            Expense.category,
            func.sum(Expense.amount).label("total"),
            func.count(Expense.id).label("count"),
        )
        .filter(Expense.spent_on >= cutoff)
        .group_by(Expense.category)
        .order_by(func.sum(Expense.amount).desc())
        .all()
    )

    by_category = [
        CategorySummary(category=r.category, total=r.total, count=r.count) for r in rows
    ]
    return Summary(
        total=sum((c.total for c in by_category), Decimal("0")),
        count=sum(c.count for c in by_category),
        by_category=by_category,
    )
