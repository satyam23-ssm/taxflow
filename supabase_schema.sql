-- ============================================================================
-- TaxFlow AI — Complete Supabase (PostgreSQL) Database Schema
-- Paste this entire file into: Supabase Dashboard -> SQL Editor -> New Query -> Run
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Organization
CREATE TABLE IF NOT EXISTS public.organization (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name VARCHAR(255) NOT NULL,
    subscription_tier VARCHAR(50) DEFAULT 'CA_FIRM',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. User (CA Partners, Staff Accountants, Article Clerks)
CREATE TABLE IF NOT EXISTS public."user" (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    first_name VARCHAR(150) DEFAULT '',
    last_name VARCHAR(150) DEFAULT '',
    role VARCHAR(50) DEFAULT 'CA_FIRM_PARTNER',
    designation VARCHAR(100) DEFAULT 'Chartered Accountant',
    work_status VARCHAR(30) DEFAULT 'WORKING',
    phone_number VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    is_staff BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    organization_id VARCHAR(36) REFERENCES public.organization(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_user_username ON public."user"(username);
CREATE INDEX IF NOT EXISTS ix_user_email ON public."user"(email);
CREATE INDEX IF NOT EXISTS ix_user_phone ON public."user"(phone_number);

-- 3. Client (SME & Corporate GSTIN Profiles)
CREATE TABLE IF NOT EXISTS public.client (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    organization_id VARCHAR(36) NOT NULL REFERENCES public.organization(id) ON DELETE CASCADE,
    legal_name VARCHAR(255) NOT NULL,
    trade_name VARCHAR(255),
    gstin VARCHAR(15) NOT NULL,
    pan VARCHAR(10),
    email VARCHAR(254),
    phone_number VARCHAR(20) NOT NULL,
    address TEXT,
    assigned_ca VARCHAR(100) DEFAULT 'CA Rajesh Kumar',
    compliance_status VARCHAR(30) DEFAULT 'COMPLIANT',
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_client_gstin ON public.client(gstin);
CREATE INDEX IF NOT EXISTS ix_client_phone ON public.client(phone_number);
CREATE INDEX IF NOT EXISTS ix_client_status ON public.client(compliance_status);

-- 4. Invoice Ledger (Purchase Register, OCR & GSTR-2B Reconciliation)
CREATE TABLE IF NOT EXISTS public.invoice_ledger (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    organization_id VARCHAR(36) NOT NULL REFERENCES public.organization(id) ON DELETE CASCADE,
    client_id VARCHAR(36) NOT NULL REFERENCES public.client(id) ON DELETE CASCADE,

    invoice_number VARCHAR(100) NOT NULL,
    invoice_date DATE NOT NULL,
    vendor_name VARCHAR(255),
    vendor_gstin VARCHAR(15) NOT NULL,
    buyer_gstin VARCHAR(15) NOT NULL,
    hsn_code VARCHAR(20),

    taxable_value NUMERIC(15, 2) DEFAULT 0,
    cgst NUMERIC(15, 2) DEFAULT 0,
    sgst NUMERIC(15, 2) DEFAULT 0,
    igst NUMERIC(15, 2) DEFAULT 0,
    cess NUMERIC(15, 2) DEFAULT 0,
    total_amount NUMERIC(15, 2) DEFAULT 0,

    portal_taxable_value NUMERIC(15, 2),
    portal_tax_amount NUMERIC(15, 2),

    ai_finding VARCHAR(255),
    ai_reason TEXT,
    ai_confidence DOUBLE PRECISION DEFAULT 0.98,
    ai_recommended_action VARCHAR(255),

    vendor_chaser_status VARCHAR(30) DEFAULT 'NOT_CHASED',
    vendor_chaser_message TEXT,
    chaser_history JSONB DEFAULT '[]'::jsonb,

    roi_minutes_saved INTEGER DEFAULT 30,

    source VARCHAR(20) DEFAULT 'MANUAL',
    processing_status VARCHAR(20) DEFAULT 'QUEUED',
    matching_status VARCHAR(30),

    raw_extracted_data JSONB,
    document_file VARCHAR(500),
    document_original_filename VARCHAR(255),
    tax_period VARCHAR(6),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_invoice_number ON public.invoice_ledger(invoice_number);
CREATE INDEX IF NOT EXISTS ix_invoice_date ON public.invoice_ledger(invoice_date);
CREATE INDEX IF NOT EXISTS ix_invoice_vendor_gstin ON public.invoice_ledger(vendor_gstin);
CREATE INDEX IF NOT EXISTS ix_invoice_buyer_gstin ON public.invoice_ledger(buyer_gstin);
CREATE INDEX IF NOT EXISTS ix_invoice_org_client_date ON public.invoice_ledger(organization_id, client_id, invoice_date);

-- 5. Compliance Task (Statutory Calendar: GSTR-1, GSTR-3B, PMT-06)
CREATE TABLE IF NOT EXISTS public.compliance_task (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    organization_id VARCHAR(36) NOT NULL REFERENCES public.organization(id) ON DELETE CASCADE,
    client_id VARCHAR(36) REFERENCES public.client(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    compliance_type VARCHAR(50) DEFAULT 'GSTR-3B',
    due_date DATE NOT NULL,
    status VARCHAR(30) DEFAULT 'UPCOMING',
    penalty_per_day INTEGER DEFAULT 50,
    applicable_to VARCHAR(255) DEFAULT 'All Regular GST Taxpayers',
    assigned_to VARCHAR(100) DEFAULT 'CA Rajesh Kumar',
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_compliance_due_date ON public.compliance_task(due_date);
CREATE INDEX IF NOT EXISTS ix_compliance_status ON public.compliance_task(status);

-- 6. Legal Notice Tracker (ASMT-10, DRC-01, DRC-01A, ADT-01)
CREATE TABLE IF NOT EXISTS public.legal_notice_tracker (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    organization_id VARCHAR(36) NOT NULL REFERENCES public.organization(id) ON DELETE CASCADE,
    client_id VARCHAR(36) NOT NULL REFERENCES public.client(id) ON DELETE CASCADE,
    notice_type VARCHAR(50) NOT NULL,
    notice_reference VARCHAR(100) NOT NULL,
    issue_date DATE NOT NULL,
    deadline_date DATE NOT NULL,
    cited_sections JSONB DEFAULT '[]'::jsonb,
    disputed_tax_value NUMERIC(15, 2) DEFAULT 0,
    raw_notice_text TEXT,
    ai_summary TEXT,
    ai_recommendation TEXT,
    generated_asmt11_draft TEXT,
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_notice_type ON public.legal_notice_tracker(notice_type);
CREATE INDEX IF NOT EXISTS ix_notice_deadline ON public.legal_notice_tracker(deadline_date);

-- 7. WhatsApp Inbound Message
CREATE TABLE IF NOT EXISTS public.whatsapp_inbound_message (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    organization_id VARCHAR(36) REFERENCES public.organization(id) ON DELETE SET NULL,
    client_id VARCHAR(36) REFERENCES public.client(id) ON DELETE SET NULL,
    direction VARCHAR(20) DEFAULT 'INBOUND',
    processing_status VARCHAR(20) DEFAULT 'RECEIVED',
    whatsapp_message_id VARCHAR(120) UNIQUE,
    sender_phone VARCHAR(20) NOT NULL,
    message_type VARCHAR(30) DEFAULT '',
    text_body TEXT DEFAULT '',
    media_id VARCHAR(120) DEFAULT '',
    media_mime_type VARCHAR(120) DEFAULT '',
    raw_payload JSONB DEFAULT '{}'::jsonb,
    error_message TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_wa_sender_phone ON public.whatsapp_inbound_message(sender_phone);

-- 8. Audit Log
CREATE TABLE IF NOT EXISTS public.audit_log (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    user_id VARCHAR(36) REFERENCES public."user"(id) ON DELETE SET NULL,
    organization_id VARCHAR(36) NOT NULL REFERENCES public.organization(id) ON DELETE CASCADE,
    action VARCHAR(255) NOT NULL,
    entity_type VARCHAR(100) DEFAULT 'SYSTEM',
    entity_id VARCHAR(100),
    ip_address VARCHAR(45),
    pre_change_payload JSONB,
    post_change_payload JSONB
);
CREATE INDEX IF NOT EXISTS ix_audit_timestamp ON public.audit_log(timestamp);

-- 9. Task (Team Command Center & Employee Workdesk)
CREATE TABLE IF NOT EXISTS public.task (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    organization_id VARCHAR(36) NOT NULL REFERENCES public.organization(id) ON DELETE CASCADE,
    client_id VARCHAR(36) REFERENCES public.client(id) ON DELETE SET NULL,
    invoice_id VARCHAR(36) REFERENCES public.invoice_ledger(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    priority VARCHAR(20) DEFAULT 'MEDIUM',
    status VARCHAR(20) DEFAULT 'OPEN',
    source VARCHAR(20) DEFAULT 'MANUAL',
    assigned_user_id VARCHAR(36) REFERENCES public."user"(id) ON DELETE SET NULL,
    assigned_to VARCHAR(100) DEFAULT 'CA Rajesh Kumar',
    due_date DATE,
    completed_at TIMESTAMPTZ,
    activity_history JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_task_status ON public.task(status);
CREATE INDEX IF NOT EXISTS ix_task_priority ON public.task(priority);

-- 10. Document (Uploaded Invoices & Notices Metadata)
CREATE TABLE IF NOT EXISTS public.document (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    organization_id VARCHAR(36) NOT NULL REFERENCES public.organization(id) ON DELETE CASCADE,
    client_id VARCHAR(36) REFERENCES public.client(id) ON DELETE SET NULL,
    invoice_id VARCHAR(36) REFERENCES public.invoice_ledger(id) ON DELETE SET NULL,
    document_type VARCHAR(20) DEFAULT 'INVOICE',
    original_filename VARCHAR(255) NOT NULL,
    file VARCHAR(500),
    file_size BIGINT DEFAULT 0,
    mime_type VARCHAR(120) DEFAULT '',
    storage_backend VARCHAR(40) DEFAULT 'supabase',
    is_processed BOOLEAN DEFAULT FALSE,
    processing_status VARCHAR(20) DEFAULT 'QUEUED',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 11. AI Processing Log
CREATE TABLE IF NOT EXISTS public.ai_processing_log (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    organization_id VARCHAR(36) REFERENCES public.organization(id) ON DELETE SET NULL,
    model VARCHAR(80) DEFAULT 'gemini-1.5-flash',
    operation VARCHAR(80) NOT NULL,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    cost_usd NUMERIC(10, 6) DEFAULT 0,
    cached BOOLEAN DEFAULT FALSE,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT DEFAULT '',
    duration_ms INTEGER DEFAULT 0,
    request_payload JSONB,
    response_summary TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Optional: Create Supabase Storage Bucket for Invoice PDFs & Images
INSERT INTO storage.buckets (id, name, public)
VALUES ('taxflow-invoices', 'taxflow-invoices', false)
ON CONFLICT (id) DO NOTHING;

