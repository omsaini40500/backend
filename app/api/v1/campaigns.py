from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import uuid4
from app.api.v1.deps import get_db, get_current_user
from app.models import Campaign, User
from app.schemas import CampaignOut, CampaignCreate, CampaignUpdate

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

def _serialize(campaign: Campaign) -> dict:
    return {
        "id": campaign.id,
        "name": campaign.name,
        "client": campaign.client,
        "status": campaign.status,
        "start": campaign.start,
        "end": campaign.end,
        "team": campaign.team or "",
        "created_by": campaign.created_by,
        "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
    }

@router.get("", response_model=List[CampaignOut])
def read_campaigns(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return [_serialize(c) for c in db.query(Campaign).all()]

@router.post("", response_model=CampaignOut, status_code=status.HTTP_201_CREATED)
def create_campaign(data: CampaignCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    campaign = Campaign(
        id=str(uuid4())[:8],
        name=data.name,
        client=data.client or "General",
        status=data.status or "Planning",
        start=data.start,
        end=data.end,
        team=data.team,
        created_by=current_user.id,
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return _serialize(campaign)

@router.patch("/{campaign_id}", response_model=CampaignOut)
def update_campaign(campaign_id: str, data: CampaignUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    if current_user.role not in ("super_admin", "admin") and campaign.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this campaign")
    if data.name is not None:
        campaign.name = data.name
    if data.client is not None:
        campaign.client = data.client
    if data.status is not None:
        campaign.status = data.status
    if data.start is not None:
        campaign.start = data.start
    if data.end is not None:
        campaign.end = data.end
    if data.team is not None:
        campaign.team = data.team
    db.commit()
    db.refresh(campaign)
    return _serialize(campaign)

@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(campaign_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    if current_user.role not in ("super_admin", "admin") and campaign.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this campaign")
    db.delete(campaign)
    db.commit()
    return
