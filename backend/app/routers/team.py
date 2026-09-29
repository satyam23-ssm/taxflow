from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import User, Task, Organization
from ..auth import get_current_user, get_password_hash
from ..utils import record_audit

router = APIRouter(prefix="/api/v1/team", tags=["team"])


def employee_to_dict(u: User) -> dict:
    tasks = u.assigned_tasks or []
    active_tasks = sum(1 for t in tasks if t.status in ["OPEN", "IN_PROGRESS"])
    completed_tasks = sum(1 for t in tasks if t.status == "COMPLETED")
    full_name = f"{u.first_name} {u.last_name}".strip() or u.username

    return {
        "id": str(u.id),
        "name": full_name,
        "username": u.username,
        "email": u.email,
        "role": u.role or "STAFF_ACCOUNTANT",
        "designation": u.designation or ("Managing Partner" if u.role == "CA_FIRM_PARTNER" else "Staff Accountant"),
        "work_status": u.work_status or "WORKING",
        "phone_number": u.phone_number or "",
        "is_active": u.is_active,
        "is_admin": u.role == "CA_FIRM_PARTNER" or u.is_staff or u.is_superuser,
        "tasks_count": len(tasks),
        "active_tasks_count": active_tasks,
        "completed_tasks_count": completed_tasks,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }


@router.get("/employees")
@router.get("/employees/")
async def list_employees(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(User)
        .options(selectinload(User.assigned_tasks))
        .where(User.organization_id == user.organization_id)
        .order_by(User.first_name.asc())
    )
    res = await db.execute(stmt)
    users = res.scalars().all()
    return [employee_to_dict(u) for u in users]


@router.post("/employees")
@router.post("/employees/")
async def create_employee(
    payload: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    email = payload.get("email")
    first_name = payload.get("first_name", "")
    last_name = payload.get("last_name", "")
    username = payload.get("username") or email
    password = payload.get("password", "welcome123")
    role = payload.get("role", "STAFF_ACCOUNTANT")
    designation = payload.get("designation", "Staff Accountant")
    work_status = payload.get("work_status", "WORKING")
    phone = payload.get("phone_number", "")

    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User with this email already exists")

    new_emp = User(
        organization_id=user.organization_id,
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        first_name=first_name,
        last_name=last_name,
        role=role,
        designation=designation,
        work_status=work_status,
        phone_number=phone,
        is_active=True,
        is_staff=(role == "CA_FIRM_PARTNER")
    )
    db.add(new_emp)
    await db.commit()
    await db.refresh(new_emp)

    await record_audit(
        db, user.organization_id,
        f"Admin added new team member: {first_name} {last_name} ({designation})",
        user, "USER", new_emp.id
    )

    # Reload with tasks
    stmt = select(User).options(selectinload(User.assigned_tasks)).where(User.id == new_emp.id)
    res = await db.execute(stmt)
    new_emp = res.scalar_one()

    return employee_to_dict(new_emp)


@router.patch("/employees/{emp_id}/status")
@router.patch("/employees/{emp_id}/status/")
async def update_employee_status(
    emp_id: str,
    payload: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(User)
        .options(selectinload(User.assigned_tasks))
        .where(User.id == emp_id, User.organization_id == user.organization_id)
    )
    res = await db.execute(stmt)
    emp = res.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    new_status = payload.get("work_status")
    if new_status:
        emp.work_status = new_status

    if "designation" in payload:
        emp.designation = payload["designation"]

    await db.commit()
    await db.refresh(emp)

    await record_audit(
        db, user.organization_id,
        f"Updated status for {emp.first_name} {emp.last_name} to {emp.work_status}",
        user, "USER", emp.id
    )

    return employee_to_dict(emp)


@router.get("/workload")
@router.get("/workload/")
async def team_workload_metrics(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(User)
        .options(selectinload(User.assigned_tasks))
        .where(User.organization_id == user.organization_id)
    )
    res = await db.execute(stmt)
    users = res.scalars().all()

    total_employees = len(users)
    working_now = sum(1 for u in users if u.work_status == "WORKING")
    in_review = sum(1 for u in users if u.work_status == "IN_REVIEW")
    on_leave = sum(1 for u in users if u.work_status == "ON_LEAVE")

    t_stmt = select(Task).where(Task.organization_id == user.organization_id)
    t_res = await db.execute(t_stmt)
    tasks = t_res.scalars().all()

    total_tasks = len(tasks)
    open_tasks = sum(1 for t in tasks if t.status == "OPEN")
    in_progress_tasks = sum(1 for t in tasks if t.status == "IN_PROGRESS")
    completed_tasks = sum(1 for t in tasks if t.status == "COMPLETED")

    return {
        "total_employees": total_employees,
        "currently_working": working_now,
        "in_review": in_review,
        "on_leave": on_leave,
        "total_tasks": total_tasks,
        "open_tasks": open_tasks,
        "in_progress_tasks": in_progress_tasks,
        "completed_tasks": completed_tasks,
        "employee_distribution": [
            {
                "id": str(u.id),
                "name": f"{u.first_name} {u.last_name}".strip() or u.username,
                "role": u.designation or u.role,
                "status": u.work_status or "WORKING",
                "active_tasks": sum(1 for t in (u.assigned_tasks or []) if t.status in ["OPEN", "IN_PROGRESS"]),
                "completed_tasks": sum(1 for t in (u.assigned_tasks or []) if t.status == "COMPLETED"),
            }
            for u in users
        ]
    }
