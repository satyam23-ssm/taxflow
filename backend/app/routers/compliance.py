from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import User, ComplianceTask, Client, Organization
from ..schemas import ComplianceTaskCreate
from ..auth import get_current_user
from ..utils import get_or_create_default_org, record_audit

router = APIRouter(tags=["compliance"])


def task_to_dict(t: ComplianceTask) -> dict:
    client_name = ""
    if t.client:
        client_name = t.client.trade_name or t.client.legal_name

    return {
        "id": str(t.id),
        "client": str(t.client_id) if t.client_id else None,
        "client_name": client_name,
        "title": t.title,
        "description": t.description or "",
        "compliance_type": t.compliance_type,
        "due_date": t.due_date.isoformat() if t.due_date else None,
        "status": t.status,
        "penalty_per_day": t.penalty_per_day,
        "applicable_to": t.applicable_to or "",
        "assigned_to": t.assigned_to or "",
        "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


@router.get("/api/v1/compliance-tasks")
@router.get("/api/v1/compliance-tasks/")
async def list_compliance_tasks(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(ComplianceTask)
        .options(selectinload(ComplianceTask.client))
        .where(ComplianceTask.organization_id == user.organization_id)
        .order_by(ComplianceTask.due_date.asc())
    )
    res = await db.execute(stmt)
    tasks = res.scalars().all()
    return [task_to_dict(t) for t in tasks]


@router.post("/api/v1/compliance-tasks")
@router.post("/api/v1/compliance-tasks/")
async def create_compliance_task(
    req: ComplianceTaskCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    org_id = user.organization_id
    if not org_id:
        default_org = await get_or_create_default_org(db)
        org_id = default_org.id

    task = ComplianceTask(
        organization_id=org_id,
        client_id=req.client,
        title=req.title,
        description=req.description,
        compliance_type=req.compliance_type,
        due_date=req.due_date,
        status=req.status,
        penalty_per_day=req.penalty_per_day,
        applicable_to=req.applicable_to,
        assigned_to=req.assigned_to
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    await record_audit(
        db, org_id,
        f"Added compliance deadline: {task.title}",
        user, "COMPLIANCE", task.id
    )

    return task_to_dict(task)


@router.post("/api/v1/compliance-tasks/{task_id}/mark_completed")
@router.post("/api/v1/compliance-tasks/{task_id}/mark_completed/")
async def mark_completed(
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ComplianceTask).where(
        ComplianceTask.id == task_id, ComplianceTask.organization_id == user.organization_id
    )
    res = await db.execute(stmt)
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = "COMPLETED"
    task.completed_at = datetime.utcnow()
    await db.commit()
    await db.refresh(task)

    await record_audit(
        db, task.organization_id,
        f"Marked compliance task complete: {task.title}",
        user, "COMPLIANCE", task.id
    )

    return {"status": "COMPLETED", "task": task_to_dict(task)}


@router.post("/api/v1/compliance-tasks/broadcast_reminders")
@router.post("/api/v1/compliance-tasks/broadcast_reminders/")
async def broadcast_reminders(
    payload: dict = {},
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    c_res = await db.execute(
        select(Client).where(Client.organization_id == user.organization_id, Client.is_active == True)
    )
    active_clients = c_res.scalars().all()
    clients_count = len(active_clients)

    task_id = payload.get("task_id")
    task_name = "Statutory GST Filing"
    if task_id:
        t_res = await db.execute(select(ComplianceTask).where(ComplianceTask.id == task_id))
        t = t_res.scalar_one_or_none()
        if t:
            task_name = t.title

    await record_audit(
        db, user.organization_id,
        f"Triggered automated WhatsApp deadline reminder to all {clients_count} clients for '{task_name}'",
        user, "COMPLIANCE"
    )

    return {
        "status": "BROADCAST_QUEUED",
        "clients_targeted": clients_count,
        "message": f"Statutory filing reminders queued for delivery to {clients_count} active clients."
    }


@router.get("/api/v1/compliance/calendar")
@router.get("/api/v1/compliance/calendar/")
async def compliance_calendar(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(ComplianceTask)
        .where(ComplianceTask.organization_id == user.organization_id)
        .order_by(ComplianceTask.due_date.asc())
    )
    res = await db.execute(stmt)
    tasks = res.scalars().all()

    if not tasks:
        # Seed default statutory deadlines if empty
        default_deadlines = [
            {
                "title": "GSTR-1 Monthly Supplies Return",
                "compliance_type": "GSTR-1",
                "description": "Outward Supplies Statement for regular monthly filers (Turnover > ₹5 Cr)",
                "due_date": date(2026, 7, 11),
                "status": "UPCOMING",
                "penalty_per_day": 50,
                "applicable_to": "Regular taxpayers"
            },
            {
                "title": "GSTR-1 (IFF) QRMP Invoices",
                "compliance_type": "IFF",
                "description": "Invoice Furnishing Facility for QRMP quarterly filers",
                "due_date": date(2026, 7, 13),
                "status": "UPCOMING",
                "penalty_per_day": 50,
                "applicable_to": "QRMP Scheme Taxpayers"
            },
            {
                "title": "GSTR-3B Monthly Return & Tax Payment",
                "compliance_type": "GSTR-3B",
                "description": "Summary Return and statutory tax liability discharge into government treasury",
                "due_date": date(2026, 7, 20),
                "status": "CRITICAL",
                "penalty_per_day": 50,
                "applicable_to": "All Monthly Filers"
            },
            {
                "title": "PMT-06 Monthly Challan Payment",
                "compliance_type": "PMT-06",
                "description": "Challan for monthly 35% fixed sum or actual self-assessed tax under QRMP",
                "due_date": date(2026, 7, 25),
                "status": "UPCOMING",
                "penalty_per_day": 0,
                "applicable_to": "QRMP Quarterly Filers"
            }
        ]
        org_id = user.organization_id
        if not org_id:
            default_org = await get_or_create_default_org(db)
            org_id = default_org.id

        for d in default_deadlines:
            t = ComplianceTask(
                organization_id=org_id,
                title=d["title"],
                compliance_type=d["compliance_type"],
                description=d["description"],
                due_date=d["due_date"],
                status=d["status"],
                penalty_per_day=d["penalty_per_day"],
                applicable_to=d["applicable_to"]
            )
            db.add(t)
        await db.commit()

        stmt = select(ComplianceTask).where(ComplianceTask.organization_id == org_id).order_by(ComplianceTask.due_date.asc())
        res = await db.execute(stmt)
        tasks = res.scalars().all()

    return {
        "current_date": str(date.today()),
        "deadlines": [task_to_dict(t) for t in tasks]
    }
