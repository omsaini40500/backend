from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import uuid4
from app.api.v1.deps import get_db, get_current_user
from app.models import Department, Team, Client, Notification, ActivityLog, RecycleBinItem, User, Project, Campaign
from app.schemas import DepartmentOut, TeamOut, ClientOut, ClientCreate, ClientUpdate, NotificationOut, ActivityLogOut

router_depts = APIRouter(prefix="/departments", tags=["departments"])
@router_depts.get("", response_model=List[DepartmentOut])
def read_departments(db: Session = Depends(get_db)):
    return db.query(Department).all()

router_teams = APIRouter(prefix="/teams", tags=["teams"])
@router_teams.get("", response_model=List[TeamOut])
def read_teams(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return db.query(Team).all()

router_clients = APIRouter(prefix="/clients", tags=["clients"])

@router_clients.get("", response_model=List[ClientOut])
def read_clients(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return db.query(Client).all()

@router_clients.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
def create_client(client: ClientCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    new_client = Client(
        id=str(uuid4()),
        name=client.name,
        industry=client.industry or "",
        contact_name=client.contact_name or "",
        contact_email=client.contact_email or "",
        status=client.status or "active",
    )
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    return new_client

@router_clients.patch("/{client_id}", response_model=ClientOut)
def update_client(client_id: str, client: ClientUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    existing = db.query(Client).filter(Client.id == client_id).first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    if client.name is not None:
        existing.name = client.name
    if client.industry is not None:
        existing.industry = client.industry
    if client.contact_name is not None:
        existing.contact_name = client.contact_name
    if client.contact_email is not None:
        existing.contact_email = client.contact_email
    if client.status is not None:
        existing.status = client.status
    db.commit()
    db.refresh(existing)
    return existing

@router_clients.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    existing = db.query(Client).filter(Client.id == client_id).first()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        
    db.query(User).filter(User.client_id == client_id).update({User.client_id: None})
    db.query(Project).filter(Project.client_id == client_id).update({Project.client_id: None})
    db.query(Campaign).filter(Campaign.client == existing.name).update({Campaign.client: None})
    
    db.delete(existing)
    db.commit()
    return

router_notifications = APIRouter(prefix="/notifications", tags=["notifications"])
@router_notifications.get("", response_model=List[NotificationOut])
def read_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role not in ("super_admin", "admin"):
        return db.query(Notification).filter(Notification.user_id == current_user.id).all()
    return db.query(Notification).all()

@router_notifications.post("/read-all")
def mark_all_read(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.query(Notification).filter(Notification.user_id == current_user.id).update({Notification.read: True})
    db.commit()
    return {"message": "All notifications marked as read"}

@router_notifications.post("/{notification_id}/read")
def mark_notification_read(notification_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    notif.read = True
    db.commit()
    db.refresh(notif)
    return {"message": "Notification marked as read"}

@router_notifications.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(notification_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    db.delete(notif)
    db.commit()
    return

router_activity_logs = APIRouter(prefix="/activity-logs", tags=["activity-logs"])
@router_activity_logs.get("", response_model=List[ActivityLogOut])
def read_logs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    logs = db.query(ActivityLog).order_by(ActivityLog.created_at.desc()).all()
    result = []
    
    for l in logs:
        result.append({
            "id": l.id,
            "user": l.user_name or "System",
            "userId": l.user_id or "",
            "action": l.action or "",
            "target": l.target or "",
            "module": l.module or "",
            "oldValue": l.old_value,
            "newValue": l.new_value,
            "ip": l.ip or "127.0.0.1",
            "browser": l.browser or "Unknown",
            "location": l.location or "Unknown",
            "timestamp": l.created_at.strftime("%b %d, %Y %I:%M %p") if l.created_at else "Unknown"
        })
    return result

router_recycle_bin = APIRouter(prefix="/recycle-bin", tags=["recycle-bin"])

@router_recycle_bin.get("")
def read_recycle_bin(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    items = db.query(RecycleBinItem).all()
    return [
        {
            "id": r.id,
            "itemType": r.item_type,
            "itemId": r.item_id,
            "deletedAt": r.deleted_at.isoformat() if r.deleted_at else None,
            "deletedBy": r.deleted_by,
        }
        for r in items
    ]

@router_recycle_bin.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def permanently_delete(item_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    item = db.query(RecycleBinItem).filter(RecycleBinItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    db.delete(item)
    db.commit()
    return
