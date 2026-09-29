import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float, Date, DateTime,
    ForeignKey, Index, UniqueConstraint, Numeric, JSON, BigInteger
)
from sqlalchemy.orm import relationship
from .database import Base


def gen_uuid():
    return str(uuid.uuid4())


# ─── Organization ──────────────────────────────────────
class Organization(Base):
    __tablename__ = "organization"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    subscription_tier = Column(String(50), default="CA_FIRM")  # SOLO_CA, CA_FIRM, ENTERPRISE
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = relationship("User", back_populates="organization")
    clients = relationship("Client", back_populates="organization")
    invoices = relationship("InvoiceLedger", back_populates="organization")
    compliance_tasks = relationship("ComplianceTask", back_populates="organization")
    audit_logs = relationship("AuditLog", back_populates="organization")
    whatsapp_messages = relationship("WhatsAppInboundMessage", back_populates="organization")
    documents = relationship("Document", back_populates="organization")
    tasks = relationship("Task", back_populates="organization")


# ─── User ──────────────────────────────────────────────
class User(Base):
    __tablename__ = "user"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    username = Column(String(150), unique=True, nullable=False, index=True)
    email = Column(String(254), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(150), default="")
    last_name = Column(String(150), default="")
    role = Column(String(50), default="CA_FIRM_PARTNER")  # CA_FIRM_PARTNER (Admin), STAFF_ACCOUNTANT, ARTICLE_ASSISTANT
    designation = Column(String(100), default="Chartered Accountant")
    work_status = Column(String(30), default="WORKING")  # WORKING, IN_REVIEW, ON_LEAVE, IDLE
    phone_number = Column(String(20), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    is_staff = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    organization_id = Column(String(36), ForeignKey("organization.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="users")
    assigned_tasks = relationship("Task", back_populates="assigned_user", foreign_keys="[Task.assigned_user_id]")


# ─── Client ──────────────────────────────────────────
class Client(Base):
    __tablename__ = "client"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organization.id"), nullable=False)
    legal_name = Column(String(255), nullable=False)
    trade_name = Column(String(255), nullable=True)
    gstin = Column(String(15), index=True, nullable=False)
    pan = Column(String(10), nullable=True)
    email = Column(String(254), nullable=True)
    phone_number = Column(String(20), index=True, nullable=False)
    address = Column(Text, nullable=True)
    assigned_ca = Column(String(100), default="CA Rajesh Kumar")
    compliance_status = Column(String(30), default="COMPLIANT", index=True)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization", back_populates="clients")
    invoices = relationship("InvoiceLedger", back_populates="client")
    compliance_tasks = relationship("ComplianceTask", back_populates="client")
    notices = relationship("LegalNoticeTracker", back_populates="client")
    whatsapp_messages = relationship("WhatsAppInboundMessage", back_populates="client")
    documents = relationship("Document", back_populates="client")
    tasks = relationship("Task", back_populates="client")


# ─── Invoice Ledger ──────────────────────────────────
class InvoiceLedger(Base):
    __tablename__ = "invoice_ledger"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organization.id"), nullable=False)
    client_id = Column(String(36), ForeignKey("client.id"), nullable=False)

    # Core tax metadata
    invoice_number = Column(String(100), index=True, nullable=False)
    invoice_date = Column(Date, index=True, nullable=False)
    vendor_name = Column(String(255), nullable=True)
    vendor_gstin = Column(String(15), index=True, nullable=False)
    buyer_gstin = Column(String(15), index=True, nullable=False)
    hsn_code = Column(String(20), nullable=True)

    # Books financial amounts
    taxable_value = Column(Numeric(15, 2), default=0)
    cgst = Column(Numeric(15, 2), default=0)
    sgst = Column(Numeric(15, 2), default=0)
    igst = Column(Numeric(15, 2), default=0)
    cess = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), default=0)

    # GSTR-2B comparison
    portal_taxable_value = Column(Numeric(15, 2), nullable=True)
    portal_tax_amount = Column(Numeric(15, 2), nullable=True)

    # AI explainability
    ai_finding = Column(String(255), nullable=True)
    ai_reason = Column(Text, nullable=True)
    ai_confidence = Column(Float, default=0.98)
    ai_recommended_action = Column(String(255), nullable=True)

    # Vendor Chaser
    vendor_chaser_status = Column(String(30), default="NOT_CHASED", index=True)
    vendor_chaser_message = Column(Text, nullable=True)
    chaser_history = Column(JSON, default=list)

    # ROI
    roi_minutes_saved = Column(Integer, default=30)

    # Status tracking
    source = Column(String(20), default="MANUAL")
    processing_status = Column(String(20), default="QUEUED", index=True)
    matching_status = Column(String(30), nullable=True, index=True)

    # Raw data
    raw_extracted_data = Column(JSON, nullable=True)

    # Document
    document_file = Column(String(500), nullable=True)
    document_original_filename = Column(String(255), nullable=True)
    tax_period = Column(String(6), nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization", back_populates="invoices")
    client = relationship("Client", back_populates="invoices")
    documents = relationship("Document", back_populates="invoice")
    tasks = relationship("Task", back_populates="invoice")

    __table_args__ = (
        Index("ix_invoice_org_client_date", "organization_id", "client_id", "invoice_date"),
    )


# ─── Compliance Task ─────────────────────────────────
class ComplianceTask(Base):
    __tablename__ = "compliance_task"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organization.id"), nullable=False)
    client_id = Column(String(36), ForeignKey("client.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    compliance_type = Column(String(50), default="GSTR-3B")
    due_date = Column(Date, index=True, nullable=False)
    status = Column(String(30), default="UPCOMING", index=True)
    penalty_per_day = Column(Integer, default=50)
    applicable_to = Column(String(255), default="All Regular GST Taxpayers")
    assigned_to = Column(String(100), default="CA Rajesh Kumar")
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="compliance_tasks")
    client = relationship("Client", back_populates="compliance_tasks")


# ─── Legal Notice Tracker ────────────────────────────
class LegalNoticeTracker(Base):
    __tablename__ = "legal_notice_tracker"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organization.id"), nullable=False)
    client_id = Column(String(36), ForeignKey("client.id"), nullable=False)

    notice_type = Column(String(50), index=True, nullable=False)
    notice_reference = Column(String(100), index=True, nullable=False)
    issue_date = Column(Date, nullable=False)
    deadline_date = Column(Date, index=True, nullable=False)

    cited_sections = Column(JSON, default=list)
    disputed_tax_value = Column(Numeric(15, 2), default=0)

    raw_notice_text = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    ai_recommendation = Column(Text, nullable=True)
    generated_asmt11_draft = Column(Text, nullable=True)

    is_resolved = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization")
    client = relationship("Client", back_populates="notices")


# ─── WhatsApp Inbound Message ────────────────────────
class WhatsAppInboundMessage(Base):
    __tablename__ = "whatsapp_inbound_message"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organization.id"), nullable=True)
    client_id = Column(String(36), ForeignKey("client.id"), nullable=True)
    direction = Column(String(20), default="INBOUND")
    processing_status = Column(String(20), default="RECEIVED", index=True)
    whatsapp_message_id = Column(String(120), unique=True, nullable=True)
    sender_phone = Column(String(20), index=True, nullable=False)
    message_type = Column(String(30), default="")
    text_body = Column(Text, default="")
    media_id = Column(String(120), default="")
    media_mime_type = Column(String(120), default="")
    raw_payload = Column(JSON, default=dict)
    error_message = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    organization = relationship("Organization", back_populates="whatsapp_messages")
    client = relationship("Client", back_populates="whatsapp_messages")


# ─── Audit Log ───────────────────────────────────────
class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(String(36), ForeignKey("user.id"), nullable=True)
    organization_id = Column(String(36), ForeignKey("organization.id"), nullable=False)
    action = Column(String(255), nullable=False)
    entity_type = Column(String(100), default="SYSTEM")
    entity_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    pre_change_payload = Column(JSON, nullable=True)
    post_change_payload = Column(JSON, nullable=True)

    user = relationship("User")
    organization = relationship("Organization", back_populates="audit_logs")


# ─── Task ────────────────────────────────────────────
class Task(Base):
    __tablename__ = "task"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organization.id"), nullable=False)
    client_id = Column(String(36), ForeignKey("client.id"), nullable=True)
    invoice_id = Column(String(36), ForeignKey("invoice_ledger.id"), nullable=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String(20), default="MEDIUM", index=True)
    status = Column(String(20), default="OPEN", index=True)
    source = Column(String(20), default="MANUAL", index=True)
    assigned_user_id = Column(String(36), ForeignKey("user.id"), nullable=True)
    assigned_to = Column(String(100), default="CA Rajesh Kumar")
    due_date = Column(Date, nullable=True, index=True)
    completed_at = Column(DateTime, nullable=True)
    activity_history = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization", back_populates="tasks")
    client = relationship("Client", back_populates="tasks")
    invoice = relationship("InvoiceLedger", back_populates="tasks")
    assigned_user = relationship("User", back_populates="assigned_tasks", foreign_keys=[assigned_user_id])


# ─── Document ────────────────────────────────────────
class Document(Base):
    __tablename__ = "document"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organization.id"), nullable=False)
    client_id = Column(String(36), ForeignKey("client.id"), nullable=True)
    invoice_id = Column(String(36), ForeignKey("invoice_ledger.id"), nullable=True)

    document_type = Column(String(20), default="INVOICE", index=True)
    original_filename = Column(String(255), nullable=False)
    file = Column(String(500), nullable=True)
    file_size = Column(BigInteger, default=0)
    mime_type = Column(String(120), default="")
    storage_backend = Column(String(40), default="local")
    is_processed = Column(Boolean, default=False, index=True)
    processing_status = Column(String(20), default="QUEUED", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization", back_populates="documents")
    client = relationship("Client", back_populates="documents")
    invoice = relationship("InvoiceLedger", back_populates="documents")


# ─── AI Processing Log ──────────────────────────────
class AiProcessingLog(Base):
    __tablename__ = "ai_processing_log"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organization.id"), nullable=True)
    model = Column(String(80), default="gemini-1.5-flash")
    operation = Column(String(80), index=True, nullable=False)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost_usd = Column(Numeric(10, 6), default=0)
    cached = Column(Boolean, default=False, index=True)
    success = Column(Boolean, default=True, index=True)
    error_message = Column(Text, default="")
    duration_ms = Column(Integer, default=0)
    request_payload = Column(JSON, nullable=True)
    response_summary = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    organization = relationship("Organization")
