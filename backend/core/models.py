import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import AbstractUser

class Organization(models.Model):
    class SubscriptionTier(models.TextChoices):
        SOLO_CA = 'SOLO_CA', 'Solo CA'
        CA_FIRM = 'CA_FIRM', 'CA Firm'
        ENTERPRISE = 'ENTERPRISE', 'Enterprise'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    subscription_tier = models.CharField(
        max_length=50, 
        choices=SubscriptionTier.choices, 
        default=SubscriptionTier.CA_FIRM
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class User(AbstractUser):
    class Role(models.TextChoices):
        INDIVIDUAL_CA = 'INDIVIDUAL_CA', 'Individual CA'
        CA_FIRM_PARTNER = 'CA_FIRM_PARTNER', 'CA Firm Partner'
        ENTERPRISE_ADMIN = 'ENTERPRISE_ADMIN', 'Enterprise Admin'
        INTERN = 'INTERN', 'Intern / Staff'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    role = models.CharField(max_length=50, choices=Role.choices, default=Role.CA_FIRM_PARTNER)
    phone_number = models.CharField(max_length=20, blank=True, null=True, db_index=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.email})"

class Client(models.Model):
    class ComplianceStatus(models.TextChoices):
        COMPLIANT = 'COMPLIANT', 'Compliant'
        PENDING_DOCS = 'PENDING_DOCS', 'Pending Documents'
        AT_RISK = 'AT_RISK', 'At Risk'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='clients')
    legal_name = models.CharField(max_length=255)
    trade_name = models.CharField(max_length=255, blank=True, null=True)
    gstin = models.CharField(max_length=15, db_index=True)
    pan = models.CharField(max_length=10, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, db_index=True)
    address = models.TextField(blank=True, null=True)
    assigned_ca = models.CharField(max_length=100, default='CA Rajesh Kumar', blank=True)
    compliance_status = models.CharField(
        max_length=30, 
        choices=ComplianceStatus.choices, 
        default=ComplianceStatus.COMPLIANT,
        db_index=True
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['trade_name', 'legal_name']

    def __str__(self):
        return f"{self.trade_name or self.legal_name} ({self.gstin})"

class InvoiceLedger(models.Model):
    class Source(models.TextChoices):
        WHATSAPP = 'WHATSAPP', 'WhatsApp'
        MANUAL = 'MANUAL', 'Manual'
        MANUAL_UPLOAD = 'MANUAL_UPLOAD', 'OCR Upload'
        ERP = 'ERP', 'ERP'

    class ProcessingStatus(models.TextChoices):
        QUEUED = 'QUEUED', 'Queued'
        PARSED = 'PARSED', 'Parsed'
        PENDING_REVIEW = 'PENDING_REVIEW', 'Pending Review'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    class MatchingStatus(models.TextChoices):
        MATCHED = 'MATCHED', 'Matched'
        MISMATCHED = 'MISMATCHED', 'Mismatched'
        MISSING_IN_PORTAL = 'MISSING_IN_PORTAL', 'Missing in Portal'
        MISSING_IN_BOOKS = 'MISSING_IN_BOOKS', 'Missing in Books'

    class VendorChaserStatus(models.TextChoices):
        NOT_CHASED = 'NOT_CHASED', 'Not Chased'
        CHASE_GENERATED = 'CHASE_GENERATED', 'Chase Generated'
        CHASE_SENT = 'CHASE_SENT', 'Sent via WhatsApp'
        CHASE_SENT_EMAIL = 'CHASE_SENT_EMAIL', 'Sent via Email'
        VENDOR_RESPONDED = 'VENDOR_RESPONDED', 'Vendor Responded'
        RESOLVED = 'RESOLVED', 'Resolved & Recovered'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='invoices')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoices')
    
    # Core tax metadata
    invoice_number = models.CharField(max_length=100, db_index=True)
    invoice_date = models.DateField(db_index=True)
    vendor_name = models.CharField(max_length=255, blank=True, null=True)
    vendor_gstin = models.CharField(max_length=15, db_index=True)
    buyer_gstin = models.CharField(max_length=15, db_index=True)
    hsn_code = models.CharField(max_length=20, blank=True, null=True)
    
    # Books financial amounts
    taxable_value = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    cgst = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    sgst = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    igst = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    cess = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # GSTR-2B comparison values
    portal_taxable_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    portal_tax_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # AI explainability & anomaly detection
    ai_finding = models.CharField(max_length=255, blank=True, null=True)
    ai_reason = models.TextField(blank=True, null=True)
    ai_confidence = models.FloatField(default=0.98)
    ai_recommended_action = models.CharField(max_length=255, blank=True, null=True)
    
    # Vendor Chaser Workflow
    vendor_chaser_status = models.CharField(
        max_length=30, 
        choices=VendorChaserStatus.choices, 
        default=VendorChaserStatus.NOT_CHASED,
        db_index=True
    )
    vendor_chaser_message = models.TextField(blank=True, null=True)
    chaser_history = models.JSONField(default=list, blank=True)

    # ROI Calculation (time saved in minutes)
    roi_minutes_saved = models.IntegerField(default=30)
    
    # Status tracking
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL)
    processing_status = models.CharField(max_length=20, choices=ProcessingStatus.choices, default=ProcessingStatus.QUEUED, db_index=True)
    matching_status = models.CharField(max_length=30, choices=MatchingStatus.choices, null=True, blank=True, db_index=True)
    
    # Raw JSON from OCR/LLM
    raw_extracted_data = models.JSONField(null=True, blank=True)

    # Source document storage
    document_file = models.FileField(upload_to='taxflow/invoices/%Y/%m/', max_length=500, null=True, blank=True)
    document_original_filename = models.CharField(max_length=255, blank=True, null=True)
    tax_period = models.CharField(max_length=6, blank=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-invoice_date', '-created_at']
        indexes = [
            models.Index(fields=['organization', 'client', 'invoice_date']),
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.vendor_name or self.vendor_gstin}"

class ComplianceTask(models.Model):
    class ComplianceType(models.TextChoices):
        GSTR1 = 'GSTR-1', 'GSTR-1 (Outward Supplies)'
        GSTR3B = 'GSTR-3B', 'GSTR-3B (Monthly Return & Payment)'
        IFF = 'IFF', 'IFF (QRMP Invoice Furnishing)'
        CMP08 = 'CMP-08', 'CMP-08 (Composition Challan)'
        PMT06 = 'PMT-06', 'PMT-06 (QRMP Tax Challan)'
        GSTR9 = 'GSTR-9', 'GSTR-9 (Annual Return)'
        ASMT10 = 'ASMT-10', 'ASMT-10 Notice Reply'
        AUDIT = 'AUDIT', 'Statutory Tax Audit'
        CUSTOM = 'CUSTOM', 'Custom Task'

    class TaskStatus(models.TextChoices):
        UPCOMING = 'UPCOMING', 'Upcoming'
        CRITICAL = 'CRITICAL', 'Critical'
        OVERDUE = 'OVERDUE', 'Overdue'
        COMPLETED = 'COMPLETED', 'Completed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='compliance_tasks')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='compliance_tasks', null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    compliance_type = models.CharField(max_length=50, choices=ComplianceType.choices, default=ComplianceType.GSTR3B)
    due_date = models.DateField(db_index=True)
    status = models.CharField(max_length=30, choices=TaskStatus.choices, default=TaskStatus.UPCOMING, db_index=True)
    penalty_per_day = models.IntegerField(default=50)
    applicable_to = models.CharField(max_length=255, default='All Regular GST Taxpayers')
    assigned_to = models.CharField(max_length=100, default='CA Rajesh Kumar', blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['due_date', 'status']

    def __str__(self):
        return f"{self.title} - Due {self.due_date}"

class LegalNoticeTracker(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    
    notice_type = models.CharField(max_length=50, db_index=True) # e.g., ASMT-10, DRC-01, DRC-01A
    notice_reference = models.CharField(max_length=100, db_index=True)
    issue_date = models.DateField()
    deadline_date = models.DateField(db_index=True)
    
    cited_sections = models.JSONField(default=list) # e.g., ["Section 61", "Rule 99"]
    disputed_tax_value = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    raw_notice_text = models.TextField(blank=True, null=True)
    ai_summary = models.TextField(blank=True, null=True)
    ai_recommendation = models.TextField(blank=True, null=True)
    generated_asmt11_draft = models.TextField(blank=True, null=True)
    
    is_resolved = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['deadline_date', '-created_at']

    def __str__(self):
        return f"{self.notice_type} - {self.client.trade_name or self.client.legal_name}"

class ConnectorConfig(models.Model):
    class ConnectorType(models.TextChoices):
        WHATSAPP = 'WHATSAPP', 'WhatsApp Cloud API'
        GSP = 'GSP', 'GSTN/GSP Gateway'
        TALLY = 'TALLY', 'Tally Desktop Agent'

    class ConnectorStatus(models.TextChoices):
        NOT_CONFIGURED = 'NOT_CONFIGURED', 'Not Configured'
        NEEDS_ATTENTION = 'NEEDS_ATTENTION', 'Needs Attention'
        ACTIVE = 'ACTIVE', 'Active'
        ERROR = 'ERROR', 'Error'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='connectors')
    connector_type = models.CharField(max_length=30, choices=ConnectorType.choices, db_index=True)
    display_name = models.CharField(max_length=120)
    is_enabled = models.BooleanField(default=True)
    status = models.CharField(
        max_length=30,
        choices=ConnectorStatus.choices,
        default=ConnectorStatus.NOT_CONFIGURED,
        db_index=True
    )
    config = models.JSONField(default=dict, blank=True)
    last_error = models.TextField(blank=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'connector_type'],
                name='uniq_connector_per_org'
            )
        ]

    def __str__(self):
        return f"{self.organization.name} - {self.display_name}"

class WhatsAppInboundMessage(models.Model):
    class Direction(models.TextChoices):
        INBOUND = 'INBOUND', 'Inbound'
        OUTBOUND = 'OUTBOUND', 'Outbound'

    class ProcessingStatus(models.TextChoices):
        RECEIVED = 'RECEIVED', 'Received'
        QUEUED = 'QUEUED', 'Queued'
        PROCESSED = 'PROCESSED', 'Processed'
        IGNORED = 'IGNORED', 'Ignored'
        FAILED = 'FAILED', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='whatsapp_messages',
        null=True,
        blank=True
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        related_name='whatsapp_messages',
        null=True,
        blank=True
    )
    direction = models.CharField(max_length=20, choices=Direction.choices, default=Direction.INBOUND)
    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.RECEIVED,
        db_index=True
    )
    whatsapp_message_id = models.CharField(max_length=120, unique=True, null=True, blank=True)
    sender_phone = models.CharField(max_length=20, db_index=True)
    message_type = models.CharField(max_length=30, blank=True)
    text_body = models.TextField(blank=True)
    media_id = models.CharField(max_length=120, blank=True)
    media_mime_type = models.CharField(max_length=120, blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sender_phone} - {self.message_type or 'message'}"

class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, db_index=True)
    action = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=100, blank=True, default='SYSTEM')
    entity_id = models.CharField(max_length=100, blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    pre_change_payload = models.JSONField(null=True, blank=True)
    post_change_payload = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} at {self.timestamp}"


class Task(models.Model):
    """
    General task management: work items created by CA, by AI suggestion,
    or by automated workflow triggers (e.g. vendor chase, document requests).
    """
    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        URGENT = 'URGENT', 'Urgent'

    class TaskStatus(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    class Source(models.TextChoices):
        MANUAL = 'MANUAL', 'Manual'
        AI_SUGGESTED = 'AI_SUGGESTED', 'AI Suggested'
        WORKFLOW = 'WORKFLOW', 'Workflow'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='tasks')
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, related_name='tasks', null=True, blank=True)
    invoice = models.ForeignKey(InvoiceLedger, on_delete=models.SET_NULL, related_name='tasks', null=True, blank=True)

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM, db_index=True)
    status = models.CharField(max_length=20, choices=TaskStatus.choices, default=TaskStatus.OPEN, db_index=True)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL, db_index=True)
    assigned_to = models.CharField(max_length=100, default='CA Rajesh Kumar', blank=True)
    due_date = models.DateField(db_index=True, null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    activity_history = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', 'due_date', '-created_at']

    def __str__(self):
        return f"{self.title} [{self.priority}]"


class Document(models.Model):
    """
    Stores uploaded invoice images/PDFs with a real file URL and metadata.
    """
    class DocumentType(models.TextChoices):
        INVOICE = 'INVOICE', 'Invoice'
        GSTR2B = 'GSTR_2B', 'GSTR-2B'
        NOTICE = 'NOTICE', 'Legal Notice'
        OTHER = 'OTHER', 'Other'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='documents')
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, related_name='documents', null=True, blank=True)
    invoice = models.ForeignKey(InvoiceLedger, on_delete=models.SET_NULL, related_name='documents', null=True, blank=True)

    document_type = models.CharField(max_length=20, choices=DocumentType.choices, default=DocumentType.INVOICE, db_index=True)
    original_filename = models.CharField(max_length=255)
    file = models.FileField(upload_to='taxflow/documents/%Y/%m/', max_length=500)
    file_size = models.BigIntegerField(default=0)
    mime_type = models.CharField(max_length=120, blank=True)
    storage_backend = models.CharField(max_length=40, default='local', blank=True)
    is_processed = models.BooleanField(default=False, db_index=True)
    processing_status = models.CharField(
        max_length=20,
        choices=InvoiceLedger.ProcessingStatus.choices,
        default=InvoiceLedger.ProcessingStatus.QUEUED,
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.original_filename} ({self.document_type})"


class AiProcessingLog(models.Model):
    """
    Tracks every Gemini/OpenAI API call for cost control, caching, and audit.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='ai_processing_logs', null=True, blank=True)
    model = models.CharField(max_length=80, default='gemini-1.5-flash')
    operation = models.CharField(max_length=80, db_index=True)  # e.g. invoice_extraction, vendor_chaser
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal('0.000000'))
    cached = models.BooleanField(default=False, db_index=True)
    success = models.BooleanField(default=True, db_index=True)
    error_message = models.TextField(blank=True)
    duration_ms = models.IntegerField(default=0)
    request_payload = models.JSONField(null=True, blank=True)
    response_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.operation} ({self.model}) — {self.created_at:%Y-%m-%d %H:%M}"
