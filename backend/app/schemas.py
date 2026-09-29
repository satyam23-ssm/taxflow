from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Any
from pydantic import BaseModel, EmailStr, Field


# ─── Auth Schemas ────────────────────────────────────
class RegisterRequest(BaseModel):
    username: Optional[str] = None
    email: str
    password: str
    first_name: str = ""
    last_name: str = ""

class LoginRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: str

class TokenResponse(BaseModel):
    access: str
    refresh: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    first_name: str
    last_name: str
    is_staff: bool = False

    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    tokens: TokenResponse
    user: UserResponse
    message: str = ""


# ─── Client Schemas ──────────────────────────────────
class ClientCreate(BaseModel):
    legal_name: str
    trade_name: Optional[str] = None
    gstin: str
    pan: Optional[str] = None
    email: Optional[str] = None
    phone_number: str
    address: Optional[str] = None
    assigned_ca: str = "CA Rajesh Kumar"
    compliance_status: str = "COMPLIANT"
    notes: Optional[str] = None

class ClientResponse(BaseModel):
    id: str
    legal_name: str
    trade_name: Optional[str] = None
    gstin: str
    pan: Optional[str] = None
    email: Optional[str] = None
    phone_number: str
    address: Optional[str] = None
    assigned_ca: str = ""
    compliance_status: str = "COMPLIANT"
    is_active: bool = True
    notes: Optional[str] = None
    active_mismatches_count: int = 0
    active_notices_count: int = 0
    total_invoices_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Invoice Schemas ─────────────────────────────────
class InvoiceCreate(BaseModel):
    client: Optional[str] = Field(None, alias="client_id")
    invoice_number: str
    invoice_date: date
    vendor_name: Optional[str] = None
    vendor_gstin: str
    buyer_gstin: str
    hsn_code: Optional[str] = None
    taxable_value: Decimal = Decimal("0")
    cgst: Decimal = Decimal("0")
    sgst: Decimal = Decimal("0")
    igst: Decimal = Decimal("0")
    cess: Decimal = Decimal("0")
    total_amount: Decimal = Decimal("0")
    source: str = "MANUAL"

class InvoiceResponse(BaseModel):
    id: str
    client: Optional[str] = None
    client_name: Optional[str] = None
    invoice_number: str
    invoice_date: Optional[date] = None
    formatted_date: str = ""
    vendor_name: Optional[str] = None
    vendor_gstin: str = ""
    buyer_gstin: str = ""
    hsn_code: Optional[str] = None
    taxable_value: Optional[Decimal] = None
    cgst: Optional[Decimal] = None
    sgst: Optional[Decimal] = None
    igst: Optional[Decimal] = None
    cess: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    portal_taxable_value: Optional[Decimal] = None
    portal_tax_amount: Optional[Decimal] = None
    ai_finding: Optional[str] = None
    ai_reason: Optional[str] = None
    ai_confidence: float = 0.98
    ai_recommended_action: Optional[str] = None
    vendor_chaser_status: str = "NOT_CHASED"
    vendor_chaser_message: Optional[str] = None
    chaser_history: Optional[list] = None
    roi_minutes_saved: int = 30
    source: str = "MANUAL"
    processing_status: str = "QUEUED"
    matching_status: Optional[str] = None
    raw_extracted_data: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Compliance Task Schemas ─────────────────────────
class ComplianceTaskCreate(BaseModel):
    client: Optional[str] = Field(None, alias="client_id")
    title: str
    description: Optional[str] = None
    compliance_type: str = "GSTR-3B"
    due_date: date
    status: str = "UPCOMING"
    penalty_per_day: int = 50
    applicable_to: str = "All Regular GST Taxpayers"
    assigned_to: str = "CA Rajesh Kumar"

class ComplianceTaskResponse(BaseModel):
    id: str
    client: Optional[str] = None
    client_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    compliance_type: str
    due_date: Optional[date] = None
    status: str
    penalty_per_day: int = 50
    applicable_to: str = ""
    assigned_to: str = ""
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Legal Notice Schemas ────────────────────────────
class NoticeCreate(BaseModel):
    client: str = Field(alias="client_id")
    notice_type: str
    notice_reference: str
    issue_date: date
    deadline_date: date
    cited_sections: list = []
    disputed_tax_value: Decimal = Decimal("0")
    raw_notice_text: Optional[str] = None

class NoticeResponse(BaseModel):
    id: str
    client: Optional[str] = None
    client_name: Optional[str] = None
    client_gstin: Optional[str] = None
    notice_type: str
    notice_reference: str
    issue_date: Optional[date] = None
    deadline_date: Optional[date] = None
    cited_sections: Optional[list] = None
    disputed_tax_value: Optional[Decimal] = None
    raw_notice_text: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_recommendation: Optional[str] = None
    generated_asmt11_draft: Optional[str] = None
    is_resolved: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Audit Log Schemas ───────────────────────────────
class AuditLogResponse(BaseModel):
    id: str
    timestamp: Optional[datetime] = None
    formatted_time: str = ""
    user_name: str = "System AI"
    action: str
    entity_type: str = "SYSTEM"
    entity_id: Optional[str] = None
    post_change_payload: Optional[dict] = None

    class Config:
        from_attributes = True


# ─── Task Schemas ────────────────────────────────────
class TaskCreate(BaseModel):
    client: Optional[str] = Field(None, alias="client_id")
    invoice: Optional[str] = Field(None, alias="invoice_id")
    title: str
    description: Optional[str] = None
    priority: str = "MEDIUM"
    source: str = "MANUAL"
    assigned_to: str = "CA Rajesh Kumar"
    due_date: Optional[date] = None

class TaskResponse(BaseModel):
    id: str
    client: Optional[str] = None
    client_name: Optional[str] = None
    invoice: Optional[str] = None
    invoice_number: Optional[str] = None
    title: str
    description: Optional[str] = None
    priority: str = "MEDIUM"
    status: str = "OPEN"
    source: str = "MANUAL"
    assigned_to: str = ""
    due_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    activity_history: Optional[list] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Document Schemas ────────────────────────────────
class DocumentResponse(BaseModel):
    id: str
    client: Optional[str] = None
    client_name: Optional[str] = None
    invoice: Optional[str] = None
    invoice_number: Optional[str] = None
    document_type: str = "INVOICE"
    original_filename: str = ""
    file: Optional[str] = None
    file_url: Optional[str] = None
    file_size: int = 0
    mime_type: str = ""
    storage_backend: str = "local"
    is_processed: bool = False
    processing_status: str = "QUEUED"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── WhatsApp Schemas ────────────────────────────────
class WhatsAppMessageResponse(BaseModel):
    id: str
    client_name: Optional[str] = None
    direction: str = "INBOUND"
    processing_status: str = "RECEIVED"
    whatsapp_message_id: Optional[str] = None
    sender_phone: str = ""
    message_type: str = ""
    text_body: str = ""
    media_id: str = ""
    media_mime_type: str = ""
    error_message: str = ""
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
