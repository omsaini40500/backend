from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import uuid4
from app.api.v1.deps import get_db, get_current_user
from app.models import Automation, AutomationTemplate, AutomationHistory
from app.schemas import AutomationOut, AutomationCreate, AutomationUpdate, AutomationTemplateOut, AutomationHistoryOut

router = APIRouter(prefix="/automations", tags=["automations"])

def _serialize_automation(automation: Automation) -> dict:
    return {
        "id": automation.id,
        "name": automation.name,
        "trigger": automation.trigger,
        "condition": automation.condition,
        "action": automation.action,
        "status": automation.status,
        "runs": automation.runs,
        "lastRun": automation.last_run,
        "createdAt": automation.created_at.isoformat() if automation.created_at else None,
    }

def _serialize_template(template: AutomationTemplate) -> dict:
    return {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "icon": template.icon,
        "trigger": template.trigger,
        "action": template.action,
        "uses": template.uses,
    }

def _serialize_history(history: AutomationHistory) -> dict:
    return {
        "id": history.id,
        "automationId": history.automation_id,
        "automationName": history.automation_name,
        "result": history.result,
        "time": history.time,
        "detail": history.detail,
    }

@router.get("", response_model=List[AutomationOut])
def read_automations(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return [_serialize_automation(a) for a in db.query(Automation).all()]

@router.post("", response_model=AutomationOut, status_code=status.HTTP_201_CREATED)
def create_automation(data: AutomationCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    automation = Automation(
        id=str(uuid4())[:8],
        name=data.name,
        trigger=data.trigger,
        condition=data.condition,
        action=data.action,
        status=data.status or "Active",
    )
    db.add(automation)
    db.commit()
    db.refresh(automation)
    return _serialize_automation(automation)

@router.patch("/{automation_id}", response_model=AutomationOut)
def update_automation(automation_id: str, data: AutomationUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    automation = db.query(Automation).filter(Automation.id == automation_id).first()
    if not automation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automation not found")
    if data.name is not None:
        automation.name = data.name
    if data.trigger is not None:
        automation.trigger = data.trigger
    if data.condition is not None:
        automation.condition = data.condition
    if data.action is not None:
        automation.action = data.action
    if data.status is not None:
        automation.status = data.status
    if data.runs is not None:
        automation.runs = data.runs
    if data.last_run is not None:
        automation.last_run = data.last_run
    db.commit()
    db.refresh(automation)
    return _serialize_automation(automation)

@router.delete("/{automation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_automation(automation_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    automation = db.query(Automation).filter(Automation.id == automation_id).first()
    if not automation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automation not found")
    db.delete(automation)
    db.commit()
    return

@router.get("/templates", response_model=List[AutomationTemplateOut])
def read_templates(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return [_serialize_template(t) for t in db.query(AutomationTemplate).all()]

@router.get("/history", response_model=List[AutomationHistoryOut])
def read_history(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return [_serialize_history(h) for h in db.query(AutomationHistory).order_by(AutomationHistory.time.desc()).all()]
