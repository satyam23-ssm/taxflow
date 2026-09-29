from decimal import Decimal
from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..config import settings
from ..database import get_db
from ..models import User, Client, InvoiceLedger, WhatsAppInboundMessage, Organization
from ..auth import get_current_user
from ..services.gemini_service import GeminiService
from ..services.whatsapp import (
    WhatsAppCloudClient,
    extract_messages_from_webhook,
    phone_variants,
    verify_meta_signature,
)
from ..utils import get_or_create_default_org, record_audit
from .invoices import invoice_to_dict

router = APIRouter(tags=["connectors"])
gemini_service = GeminiService()


def whatsapp_msg_to_dict(m: WhatsAppInboundMessage) -> dict:
    client_name = ""
    if m.client:
        client_name = m.client.trade_name or m.client.legal_name
    return {
        "id": str(m.id),
        "client_name": client_name,
        "direction": m.direction or "INBOUND",
        "processing_status": m.processing_status or "RECEIVED",
        "whatsapp_message_id": m.whatsapp_message_id,
        "sender_phone": m.sender_phone or "",
        "message_type": m.message_type or "",
        "text_body": m.text_body or "",
        "media_id": m.media_id or "",
        "media_mime_type": m.media_mime_type or "",
        "error_message": m.error_message or "",
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


@router.get("/api/v1/connectors")
@router.get("/api/v1/connectors/")
async def list_connectors(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    whatsapp_client = WhatsAppCloudClient()
    base_url = str(request.base_url).rstrip('/')
    webhook_url = f"{base_url}/api/v1/webhooks/whatsapp/"

    whatsapp_missing = list(whatsapp_client.missing_config)
    if not settings.WHATSAPP_VERIFY_TOKEN:
        whatsapp_missing.append('WHATSAPP_VERIFY_TOKEN')

    gsp_missing = []
    if not settings.GSP_BASE_URL:
        gsp_missing.append('GSP_BASE_URL')
    if not settings.GSP_API_KEY:
        gsp_missing.append('GSP_API_KEY')

    res = await db.execute(
        select(WhatsAppInboundMessage).where(WhatsAppInboundMessage.organization_id == user.organization_id)
    )
    wa_count = len(res.scalars().all())

    return [
        {
            'connector_type': 'WHATSAPP',
            'display_name': 'WhatsApp (Meta Cloud API)',
            'status': 'ACTIVE' if not whatsapp_missing else 'NOT_CONFIGURED',
            'is_enabled': True,
            'missing_config': whatsapp_missing,
            'webhook_url': webhook_url,
            'phone_number_id': settings.WHATSAPP_PHONE_NUMBER_ID,
            'business_account_id': settings.WHATSAPP_BUSINESS_ACCOUNT_ID,
            'message_count': wa_count,
        },
        {
            'connector_type': 'TALLY',
            'display_name': 'Tally Desktop Agent',
            'status': 'NEEDS_ATTENTION',
            'is_enabled': True,
            'missing_config': [],
            'websocket_url': 'ws://localhost:8000/ws/agent/sync-stream/',
            'note': 'Agent socket is ready; desktop agent connects with a client token.',
        },
        {
            'connector_type': 'GSP',
            'display_name': 'GSTN Gateway (GSP)',
            'status': 'ACTIVE' if not gsp_missing else 'NOT_CONFIGURED',
            'is_enabled': True,
            'missing_config': gsp_missing,
            'provider_name': settings.GSP_PROVIDER_NAME or 'Government NIC Sandbox',
            'base_url': settings.GSP_BASE_URL,
        },
    ]


@router.get("/api/v1/connectors/whatsapp_messages")
@router.get("/api/v1/connectors/whatsapp_messages/")
async def list_whatsapp_messages(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(WhatsAppInboundMessage)
        .options(selectinload(WhatsAppInboundMessage.client))
        .where(WhatsAppInboundMessage.organization_id == user.organization_id)
        .order_by(WhatsAppInboundMessage.created_at.desc())
        .limit(25)
    )
    res = await db.execute(stmt)
    messages = res.scalars().all()
    return [whatsapp_msg_to_dict(m) for m in messages]


@router.post("/api/v1/connectors/whatsapp/simulate-inbound-invoice")
@router.post("/api/v1/connectors/whatsapp/simulate-inbound-invoice/")
async def simulate_inbound_invoice(
    payload: dict = {},
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    client_id = payload.get("client_id")
    client = None
    if client_id:
        c_res = await db.execute(select(Client).where(Client.id == client_id))
        client = c_res.scalar_one_or_none()

    if not client:
        c_res = await db.execute(
            select(Client).where(Client.organization_id == user.organization_id, Client.is_active == True)
        )
        client = c_res.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=400, detail="No active client found for simulation.")

    media_id = payload.get("media_id") or f"WA-IMG-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    extracted = gemini_service.extract_invoice("invoice_simulated.jpg")

    message = WhatsAppInboundMessage(
        organization_id=client.organization_id,
        client_id=client.id,
        sender_phone=client.phone_number,
        message_type="image",
        media_id=media_id,
        media_mime_type="image/jpeg",
        processing_status="PROCESSED",
        raw_payload=extracted,
    )
    db.add(message)

    inv_date_str = extracted.get("invoice_date", str(date.today()))
    try:
        inv_date = date.fromisoformat(inv_date_str)
    except Exception:
        inv_date = date.today()

    taxable = Decimal(str(extracted.get("taxable_value", "85000.00")))
    cgst = Decimal(str(extracted.get("cgst", "7650.00")))
    sgst = Decimal(str(extracted.get("sgst", "7650.00")))
    igst = Decimal(str(extracted.get("igst", "0.00")))
    cess = Decimal(str(extracted.get("cess", "0.00")))
    total = Decimal(str(extracted.get("total_amount", "100300.00")))

    invoice = InvoiceLedger(
        organization_id=client.organization_id,
        client_id=client.id,
        source="WHATSAPP",
        processing_status="PENDING_REVIEW",
        buyer_gstin=client.gstin,
        invoice_number=extracted.get("invoice_number", f"WA-{media_id[-6:]}"),
        invoice_date=inv_date,
        vendor_name=extracted.get("vendor_name", "Tata Communications Ltd"),
        vendor_gstin=extracted.get("vendor_gstin", "27AAACT2727Q1ZW"),
        hsn_code=extracted.get("hsn_code", "998313"),
        taxable_value=taxable,
        cgst=cgst,
        sgst=sgst,
        igst=igst,
        cess=cess,
        total_amount=total,
        raw_extracted_data=extracted,
        roi_minutes_saved=30
    )
    db.add(invoice)
    await db.commit()
    await db.refresh(message)
    await db.refresh(invoice)

    # Reload with client
    c_stmt = select(InvoiceLedger).options(selectinload(InvoiceLedger.client)).where(InvoiceLedger.id == invoice.id)
    inv_res = await db.execute(c_stmt)
    invoice = inv_res.scalar_one()

    await record_audit(
        db, client.organization_id,
        f"WhatsApp Bot ingested & extracted invoice {invoice.invoice_number} for {client.trade_name or client.legal_name}",
        user, "INVOICE", invoice.id
    )

    return {
        "status": "created",
        "message": whatsapp_msg_to_dict(message),
        "invoice": invoice_to_dict(invoice),
    }


@router.get("/api/v1/webhooks/whatsapp")
@router.get("/api/v1/webhooks/whatsapp/")
async def whatsapp_webhook_verify(request: Request):
    mode = request.query_params.get("hub.mode")
    verify_token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        return Response(content=challenge or "", media_type="text/plain")
    raise HTTPException(status_code=403, detail="Webhook verification failed")


@router.post("/api/v1/webhooks/whatsapp")
@router.post("/api/v1/webhooks/whatsapp/")
async def whatsapp_webhook_event(request: Request, db: AsyncSession = Depends(get_db)):
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    if not verify_meta_signature(raw_body, signature, settings.WHATSAPP_APP_SECRET):
        raise HTTPException(status_code=403, detail="Invalid Meta webhook signature")

    payload = await request.json()
    events = extract_messages_from_webhook(payload)
    created = []

    for event in events:
        variants = list(phone_variants(event["sender_phone"]))
        c_res = await db.execute(
            select(Client).where(Client.phone_number.in_(variants), Client.is_active == True)
        )
        client = c_res.scalar_one_or_none()
        default_org = await get_or_create_default_org(db)
        org_id = client.organization_id if client else default_org.id
        status_value = "RECEIVED" if client else "IGNORED"

        # Check existing message ID
        existing = await db.execute(
            select(WhatsAppInboundMessage).where(WhatsAppInboundMessage.whatsapp_message_id == event["message_id"])
        )
        if existing.scalar_one_or_none():
            continue

        msg = WhatsAppInboundMessage(
            organization_id=org_id,
            client_id=client.id if client else None,
            whatsapp_message_id=event["message_id"],
            sender_phone=event["sender_phone"],
            message_type=event["message_type"],
            text_body=event["text_body"],
            media_id=event["media_id"],
            media_mime_type=event["media_mime_type"],
            processing_status=status_value,
            raw_payload=event,
        )
        db.add(msg)
        await db.commit()
        await db.refresh(msg)
        created.append({"message_id": str(msg.id), "status": msg.processing_status})

    return {"status": "received", "events": created}
