from decimal import Decimal
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import User, LegalNoticeTracker, Client
from ..schemas import NoticeCreate
from ..auth import get_current_user
from ..services.gemini_service import GeminiService
from ..utils import get_or_create_default_org, record_audit

router = APIRouter(prefix="/api/v1/notices", tags=["notices"])
gemini_service = GeminiService()


def notice_to_dict(n: LegalNoticeTracker) -> dict:
    client_name = ""
    client_gstin = ""
    if n.client:
        client_name = n.client.trade_name or n.client.legal_name
        client_gstin = n.client.gstin

    return {
        "id": str(n.id),
        "client": str(n.client_id) if n.client_id else None,
        "client_name": client_name,
        "client_gstin": client_gstin,
        "notice_type": n.notice_type,
        "notice_reference": n.notice_reference,
        "issue_date": n.issue_date.isoformat() if n.issue_date else None,
        "deadline_date": n.deadline_date.isoformat() if n.deadline_date else None,
        "cited_sections": n.cited_sections or [],
        "disputed_tax_value": float(n.disputed_tax_value or 0),
        "raw_notice_text": n.raw_notice_text or "",
        "ai_summary": n.ai_summary or "",
        "ai_recommendation": n.ai_recommendation or "",
        "generated_asmt11_draft": n.generated_asmt11_draft or "",
        "is_resolved": n.is_resolved,
        "created_at": n.created_at.isoformat() if n.created_at else None,
        "updated_at": n.updated_at.isoformat() if n.updated_at else None,
    }


@router.get("")
@router.get("/")
async def list_notices(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(LegalNoticeTracker)
        .options(selectinload(LegalNoticeTracker.client))
        .where(LegalNoticeTracker.organization_id == user.organization_id)
        .order_by(LegalNoticeTracker.deadline_date.asc())
    )
    res = await db.execute(stmt)
    notices = res.scalars().all()
    return [notice_to_dict(n) for n in notices]


@router.post("")
@router.post("/")
async def create_notice(
    req: NoticeCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    org_id = user.organization_id
    if not org_id:
        default_org = await get_or_create_default_org(db)
        org_id = default_org.id

    notice = LegalNoticeTracker(
        organization_id=org_id,
        client_id=req.client,
        notice_type=req.notice_type,
        notice_reference=req.notice_reference,
        issue_date=req.issue_date,
        deadline_date=req.deadline_date,
        cited_sections=req.cited_sections,
        disputed_tax_value=req.disputed_tax_value,
        raw_notice_text=req.raw_notice_text
    )
    db.add(notice)
    await db.commit()
    await db.refresh(notice)

    # Reload client for response
    stmt = select(LegalNoticeTracker).options(selectinload(LegalNoticeTracker.client)).where(LegalNoticeTracker.id == notice.id)
    res = await db.execute(stmt)
    notice = res.scalar_one()

    await record_audit(
        db, org_id,
        f"Logged new statutory GST notice: {notice.notice_type} (Ref: {notice.notice_reference})",
        user, "NOTICE", notice.id
    )

    return notice_to_dict(notice)


@router.get("/{notice_id}")
@router.get("/{notice_id}/")
async def get_notice(
    notice_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(LegalNoticeTracker)
        .options(selectinload(LegalNoticeTracker.client))
        .where(LegalNoticeTracker.id == notice_id, LegalNoticeTracker.organization_id == user.organization_id)
    )
    res = await db.execute(stmt)
    notice = res.scalar_one_or_none()
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    return notice_to_dict(notice)


@router.post("/{notice_id}/generate_draft")
@router.post("/{notice_id}/generate_draft/")
async def generate_draft(
    notice_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(LegalNoticeTracker)
        .options(selectinload(LegalNoticeTracker.client))
        .where(LegalNoticeTracker.id == notice_id, LegalNoticeTracker.organization_id == user.organization_id)
    )
    res = await db.execute(stmt)
    notice = res.scalar_one_or_none()
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")

    client_name = "The Taxpayer"
    gstin = "27ABCDE1234F1Z5"
    if notice.client:
        client_name = notice.client.trade_name or notice.client.legal_name
        gstin = notice.client.gstin

    draft_res = gemini_service.summarize_and_draft_notice(
        notice_type=notice.notice_type,
        notice_ref=notice.notice_reference,
        client_name=client_name,
        gstin=gstin,
        demand_amount=float(notice.disputed_tax_value or 0),
        raw_text=notice.raw_notice_text or f"Notice {notice.notice_type} regarding GSTR-3B vs 2B reconciliation variance."
    )

    notice.ai_summary = draft_res.get("summary")
    notice.generated_asmt11_draft = draft_res.get("reply_draft")
    if draft_res.get("cited_sections"):
        notice.cited_sections = draft_res.get("cited_sections")

    await db.commit()
    await db.refresh(notice)

    await record_audit(
        db, notice.organization_id,
        f"Generated AI legal reply draft for Notice {notice.notice_reference}",
        user, "NOTICE", notice.id
    )

    return {
        "status": "DRAFT_GENERATED",
        "reply_draft": notice.generated_asmt11_draft,
        "citations": draft_res.get("statutory_citations", []),
        "notice": notice_to_dict(notice)
    }
