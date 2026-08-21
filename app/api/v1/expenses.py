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

def is_finance_user(db: Session, user: User) -> bool:
    if user.role == "super_admin": return True
    if not user.department_id: return False
    from app.models import Department
    dept = db.query(Department).filter(Department.id == user.department_id).first()
    return dept and dept.name.lower() == "finance"



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
    if not is_finance_user(db, current_user):
        raise HTTPException(status_code=403, detail="Only super admin or finance department can access expenses")

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
    if not is_finance_user(db, current_user):
        raise HTTPException(status_code=403, detail="Only super admin or finance department can access expenses")

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
    if not is_finance_user(db, current_user):
        raise HTTPException(status_code=403, detail="Only super admin or finance department can access expenses")

    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    db.delete(expense)
    db.commit()
    return {"message": "Expense deleted successfully"}

@router.get("/summary")
def read_expense_summary(
    month: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not is_finance_user(db, current_user):
        raise HTTPException(status_code=403, detail="Only super admin or finance department can access expenses")

    target_month = month or datetime.now(timezone.utc).strftime("%Y-%m")
    total_spent = db.query(Expense).filter(Expense.date.startswith(target_month)).all()
    
    total_amount = sum(e.amount for e in total_spent)
    by_category = {}
    for e in total_spent:
        by_category[e.category] = by_category.get(e.category, 0) + e.amount

    return {
        "total_spent": total_amount,
        "count": len(total_spent),
        "by_category": by_category,
    }

from app.models import CompanyBudget
import uuid

class BudgetInput(BaseModel):
    amount: float
    month: Optional[str] = None # e.g. "2026-08". If not provided, defaults to current month

@router.get("/budget")
def get_company_budget(month: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    target_month = month or datetime.now(timezone.utc).strftime("%Y-%m")
    budget = db.query(CompanyBudget).filter(CompanyBudget.month == target_month).first()
    return {"budget": budget.amount if budget else 0.0, "month": target_month}

@router.post("/budget")
def set_company_budget(data: BudgetInput, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not is_finance_user(db, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to set budget")
        
    target_month = data.month or datetime.now(timezone.utc).strftime("%Y-%m")
    budget = db.query(CompanyBudget).filter(CompanyBudget.month == target_month).first()
    
    if budget:
        budget.amount = data.amount
        budget.updated_at = datetime.now(timezone.utc)
    else:
        budget = CompanyBudget(
            id=str(uuid.uuid4())[:8],
            month=target_month,
            amount=data.amount,
            created_by=current_user.id
        )
        db.add(budget)
        
    db.commit()
    return {"budget": data.amount, "month": target_month}
