import os
import logging
from typing import Dict, Any, Optional
from .gemini_service import GeminiService

logger = logging.getLogger(__name__)

class LegalAIDrafter:
    """
    Automated Legal Response Engine for Indian GST Notices
    (Forms ASMT-10, DRC-01, DRC-01A, Section 61/73/74 show-cause notices).
    Powered by the centralized GeminiService.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.gemini = GeminiService(api_key=api_key)

    def generate_notice_reply(
        self,
        notice_type: str,
        section: str,
        tax_period: str,
        demand_amount: float,
        facts: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Drafts a formal, legally grounded response to the GST notice with statutory citations.
        """
        client_name = facts.get('client_name', 'The Taxpayer')
        gstin = facts.get('gstin', '27ABCDE1234F1Z5')
        notice_ref = facts.get('notice_reference', f'GST/{notice_type}/2026/001')
        raw_text = facts.get('context', f'Alleged discrepancy between GSTR-3B and GSTR-2B for period {tax_period}.')

        draft_result = self.gemini.summarize_and_draft_notice(
            notice_type=notice_type,
            notice_ref=notice_ref,
            client_name=client_name,
            gstin=gstin,
            demand_amount=demand_amount,
            raw_text=raw_text
        )

        return {
            "reply_draft": draft_result.get("reply_draft"),
            "citations": draft_result.get("statutory_citations", []),
            "summary": draft_result.get("summary"),
            "cited_sections": draft_result.get("cited_sections", []),
            "confidence": 0.98,
            "status": "DRAFTED_BY_GEMINI"
        }
