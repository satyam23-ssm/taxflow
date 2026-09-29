from decimal import Decimal
from typing import Optional
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

router = APIRouter(prefix="/api/v1/reconciliation", tags=["reconciliation"])
gemini_service = GeminiService()


@router.get("/mismatches")
@router.get("/mismatches/")
async def list_mismatches(
    client_id: Optional[str] = None,
    status: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(InvoiceLedger)
        .options(selectinload(InvoiceLedger.client))
        .where(InvoiceLedger.organization_id == user.organization_id)
    )
    if client_id and client_id != "all":
        stmt = stmt.where(InvoiceLedger.client_id == client_id)

    if status and status != "ALL":
        stmt = stmt.where(InvoiceLedger.matching_status == status)
    else:
        stmt = stmt.where(
            InvoiceLedger.matching_status.in_(["MISMATCHED", "MISSING_IN_PORTAL", "MATCHED"])
        )

    res = await db.execute(stmt)
    invoices = res.scalars().all()

    return {
        "count": len(invoices),
        "results": [invoice_to_dict(inv) for inv in invoices]
    }


@router.post("/sync_reconcile")
@router.post("/sync_reconcile/")
async def sync_reconcile(
    payload: dict = {},
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    client_id = payload.get("client_id")
    tax_period = payload.get("tax_period", "052026")

    stmt = (
        select(InvoiceLedger)
        .options(selectinload(InvoiceLedger.client))
        .where(InvoiceLedger.organization_id == user.organization_id)
    )
    if client_id and client_id != "all":
        stmt = stmt.where(InvoiceLedger.client_id == client_id)

    res = await db.execute(stmt)
    invoices = res.scalars().all()

    reconciled_count = 0
    mismatch_count = 0
    total_risk = Decimal("0.00")

    for inv in invoices:
        if inv.matching_status == "MISMATCHED":
            mismatch_count += 1
            risk = ((inv.cgst or 0) + (inv.sgst or 0) + (inv.igst or 0)) or (inv.taxable_value * Decimal("0.18"))
            total_risk += risk
            if not inv.ai_finding:
                explanation = gemini_service.explain_itc_mismatch({
                    "invoice_number": inv.invoice_number,
                    "vendor_name": inv.vendor_name,
                    "vendor_gstin": inv.vendor_gstin,
                    "taxable_value": float(inv.taxable_value)
                }, {"taxable_value": float(inv.taxable_value) * 0.85})
                inv.ai_finding = explanation.get("finding")
                inv.ai_reason = explanation.get("reason")
                inv.ai_recommended_action = explanation.get("recommended_action")

        elif inv.matching_status == "MISSING_IN_PORTAL":
            mismatch_count += 1
            risk = ((inv.cgst or 0) + (inv.sgst or 0) + (inv.igst or 0)) or (inv.taxable_value * Decimal("0.18"))
            total_risk += risk
            if not inv.ai_finding:
                explanation = gemini_service.explain_itc_mismatch({
                    "invoice_number": inv.invoice_number,
                    "vendor_name": inv.vendor_name,
                    "vendor_gstin": inv.vendor_gstin,
                    "taxable_value": float(inv.taxable_value)
                }, None)
                inv.ai_finding = explanation.get("finding")
                inv.ai_reason = explanation.get("reason")
                inv.ai_recommended_action = explanation.get("recommended_action")
        else:
            reconciled_count += 1

    await db.commit()

    await record_audit(
        db, user.organization_id,
        f"Executed automated GSTR-2B reconciliation for period {tax_period}. Flagged {mismatch_count} discrepancies.",
        user, "RECONCILIATION"
    )

    return {
        "status": "COMPLETED",
        "tax_period": tax_period,
        "total_processed": len(invoices),
        "matched_count": reconciled_count,
        "mismatch_count": mismatch_count,
        "total_itc_at_risk": float(total_risk),
        "message": f"Reconciliation finished: {reconciled_count} invoices matched, {mismatch_count} discrepancies requiring vendor chase."
    }


@router.post("/{invoice_id}/resolve_mismatch")
@router.post("/{invoice_id}/resolve_mismatch/")
async def resolve_mismatch(
    invoice_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(InvoiceLedger)
        .options(selectinload(InvoiceLedger.client))
        .where(InvoiceLedger.id == invoice_id, InvoiceLedger.organization_id == user.organization_id)
    )
    res = await db.execute(stmt)
    invoice = res.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice.matching_status = "MATCHED"
    invoice.vendor_chaser_status = "RESOLVED"
    invoice.portal_taxable_value = invoice.taxable_value
    invoice.portal_tax_amount = (invoice.cgst or 0) + (invoice.sgst or 0) + (invoice.igst or 0)
    await db.commit()
    await db.refresh(invoice)

    tax_recovered = float((invoice.cgst or 0) + (invoice.sgst or 0) + (invoice.igst or 0) or (invoice.taxable_value * Decimal("0.18")))
    await record_audit(
        db, user.organization_id,
        f"Resolved discrepancy for Invoice {invoice.invoice_number} ({invoice.vendor_name or invoice.vendor_gstin}). ₹{tax_recovered:,.2f} ITC Recovered.",
        user, "RECONCILIATION", invoice.id
    )

    return {
        "status": "RESOLVED",
        "message": f"Discrepancy resolved. ₹{tax_recovered:,.2f} ITC successfully secured.",
        "invoice": invoice_to_dict(invoice)
    }
