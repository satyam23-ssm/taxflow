from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import User, Task, Document, Organization, Client
from ..auth import get_current_user
from ..utils import get_or_create_default_org, record_audit

router = APIRouter(tags=["tasks-and-docs"])


def task_to_dict(t: Task) -> dict:
    client_name = ""
    if t.client:
        client_name = t.client.trade_name or t.client.legal_name
    inv_num = t.invoice.invoice_number if t.invoice else ""
    assigned_name = t.assigned_to or ""
    if t.assigned_user:
        assigned_name = f"{t.assigned_user.first_name} {t.assigned_user.last_name}".strip() or t.assigned_user.username

    return {
        "id": str(t.id),
        "client": str(t.client_id) if t.client_id else None,
        "client_name": client_name,
        "invoice": str(t.invoice_id) if t.invoice_id else None,
        "invoice_number": inv_num,
        "title": t.title,
        "description": t.description or "",
        "priority": t.priority or "MEDIUM",
        "status": t.status or "OPEN",
        "source": t.source or "MANUAL",
        "assigned_user_id": str(t.assigned_user_id) if t.assigned_user_id else None,
        "assigned_to": assigned_name,
        "due_date": t.due_date.isoformat() if t.due_date else None,
        "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        "activity_history": t.activity_history or [],
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


def doc_to_dict(d: Document) -> dict:
    client_name = d.client.trade_name if d.client else ""
    inv_num = d.invoice.invoice_number if d.invoice else ""
    return {
        "id": str(d.id),
        "client": str(d.client_id) if d.client_id else None,
        "client_name": client_name,
        "invoice": str(d.invoice_id) if d.invoice_id else None,
        "invoice_number": inv_num,
        "document_type": d.document_type or "INVOICE",
        "original_filename": d.original_filename or "",
        "file": d.file,
        "file_url": d.file,
        "file_size": d.file_size or 0,
        "mime_type": d.mime_type or "",
        "storage_backend": d.storage_backend or "local",
        "is_processed": d.is_processed,
        "processing_status": d.processing_status or "QUEUED",
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "updated_at": d.updated_at.isoformat() if d.updated_at else None,
    }


@router.get("/api/v1/tasks")
@router.get("/api/v1/tasks/")
async def list_tasks(
    assigned_user_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    my_tasks: Optional[bool] = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Task)
        .options(
            selectinload(Task.client),
            selectinload(Task.invoice),
            selectinload(Task.assigned_user)
        )
        .where(Task.organization_id == user.organization_id)
        .order_by(Task.created_at.desc())
    )

    if my_tasks:
        stmt = stmt.where(Task.assigned_user_id == user.id)
    elif assigned_user_id and assigned_user_id != "all":
        stmt = stmt.where(Task.assigned_user_id == assigned_user_id)

    if status_filter and status_filter != "ALL":
        stmt = stmt.where(Task.status == status_filter)

    res = await db.execute(stmt)
    tasks = res.scalars().all()
    return [task_to_dict(t) for t in tasks]


@router.post("/api/v1/tasks")
@router.post("/api/v1/tasks/")
async def create_task(
    payload: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    org_id = user.organization_id
    if not org_id:
        default_org = await get_or_create_default_org(db)
        org_id = default_org.id

    assigned_user_id = payload.get("assigned_user_id")
    assigned_name = payload.get("assigned_to", "CA Rajesh Kumar")

    if assigned_user_id:
        u_res = await db.execute(select(User).where(User.id == assigned_user_id))
        target_u = u_res.scalar_one_or_none()
        if target_u:
            assigned_name = f"{target_u.first_name} {target_u.last_name}".strip() or target_u.username

    due_raw = payload.get("due_date")
    due_d = None
    if due_raw:
        try:
            due_d = date.fromisoformat(due_raw)
        except Exception:
            due_d = None

    task = Task(
        organization_id=org_id,
        client_id=payload.get("client_id"),
        invoice_id=payload.get("invoice_id"),
        title=payload.get("title", "New Task"),
        description=payload.get("description", ""),
        priority=payload.get("priority", "MEDIUM"),
        status="OPEN",
        source="ADMIN_DELEGATION",
        assigned_user_id=assigned_user_id,
        assigned_to=assigned_name,
        due_date=due_d,
        activity_history=[
            {"timestamp": datetime.utcnow().isoformat(), "action": f"Task assigned to {assigned_name} by {user.first_name or 'Admin'}"}
        ]
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # Reload with relations
    t_stmt = (
        select(Task)
        .options(selectinload(Task.client), selectinload(Task.invoice), selectinload(Task.assigned_user))
        .where(Task.id == task.id)
    )
    res = await db.execute(t_stmt)
    task = res.scalar_one()

    await record_audit(
        db, org_id,
        f"Admin assigned task '{task.title}' to {assigned_name}",
        user, "TASK", task.id
    )
    return task_to_dict(task)


@router.patch("/api/v1/tasks/{task_id}/status")
@router.patch("/api/v1/tasks/{task_id}/status/")
async def update_task_status(
    task_id: str,
    payload: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Task)
        .options(selectinload(Task.client), selectinload(Task.invoice), selectinload(Task.assigned_user))
        .where(Task.id == task_id, Task.organization_id == user.organization_id)
    )
    res = await db.execute(stmt)
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    new_status = payload.get("status")
    note = payload.get("note", "")

    if new_status:
        task.status = new_status
        if new_status == "COMPLETED":
            task.completed_at = datetime.utcnow()

    history = list(task.activity_history or [])
    action_text = f"Status updated to {new_status} by {user.first_name or user.username}"
    if note:
        action_text += f": {note}"
    history.append({"timestamp": datetime.utcnow().isoformat(), "action": action_text})
    task.activity_history = history

    await db.commit()
    await db.refresh(task)

    await record_audit(
        db, task.organization_id,
        f"Updated task status for '{task.title}' to {new_status}",
        user, "TASK", task.id
    )

    return task_to_dict(task)


@router.post("/api/v1/tasks/{task_id}/complete")
@router.post("/api/v1/tasks/{task_id}/complete/")
async def complete_task(
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Task)
        .options(selectinload(Task.client), selectinload(Task.invoice), selectinload(Task.assigned_user))
        .where(Task.id == task_id, Task.organization_id == user.organization_id)
    )
    res = await db.execute(stmt)
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = "COMPLETED"
    task.completed_at = datetime.utcnow()
    history = list(task.activity_history or [])
    history.append({"timestamp": datetime.utcnow().isoformat(), "action": f"Task completed by {user.first_name or 'User'}"})
    task.activity_history = history
    await db.commit()
    await db.refresh(task)

    await record_audit(db, task.organization_id, f"Completed task: {task.title}", user, "TASK", task.id)
    return task_to_dict(task)


@router.get("/api/v1/documents")
@router.get("/api/v1/documents/")
async def list_documents(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Document)
        .options(selectinload(Document.client), selectinload(Document.invoice))
        .where(Document.organization_id == user.organization_id)
        .order_by(Document.created_at.desc())
    )
    res = await db.execute(stmt)
    docs = res.scalars().all()
    return [doc_to_dict(d) for d in docs]


@router.post("/api/v1/documents/{doc_id}/mark_processed")
@router.post("/api/v1/documents/{doc_id}/mark_processed/")
async def mark_document_processed(
    doc_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Document).where(Document.id == doc_id, Document.organization_id == user.organization_id)
    res = await db.execute(stmt)
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.is_processed = True
    doc.processing_status = "APPROVED"
    await db.commit()
    await db.refresh(doc)

    await record_audit(db, doc.organization_id, f"Processed document: {doc.original_filename}", user, "DOCUMENT", doc.id)
    return doc_to_dict(doc)
