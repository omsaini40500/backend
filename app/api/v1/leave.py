from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from app.api.v1.deps import get_db, get_current_user
from app.models import LeaveRequest, User
from app.schemas import LeaveOut, LeaveCreate, LeaveUpdate

router = APIRouter(prefix="/leave", tags=["leave"])

def _serialize(leave: LeaveRequest) -> dict:
    return {
        "id": leave.id,
        "userId": leave.user_id,
        "userName": leave.user_name,
        "type": leave.type,
        "startDate": leave.start_date,
        "endDate": leave.end_date,
        "reason": leave.reason,
        "status": leave.status,
        "approvedBy": leave.approved_by,
        "approvedAt": leave.approved_at.isoformat() if leave.approved_at else None,
        "createdAt": leave.created_at.isoformat() if leave.created_at else None,
    }

@router.get("/requests", response_model=List[LeaveOut])
def read_leaves(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(LeaveRequest)
    if current_user.role != "super_admin":
        query = query.filter(LeaveRequest.user_id == current_user.id)
    if status:
        query = query.filter(LeaveRequest.status == status)
    return [_serialize(l) for l in query.all()]

@router.post("/requests", response_model=LeaveOut, status_code=status.HTTP_201_CREATED)
def create_leave(data: LeaveCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    leave = LeaveRequest(
        id=str(uuid4())[:8],
        user_id=data.user_id or current_user.id,
        user_name=data.user_name or current_user.name,
        type=data.type,
        start_date=data.start_date,
        end_date=data.end_date,
        reason=data.reason,
        status="pending",
    )
    db.add(leave)
    db.commit()
    db.refresh(leave)
    return _serialize(leave)

@router.patch("/requests/{leave_id}", response_model=LeaveOut)
def update_leave(leave_id: str, data: LeaveUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    leave = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")
    if data.status is not None:
        leave.status = data.status
    if data.approved_by is not None:
        leave.approved_by = data.approved_by
    if data.approved_at is not None:
        leave.approved_at = data.approved_at
    db.commit()
    db.refresh(leave)
    return _serialize(leave)

@router.delete("/requests/{leave_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_leave(leave_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    leave = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")
    if leave.user_id != current_user.id and current_user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    db.delete(leave)
    db.commit()
    return
