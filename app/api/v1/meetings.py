from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import uuid4
from app.api.v1.deps import get_db, get_current_user
from app.models import Meeting, User
from app.schemas import MeetingOut, MeetingCreate, MeetingUpdate

router = APIRouter(prefix="/meetings", tags=["meetings"])

def _serialize(meeting: Meeting) -> dict:
    return {
        "id": meeting.id,
        "title": meeting.title,
        "date": meeting.date,
        "time": meeting.time,
        "duration": meeting.duration,
        "type": meeting.type,
        "participants": meeting.participants or "",
        "agenda": meeting.agenda or "",
        "status": meeting.status,
        "meetingLink": meeting.meeting_link,
        "createdBy": meeting.created_by,
        "createdAt": meeting.created_at.isoformat() if meeting.created_at else None,
    }

@router.get("", response_model=List[MeetingOut])
def read_meetings(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return [_serialize(m) for m in db.query(Meeting).order_by(Meeting.date.desc()).all()]

@router.post("", response_model=MeetingOut, status_code=status.HTTP_201_CREATED)
def create_meeting(data: MeetingCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    meeting = Meeting(
        id=str(uuid4())[:8],
        title=data.title,
        date=data.date,
        time=data.time,
        duration=data.duration,
        type=data.type,
        participants=data.participants,
        agenda=data.agenda,
        status=data.status or "Upcoming",
        meeting_link=data.meeting_link,
        created_by=current_user.id,
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return _serialize(meeting)

@router.patch("/{meeting_id}", response_model=MeetingOut)
def update_meeting(meeting_id: str, data: MeetingUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    if current_user.role not in ("super_admin", "admin") and meeting.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this meeting")
    if data.title is not None:
        meeting.title = data.title
    if data.date is not None:
        meeting.date = data.date
    if data.time is not None:
        meeting.time = data.time
    if data.duration is not None:
        meeting.duration = data.duration
    if data.type is not None:
        meeting.type = data.type
    if data.participants is not None:
        meeting.participants = data.participants
    if data.agenda is not None:
        meeting.agenda = data.agenda
    if data.status is not None:
        meeting.status = data.status
    if data.meeting_link is not None:
        meeting.meeting_link = data.meeting_link
    db.commit()
    db.refresh(meeting)
    return _serialize(meeting)

@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting(meeting_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    if current_user.role not in ("super_admin", "admin") and meeting.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this meeting")
    db.delete(meeting)
    db.commit()
    return
