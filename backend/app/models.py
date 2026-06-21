from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime
from .database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    description = Column(String(255), nullable=True)
    spent_on = Column(Date, nullable=False, default=date.today, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
