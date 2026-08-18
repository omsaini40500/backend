from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import uuid4
from app.api.v1.deps import get_db, get_current_user
from app.models import Announcement, User
from app.schemas import AnnouncementOut, AnnouncementCreate, AnnouncementUpdate

router = APIRouter(prefix="/announcements", tags=["announcements"])

def _serialize(announcement: Announcement) -> dict:
    return {
        "id": announcement.id,
        "title": announcement.title,
        "type": announcement.type,
        "priority": announcement.priority,
        "author": announcement.author,
        "date": announcement.date,
        "content": announcement.content,
        "pinned": announcement.pinned,
        "createdAt": announcement.created_at.isoformat() if announcement.created_at else None,
    }

@router.get("", response_model=List[AnnouncementOut])
def read_announcements(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return [_serialize(a) for a in db.query(Announcement).order_by(Announcement.pinned.desc(), Announcement.created_at.desc()).all()]

@router.post("", response_model=AnnouncementOut, status_code=status.HTTP_201_CREATED)
def create_announcement(data: AnnouncementCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    announcement = Announcement(
        id=str(uuid4())[:8],
        title=data.title,
        type=data.type,
        priority=data.priority or "medium",
        author=data.author or current_user.name,
        date=data.date or "",
        content=data.content,
        pinned=data.pinned or False,
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    return _serialize(announcement)

@router.patch("/{announcement_id}", response_model=AnnouncementOut)
def update_announcement(announcement_id: str, data: AnnouncementUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this announcement")
    if data.title is not None:
        announcement.title = data.title
    if data.type is not None:
        announcement.type = data.type
    if data.priority is not None:
        announcement.priority = data.priority
    if data.author is not None:
        announcement.author = data.author
    if data.date is not None:
        announcement.date = data.date
    if data.content is not None:
        announcement.content = data.content
    if data.pinned is not None:
        announcement.pinned = data.pinned
    db.commit()
    db.refresh(announcement)
    return _serialize(announcement)

@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_announcement(announcement_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this announcement")
    db.delete(announcement)
    db.commit()
    return
