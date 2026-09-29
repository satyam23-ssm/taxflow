from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import Organization, AuditLog, User


async def get_or_create_default_org(db: AsyncSession) -> Organization:
    result = await db.execute(select(Organization).limit(1))
    org = result.scalar_one_or_none()
    if not org:
        org = Organization(
            name="Kumar & Associates (Chartered Accountants)",
            subscription_tier="CA_FIRM"
        )
        db.add(org)
        await db.commit()
        await db.refresh(org)
    return org


async def record_audit(
    db: AsyncSession,
    org_id: str,
    action: str,
    user: Optional[User] = None,
    entity_type: str = "SYSTEM",
    entity_id: Optional[str] = None,
    post_payload: Optional[dict] = None
):
    try:
        log = AuditLog(
            organization_id=org_id,
            user_id=user.id if user else None,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            post_change_payload=post_payload or {}
        )
        db.add(log)
        await db.commit()
    except Exception:
        pass
