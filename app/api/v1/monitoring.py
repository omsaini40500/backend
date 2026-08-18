from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.api.v1.deps import get_db, get_current_user
from app.models import ServiceHealth, ErrorLog, CronJob, User
from app.schemas import MonitoringServiceOut, ErrorLogOut, CronJobOut

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/services", response_model=List[MonitoringServiceOut])
def read_services(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return [
        {
            "id": s.id,
            "name": s.name,
            "status": s.status,
            "latency": s.latency,
            "uptime": s.uptime,
            "last_checked": s.last_checked.isoformat() if s.last_checked else None,
        }
        for s in db.query(ServiceHealth).all()
    ]

@router.post("/services", response_model=MonitoringServiceOut, status_code=status.HTTP_201_CREATED)
def create_service(data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from uuid import uuid4
    service = ServiceHealth(
        id=str(uuid4())[:8],
        name=data.get("name", ""),
        status=data.get("status", "Healthy"),
        latency=data.get("latency", "0ms"),
        uptime=data.get("uptime", "0%"),
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return {
        "id": service.id,
        "name": service.name,
        "status": service.status,
        "latency": service.latency,
        "uptime": service.uptime,
        "last_checked": service.last_checked.isoformat() if service.last_checked else None,
    }

@router.get("/errors", response_model=List[ErrorLogOut])
def read_errors(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return [
        {
            "id": e.id,
            "time": e.time,
            "level": e.level,
            "service": e.service,
            "message": e.message,
            "stack_trace": e.stack_trace,
        }
        for e in db.query(ErrorLog).all()
    ]

@router.post("/errors", response_model=ErrorLogOut, status_code=status.HTTP_201_CREATED)
def create_error(data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from uuid import uuid4
    error = ErrorLog(
        id=str(uuid4())[:8],
        time=data.get("time", ""),
        level=data.get("level", "INFO"),
        service=data.get("service", ""),
        message=data.get("message", ""),
        stack_trace=data.get("stackTrace"),
    )
    db.add(error)
    db.commit()
    db.refresh(error)
    return {
        "id": error.id,
        "time": error.time,
        "level": error.level,
        "service": error.service,
        "message": error.message,
        "stack_trace": error.stack_trace,
    }

@router.get("/cron-jobs", response_model=List[CronJobOut])
def read_cron_jobs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return [
        {
            "id": c.id,
            "name": c.name,
            "schedule": c.schedule,
            "last_run": c.last_run,
            "next_run": c.next_run,
            "duration": c.duration,
            "status": c.status,
        }
        for c in db.query(CronJob).all()
    ]

@router.post("/cron-jobs", response_model=CronJobOut, status_code=status.HTTP_201_CREATED)
def create_cron_job(data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from uuid import uuid4
    job = CronJob(
        id=str(uuid4())[:8],
        name=data.get("name", ""),
        schedule=data.get("schedule", ""),
        last_run=data.get("lastRun", ""),
        next_run=data.get("nextRun", ""),
        duration=data.get("duration", ""),
        status=data.get("status", "Success"),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return {
        "id": job.id,
        "name": job.name,
        "schedule": job.schedule,
        "last_run": job.last_run,
        "next_run": job.next_run,
        "duration": job.duration,
        "status": job.status,
    }
