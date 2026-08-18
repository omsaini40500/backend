from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import uuid4
from app.api.v1.deps import get_db, get_current_user
from app.models import Department
from app.schemas import DepartmentOut
from pydantic import BaseModel

router = APIRouter(prefix="/departments", tags=["departments"])

class DepartmentCreate(BaseModel):
    name: str

class DepartmentUpdate(BaseModel):
    name: str

@router.get("/", response_model=List[DepartmentOut])
def read_settings_departments(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(Department).all()

@router.post("/", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
def create_department(data: DepartmentCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    department = Department(
        id=str(uuid4())[:8],
        name=data.name,
    )
    db.add(department)
    db.commit()
    db.refresh(department)
    return department

@router.patch("/{department_id}", response_model=DepartmentOut)
def update_department(department_id: str, data: DepartmentUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    department.name = data.name
    db.commit()
    db.refresh(department)
    return department

@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(department_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    db.delete(department)
    db.commit()
    return
