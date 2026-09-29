from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import User, InvoiceLedger
from ..auth import get_current_user
from ..services.gemini_service import GeminiService
from ..utils import record_audit
from .invoices import invoice_to_dict

router = APIRouter(prefix="/api/v1/chaser", tags=["chaser"])
gemini_service = GeminiService()


@router.post("/generate_message")
@router.post("/generate_message/")
async def generate_message(
    payload: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    invoice_id = payload.get("invoice_id")
    channel = payload.get("channel", "whatsapp")

    if not invoice_id:
        raise HTTPException(status_code=400, detail="invoice_id required")

    stmt = (
        select(InvoiceLedger)
        .options(selectinload(InvoiceLedger.client))
        .where(InvoiceLedger.id == invoice_id, InvoiceLedger.organization_id == user.organization_id)
    )
    res = await db.execute(stmt)
    invoice = res.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    tax_at_risk = float((invoice.cgst or 0) + (invoice.sgst or 0) + (invoice.igst or 0)) or (float(invoice.taxable_value) * 0.18)
    client_name = ""
    if invoice.client:
        client_name = invoice.client.trade_name or invoice.client.legal_name

    chaser_data = gemini_service.generate_vendor_chaser_message(
        vendor_name=invoice.vendor_name or f"Supplier ({invoice.vendor_gstin})",
        vendor_gstin=invoice.vendor_gstin,
        client_name=client_name or "Our Client",
        invoice_number=invoice.invoice_number,
        invoice_date=str(invoice.invoice_date),
        taxable_value=float(invoice.taxable_value),
        tax_at_risk=tax_at_risk,
        mismatch_reason=invoice.ai_reason or "Invoice not appearing in GSTR-2B",
        channel=channel
    )

    invoice.vendor_chaser_status = "CHASE_GENERATED"
    invoice.vendor_chaser_message = chaser_data.get("message_body")
    await db.commit()
    await db.refresh(invoice)

    return {
        "status": "GENERATED",
        "subject": chaser_data.get("subject"),
        "message_body": chaser_data.get("message_body"),
        "channel": channel,
        "invoice": invoice_to_dict(invoice)
    }


@router.post("/dispatch")
@router.post("/dispatch/")
async def dispatch(
    payload: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    invoice_id = payload.get("invoice_id")
    channel = payload.get("channel", "whatsapp")
    custom_message = payload.get("message")

    stmt = (
        select(InvoiceLedger)
        .options(selectinload(InvoiceLedger.client))
        .where(InvoiceLedger.id == invoice_id, InvoiceLedger.organization_id == user.organization_id)
    )
    res = await db.execute(stmt)
    invoice = res.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice.vendor_chaser_status = "CHASE_SENT" if channel == "whatsapp" else "CHASE_SENT_EMAIL"
    if custom_message:
        invoice.vendor_chaser_message = custom_message

    history = list(invoice.chaser_history or [])
    history.append({
        "timestamp": datetime.utcnow().isoformat(),
        "channel": channel,
        "status": "SENT",
        "note": f"Dispatched via {channel.upper()} by CA"
    })
    invoice.chaser_history = history
    invoice.roi_minutes_saved = (invoice.roi_minutes_saved or 0) + 15
    await db.commit()
    await db.refresh(invoice)

    await record_audit(
        db, invoice.organization_id,
        f"Dispatched Vendor Chaser ({channel.upper()}) to {invoice.vendor_name or invoice.vendor_gstin} for Invoice {invoice.invoice_number}",
        user, "VENDOR_CHASER", invoice.id
    )

    return {
        "status": "DISPATCHED",
        "message": f"Vendor chaser logged and marked as sent via {channel.upper()}.",
        "invoice": invoice_to_dict(invoice)
    }


@router.post("/record_response")
@router.post("/record_response/")
async def record_response(
    payload: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    invoice_id = payload.get("invoice_id")
    response_text = payload.get("response_text", "Vendor confirmed filing in next GSTR-1 cycle.")
    mark_resolved = payload.get("mark_resolved", True)

    stmt = (
        select(InvoiceLedger)
        .options(selectinload(InvoiceLedger.client))
        .where(InvoiceLedger.id == invoice_id, InvoiceLedger.organization_id == user.organization_id)
    )
    res = await db.execute(stmt)
    invoice = res.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice.vendor_chaser_status = "RESOLVED" if mark_resolved else "VENDOR_RESPONDED"
    if mark_resolved:
        invoice.matching_status = "MATCHED"
        invoice.portal_taxable_value = invoice.taxable_value

    history = list(invoice.chaser_history or [])
    history.append({
        "timestamp": datetime.utcnow().isoformat(),
        "status": "VENDOR_RESPONSE",
        "response": response_text
    })
    invoice.chaser_history = history
    await db.commit()
    await db.refresh(invoice)

    await record_audit(
        db, invoice.organization_id,
        f"Recorded vendor response for Invoice {invoice.invoice_number}: '{response_text}'. Status updated to {invoice.vendor_chaser_status}.",
        user, "VENDOR_CHASER", invoice.id
    )

    return {
        "status": "RECORDED",
        "message": "Vendor response successfully recorded and reconciliation updated.",
        "invoice": invoice_to_dict(invoice)
    }
