from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import User, Client, InvoiceLedger, LegalNoticeTracker, ComplianceTask
from ..schemas import ClientCreate, ClientResponse
from ..auth import get_current_user
from ..utils import get_or_create_default_org, record_audit

router = APIRouter(prefix="/api/v1/clients", tags=["clients"])


def client_to_dict(c: Client) -> dict:
    invoices_list = c.invoices or []
    notices_list = c.notices or []
    active_mismatches = sum(
        1 for inv in invoices_list
        if inv.matching_status in ["MISMATCHED", "MISSING_IN_PORTAL"]
    )
    active_notices = sum(1 for n in notices_list if not n.is_resolved)
    return {
        "id": str(c.id),
        "legal_name": c.legal_name,
        "trade_name": c.trade_name or c.legal_name,
        "gstin": c.gstin,
        "pan": c.pan or "",
        "email": c.email or "",
        "phone_number": c.phone_number,
        "address": c.address or "",
        "assigned_ca": c.assigned_ca or "CA Rajesh Kumar",
        "compliance_status": c.compliance_status or "COMPLIANT",
        "is_active": c.is_active,
        "notes": c.notes or "",
        "active_mismatches_count": active_mismatches,
        "active_notices_count": active_notices,
        "total_invoices_count": len(invoices_list),
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


@router.get("")
@router.get("/")
async def list_clients(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Client)
        .options(selectinload(Client.invoices), selectinload(Client.notices))
        .where(Client.organization_id == user.organization_id)
        .order_by(Client.legal_name)
    )
    res = await db.execute(stmt)
    clients = res.scalars().all()
    return [client_to_dict(c) for c in clients]


@router.post("")
@router.post("/")
async def create_client(
    req: ClientCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    org_id = user.organization_id
    if not org_id:
        default_org = await get_or_create_default_org(db)
        org_id = default_org.id

    client = Client(
        organization_id=org_id,
        legal_name=req.legal_name,
        trade_name=req.trade_name or req.legal_name,
        gstin=req.gstin,
        pan=req.pan,
        email=req.email,
        phone_number=req.phone_number,
        address=req.address,
        assigned_ca=req.assigned_ca,
        compliance_status=req.compliance_status,
        notes=req.notes
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)

    await record_audit(
        db, org_id,
        f"Added new client: {client.trade_name or client.legal_name} ({client.gstin})",
        user, "CLIENT", client.id
    )

    return client_to_dict(client)


@router.get("/{client_id}")
@router.get("/{client_id}/")
async def get_client(
    client_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Client)
        .options(selectinload(Client.invoices), selectinload(Client.notices))
        .where(Client.id == client_id, Client.organization_id == user.organization_id)
    )
    res = await db.execute(stmt)
    client = res.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client_to_dict(client)


@router.put("/{client_id}")
@router.put("/{client_id}/")
@router.patch("/{client_id}")
@router.patch("/{client_id}/")
async def update_client(
    client_id: str,
    req: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Client).where(Client.id == client_id, Client.organization_id == user.organization_id)
    res = await db.execute(stmt)
    client = res.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    for k, v in req.items():
        if hasattr(client, k) and k not in ["id", "organization_id"]:
            setattr(client, k, v)

    await db.commit()
    await db.refresh(client)

    await record_audit(
        db, user.organization_id,
        f"Updated client profile: {client.trade_name or client.legal_name}",
        user, "CLIENT", client.id
    )
    return client_to_dict(client)


@router.delete("/{client_id}")
@router.delete("/{client_id}/")
async def delete_client(
    client_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Client).where(Client.id == client_id, Client.organization_id == user.organization_id)
    res = await db.execute(stmt)
    client = res.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    name = client.trade_name or client.legal_name
    await db.delete(client)
    await db.commit()

    await record_audit(
        db, user.organization_id,
        f"Archived / deleted client: {name}",
        user, "CLIENT"
    )
    return {"status": "DELETED"}


@router.get("/{client_id}/profile_details")
@router.get("/{client_id}/profile_details/")
async def client_profile_details(
    client_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Client)
        .options(
            selectinload(Client.invoices),
            selectinload(Client.notices),
            selectinload(Client.compliance_tasks)
        )
        .where(Client.id == client_id, Client.organization_id == user.organization_id)
    )
    res = await db.execute(stmt)
    client = res.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    invoices = client.invoices or []
    notices = client.notices or []
    tasks = client.compliance_tasks or []

    matched_count = sum(1 for inv in invoices if inv.matching_status == "MATCHED")
    mismatched_count = sum(1 for inv in invoices if inv.matching_status in ["MISMATCHED", "MISSING_IN_PORTAL"])
    total_itc_claimed = sum(
        float(inv.total_amount or 0) for inv in invoices if inv.matching_status == "MATCHED"
    )
    itc_at_risk = sum(
        float((inv.cgst or 0) + (inv.sgst or 0) + (inv.igst or 0))
        for inv in invoices if inv.matching_status in ["MISMATCHED", "MISSING_IN_PORTAL"]
    )

    from .invoices import invoice_to_dict
    from .notices import notice_to_dict
    from .compliance import task_to_dict

    return {
        "client": client_to_dict(client),
        "invoices": [invoice_to_dict(inv) for inv in invoices[:20]],
        "notices": [notice_to_dict(n) for n in notices],
        "tasks": [task_to_dict(t) for t in tasks],
        "summary": {
            "total_invoices": len(invoices),
            "matched_invoices": matched_count,
            "mismatches": mismatched_count,
            "total_itc_claimed": total_itc_claimed,
            "itc_at_risk": itc_at_risk
        }
    }
