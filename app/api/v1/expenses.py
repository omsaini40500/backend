from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional

from app.api.v1.deps import get_db, get_current_user
from app.models import User, Expense
from app.core.config import get_settings

router = APIRouter(prefix="/expenses", tags=["expenses"])
settings = get_settings()


class ExpenseCreate(BaseModel):
    amount: float
    category: str
    description: Optional[str] = ""
    date: str


class ExpenseOut(BaseModel):
    id: str
    amount: float
    category: str
    description: Optional[str]
    date: str
    created_by: str
    created_at: str

    class Config:
        from_attributes = True


@router.get("/", response_model=List[ExpenseOut])
def read_expenses(
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can view expenses")

    expenses = db.query(Expense).order_by(Expense.date.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": e.id,
            "amount": e.amount,
            "category": e.category,
            "description": e.description,
            "date": e.date,
            "created_by": e.created_by,
            "created_at": e.created_at.isoformat() if e.created_at else "",
        }
        for e in expenses
    ]


@router.post("/", response_model=ExpenseOut)
def create_expense(
    expense_in: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not expense_in.description:
        expense_in.description = ""

    expense = Expense(
        id=f"exp_{int(datetime.now(timezone.utc).timestamp() * 1000)}",
        amount=expense_in.amount,
        category=expense_in.category,
        description=expense_in.description,
        date=expense_in.date,
        created_by=current_user.id,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return {
        "id": expense.id,
        "amount": expense.amount,
        "category": expense.category,
        "description": expense.description,
        "date": expense.date,
        "created_by": expense.created_by,
        "created_at": expense.created_at.isoformat() if expense.created_at else "",
    }


@router.delete("/{expense_id}")
def delete_expense(
    expense_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can delete expenses")

    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    db.delete(expense)
    db.commit()
    return {"message": "Expense deleted successfully"}

@router.get("/summary")
def read_expense_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can view expense summary")

    total_spent = db.query(Expense).all()
    total_amount = sum(e.amount for e in total_spent)
    by_category = {}
    for e in total_spent:
        by_category[e.category] = by_category.get(e.category, 0) + e.amount

    return {
        "total_spent": total_amount,
        "count": len(total_spent),
        "by_category": by_category,
    }
