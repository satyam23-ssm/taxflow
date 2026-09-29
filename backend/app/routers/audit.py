from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import User, AuditLog
from ..auth import get_current_user

router = APIRouter(prefix="/api/v1/audit-logs", tags=["audit-logs"])


def audit_to_dict(a: AuditLog) -> dict:
    user_name = "System AI"
    if a.user:
        full_name = f"{a.user.first_name or ''} {a.user.last_name or ''}".strip()
        user_name = full_name or a.user.username or "CA Rajesh Kumar"

    formatted_time = a.timestamp.strftime("%d %b, %I:%M %p") if a.timestamp else ""

    return {
        "id": str(a.id),
        "timestamp": a.timestamp.isoformat() if a.timestamp else None,
        "formatted_time": formatted_time,
        "user_name": user_name,
        "action": a.action,
        "entity_type": a.entity_type or "SYSTEM",
        "entity_id": a.entity_id,
        "post_change_payload": a.post_change_payload or {},
    }


@router.get("")
@router.get("/")
async def list_audit_logs(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(AuditLog)
        .options(selectinload(AuditLog.user))
        .where(AuditLog.organization_id == user.organization_id)
        .order_by(AuditLog.timestamp.desc())
        .limit(30)
    )
    res = await db.execute(stmt)
    logs = res.scalars().all()
    return [audit_to_dict(a) for a in logs]
