from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from pydantic import BaseModel
from app.api.v1.deps import get_db, get_current_user
from app.models import Approval, User

router = APIRouter(prefix="/approvals", tags=["approvals"])

class ApprovalCreate(BaseModel):
    title: str
    description: Optional[str] = None
    type: Optional[str] = None
    priority: str = "medium"

class ApprovalUpdate(BaseModel):
    status: Optional[str] = None
    comment: Optional[str] = None

def _serialize(approval: Approval) -> dict:
    return {
        "id": approval.id,
        "title": approval.title,
        "description": approval.description or "",
        "type": approval.type or "",
        "priority": approval.priority,
        "status": approval.status,
        "requesterId": approval.requester_id,
        "requesterName": approval.requester_name,
        "comment": approval.comment or "",
        "createdAt": approval.created_at.isoformat() if approval.created_at else None,
        "updatedAt": approval.updated_at.isoformat() if approval.updated_at else None,
    }

@router.get("")
def read_approvals(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(status_code=403, detail="Not authorized to view approvals")

    query = db.query(Approval)
    if status:
        query = query.filter(Approval.status == status)
    approvals = query.order_by(Approval.created_at.desc()).all()
    return [_serialize(a) for a in approvals]

@router.get("/my")
def read_my_approvals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    approvals = db.query(Approval).filter(Approval.requester_id == current_user.id).order_by(Approval.created_at.desc()).all()
    return [_serialize(a) for a in approvals]

@router.get("/{approval_id}")
def read_approval(approval_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    approval = db.query(Approval).filter(Approval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if current_user.role not in ("super_admin", "admin") and approval.requester_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this approval")
    return _serialize(approval)

@router.post("", status_code=201)
def create_approval(
    data: ApprovalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import uuid
    approval = Approval(
        id=str(uuid.uuid4())[:8],
        title=data.title,
        description=data.description,
        type=data.type,
        priority=data.priority,
        requester_id=current_user.id,
        requester_name=current_user.name,
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)
    return _serialize(approval)

@router.patch("/{approval_id}")
def update_approval(
    approval_id: str,
    data: ApprovalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    approval = db.query(Approval).filter(Approval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(status_code=403, detail="Not authorized to update approvals")
    if data.status:
        approval.status = data.status
    if data.comment:
        approval.comment = data.comment
    db.commit()
    db.refresh(approval)
    return _serialize(approval)

@router.delete("/{approval_id}", status_code=204)
def delete_approval(
    approval_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    approval = db.query(Approval).filter(Approval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.requester_id != current_user.id and current_user.role not in ("super_admin", "admin"):
        raise HTTPException(status_code=403, detail="Not authorized to delete this approval")
    db.delete(approval)
    db.commit()
