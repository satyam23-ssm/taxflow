import os
import logging
from typing import Dict, Any, Optional
from .gemini_service import GeminiService

logger = logging.getLogger(__name__)

class InvoiceOCREngine:
    """
    Production-ready OCR engine for Indian GST Tax Invoices.
    Powered by the centralized GeminiService with vision & structured output capabilities.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.gemini = GeminiService(api_key=api_key)

    def process_invoice(self, file_path_or_bytes, mime_type: str = "image/jpeg") -> Dict[str, Any]:
        """
        Extract structured GST invoice metadata from an image or PDF using Gemini.
        """
        return self.gemini.extract_invoice(file_path_or_bytes, mime_type=mime_type)
