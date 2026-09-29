import logging
import json
from decimal import Decimal
import difflib
from celery import shared_task
from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.conf import settings

from .models import Client, InvoiceLedger, LegalNoticeTracker
from .services.ocr_engine import InvoiceOCREngine
from .services.gsp_client import GSPClient
from .services.legal_ai import LegalAIDrafter

logger = logging.getLogger(__name__)

ocr_engine = InvoiceOCREngine()
legal_drafter = LegalAIDrafter()


@shared_task(bind=True, max_retries=3)
def process_whatsapp_media_inbound(self, media_id: str, sender_phone: str):
    """
    Handles inbound WhatsApp invoice images:
    1. Authenticate sender -> Client -> Organization
    2. Extract structured GST metadata via InvoiceOCREngine
    3. Save to InvoiceLedger and broadcast via WebSocket
    """
    try:
        client = Client.objects.filter(phone_number=sender_phone, is_active=True).first()
        if not client:
            logger.warning(f"Unrecognized WhatsApp sender: {sender_phone}")
            return None

        organization = client.organization

        # OCR extraction via OCR engine
        extracted = ocr_engine.process_invoice(media_id)

        # Commit to Ledger
        with transaction.atomic():
            invoice = InvoiceLedger.objects.create(
                organization=organization,
                client=client,
                source=InvoiceLedger.Source.WHATSAPP,
                processing_status=InvoiceLedger.ProcessingStatus.PENDING_REVIEW,
                buyer_gstin=client.gstin,
                
                invoice_number=extracted.get('invoice_number', f"WA-{media_id[:6]}"),
                invoice_date=extracted.get('invoice_date', '2026-06-15'),
                vendor_gstin=extracted.get('vendor_gstin', '27AAACW2345Z1Z1'),
                
                taxable_value=Decimal(str(extracted.get('taxable_value', '0.00'))),
                cgst=Decimal(str(extracted.get('cgst', '0.00'))),
                sgst=Decimal(str(extracted.get('sgst', '0.00'))),
                igst=Decimal(str(extracted.get('igst', '0.00'))),
                cess=Decimal(str(extracted.get('cess', '0.00'))),
                total_amount=Decimal(str(extracted.get('total_amount', '0.00'))),
                
                raw_extracted_data=extracted
            )

        # Broadcast via Django Channels
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"org_{organization.id}_dashboard",
                    {
                        "type": "invoice.extracted",
                        "invoice_id": str(invoice.id),
                        "status": invoice.processing_status,
                        "message": f"New invoice {invoice.invoice_number} extracted"
                    }
                )
        except Exception as ws_err:
            logger.warning(f"WebSocket broadcast skipped or failed: {ws_err}")

        return str(invoice.id)

    except Exception as exc:
        logger.error(f"Error processing WhatsApp media {media_id}: {exc}")
        raise self.retry(exc=exc, countdown=10)


@shared_task
def reconcile_books_vs_gstr2b(client_id: str, tax_period: str):
    """
    Reconciles PR (Purchase Register) against GSTR-2B using GSPClient.
    """
    try:
        client = Client.objects.get(id=client_id)
        gsp = GSPClient(gstin=client.gstin)
        gstr2b_data = gsp.fetch_gstr2b(tax_period)

        portal_invoices = []
        for b2b in gstr2b_data.get('b2b', []):
            vendor_gstin = b2b.get('ctin')
            for inv in b2b.get('inv', []):
                portal_invoices.append({
                    'invoice_number': inv.get('inum'),
                    'vendor_gstin': vendor_gstin,
                    'taxable_value': Decimal(str(inv.get('val', '0.00'))),
                    'itc_available': inv.get('itcavl', 'Y') == 'Y'
                })

        books_invoices = InvoiceLedger.objects.filter(
            client=client, 
            processing_status=InvoiceLedger.ProcessingStatus.APPROVED
        )

        matched_count = 0
        mismatched_count = 0
        missing_count = 0

        with transaction.atomic():
            for book_inv in books_invoices:
                best_match = None
                best_ratio = 0.0

                for p_inv in portal_invoices:
                    if p_inv['vendor_gstin'] != book_inv.vendor_gstin:
                        continue

                    ratio = difflib.SequenceMatcher(
                        None, 
                        str(p_inv['invoice_number']).upper().replace("/", "").replace("-", ""),
                        str(book_inv.invoice_number).upper().replace("/", "").replace("-", "")
                    ).ratio()

                    if ratio > 0.80 and ratio > best_ratio:
                        best_match = p_inv
                        best_ratio = ratio

                if best_match:
                    diff = abs(book_inv.taxable_value - best_match['taxable_value'])
                    if diff <= Decimal("2.00"):
                        book_inv.matching_status = InvoiceLedger.MatchingStatus.MATCHED
                        matched_count += 1
                    else:
                        book_inv.matching_status = InvoiceLedger.MatchingStatus.MISMATCHED
                        mismatched_count += 1
                else:
                    book_inv.matching_status = InvoiceLedger.MatchingStatus.MISSING_IN_PORTAL
                    missing_count += 1

                book_inv.save(update_fields=['matching_status'])

        return {
            "client": client.trade_name,
            "period": tax_period,
            "matched": matched_count,
            "mismatched": mismatched_count,
            "missing_in_portal": missing_count
        }

    except Exception as exc:
        logger.error(f"Reconciliation error for client {client_id}: {exc}")
        raise exc


@shared_task
def generate_asmt11_reply_draft(notice_id: str):
    """
    Generates a formal legal reply to GST Notice using LegalAIDrafter.
    """
    try:
        notice = LegalNoticeTracker.objects.get(id=notice_id)
        
        facts = {
            "client_name": notice.client.trade_name,
            "gstin": notice.client.gstin,
            "context": f"Discrepancy notice under sections {', '.join(notice.cited_sections or [])}",
            "alleged_penalty": str(notice.alleged_penalty)
        }

        result = legal_drafter.generate_notice_reply(
            notice_type=notice.notice_type,
            section="73",
            tax_period="FY 2024-25",
            demand_amount=float(notice.disputed_tax_value),
            facts=facts
        )

        notice.generated_asmt11_draft = result["reply_draft"]
        notice.status = LegalNoticeTracker.Status.DRAFT_GENERATED
        notice.save(update_fields=['generated_asmt11_draft', 'status'])
        
        return f"Legal draft completed for notice {notice_id}"

    except Exception as exc:
        logger.error(f"Error generating ASMT-11 draft for {notice_id}: {exc}")
        raise exc
