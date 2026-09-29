from rest_framework import serializers
from .models import (
    ConnectorConfig,
    InvoiceLedger,
    Client,
    LegalNoticeTracker,
    Organization,
    WhatsAppInboundMessage,
    ComplianceTask,
    AuditLog,
    Task,
    Document,
    AiProcessingLog,
)

class ClientSerializer(serializers.ModelSerializer):
    """
    Returns client metadata, including computed counters for active mismatches and legal notices.
    """
    active_mismatches_count = serializers.SerializerMethodField()
    active_notices_count = serializers.SerializerMethodField()
    total_invoices_count = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = [
            'id', 'legal_name', 'trade_name', 'gstin', 'pan', 'email', 'phone_number',
            'address', 'assigned_ca', 'compliance_status', 'is_active', 'notes',
            'active_mismatches_count', 'active_notices_count', 'total_invoices_count',
            'created_at', 'updated_at'
        ]

    def get_active_mismatches_count(self, obj):
        return obj.invoices.filter(
            matching_status__in=[
                InvoiceLedger.MatchingStatus.MISMATCHED, 
                InvoiceLedger.MatchingStatus.MISSING_IN_PORTAL
            ]
        ).count()

    def get_active_notices_count(self, obj):
        return obj.legalnoticetracker_set.filter(is_resolved=False).count()

    def get_total_invoices_count(self, obj):
        return obj.invoices.count()


class InvoiceLedgerSerializer(serializers.ModelSerializer):
    """
    Maps out the exact tax breakdown values, explainability findings, and vendor chaser status.
    """
    client_name = serializers.CharField(source='client.trade_name', read_only=True)
    formatted_date = serializers.SerializerMethodField()

    class Meta:
        model = InvoiceLedger
        fields = [
            'id', 'client', 'client_name', 'invoice_number', 'invoice_date', 'formatted_date',
            'vendor_name', 'vendor_gstin', 'buyer_gstin', 'hsn_code',
            'taxable_value', 'cgst', 'sgst', 'igst', 'cess', 'total_amount',
            'portal_taxable_value', 'portal_tax_amount',
            'ai_finding', 'ai_reason', 'ai_confidence', 'ai_recommended_action',
            'vendor_chaser_status', 'vendor_chaser_message', 'chaser_history', 'roi_minutes_saved',
            'source', 'processing_status', 'matching_status', 'raw_extracted_data',
            'created_at', 'updated_at'
        ]

    def get_formatted_date(self, obj):
        if obj.invoice_date:
            return obj.invoice_date.strftime("%d %b %Y")
        return ""


class ComplianceTaskSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.trade_name', read_only=True, allow_null=True)

    class Meta:
        model = ComplianceTask
        fields = [
            'id', 'client', 'client_name', 'title', 'description', 'compliance_type',
            'due_date', 'status', 'penalty_per_day', 'applicable_to', 'assigned_to',
            'completed_at', 'created_at'
        ]


class LegalNoticeTrackerSerializer(serializers.ModelSerializer):
    """
    Exposes notice metadata and the Gemini AI-drafted responses (ASMT-11).
    """
    client_name = serializers.CharField(source='client.trade_name', read_only=True)
    client_gstin = serializers.CharField(source='client.gstin', read_only=True)

    class Meta:
        model = LegalNoticeTracker
        fields = [
            'id', 'client', 'client_name', 'client_gstin', 'notice_type', 'notice_reference',
            'issue_date', 'deadline_date', 'cited_sections', 'disputed_tax_value', 
            'raw_notice_text', 'ai_summary', 'ai_recommendation', 'generated_asmt11_draft',
            'is_resolved', 'created_at', 'updated_at'
        ]


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True, default='System AI')
    formatted_time = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'id', 'timestamp', 'formatted_time', 'user_name', 'action',
            'entity_type', 'entity_id', 'post_change_payload'
        ]

    def get_formatted_time(self, obj):
        return obj.timestamp.strftime("%d %b %I:%M %p")


class TaskSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.trade_name', read_only=True, allow_null=True)
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True, allow_null=True)

    class Meta:
        model = Task
        fields = [
            'id', 'client', 'client_name', 'invoice', 'invoice_number',
            'title', 'description', 'priority', 'status', 'source',
            'assigned_to', 'due_date', 'completed_at', 'activity_history',
            'created_at', 'updated_at'
        ]


class DocumentSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.trade_name', read_only=True, allow_null=True)
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True, allow_null=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id', 'client', 'client_name', 'invoice', 'invoice_number',
            'document_type', 'original_filename', 'file', 'file_url',
            'file_size', 'mime_type', 'storage_backend', 'is_processed',
            'processing_status', 'created_at', 'updated_at'
        ]

    def get_file_url(self, obj):
        if obj.file and hasattr(obj.file, 'url'):
            return obj.file.url
        return None


class AiProcessingLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiProcessingLog
        fields = [
            'id', 'organization', 'model', 'operation', 'prompt_tokens',
            'completion_tokens', 'total_tokens', 'cost_usd', 'cached',
            'success', 'error_message', 'duration_ms', 'response_summary',
            'created_at'
        ]


class ConnectorConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConnectorConfig
        fields = [
            'id', 'connector_type', 'display_name', 'is_enabled', 'status',
            'config', 'last_error', 'last_checked_at', 'created_at', 'updated_at'
        ]


class WhatsAppInboundMessageSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.trade_name', read_only=True)

    class Meta:
        model = WhatsAppInboundMessage
        fields = [
            'id', 'client_name', 'direction', 'processing_status',
            'whatsapp_message_id', 'sender_phone', 'message_type', 'text_body',
            'media_id', 'media_mime_type', 'error_message', 'created_at'
        ]
