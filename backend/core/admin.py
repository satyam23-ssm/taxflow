from django.contrib import admin
from .models import (
    Organization,
    User,
    Client,
    InvoiceLedger,
    ComplianceTask,
    LegalNoticeTracker,
    ConnectorConfig,
    WhatsAppInboundMessage,
    AuditLog,
    Task,
    Document,
    AiProcessingLog,
)

admin.site.register(Organization)
admin.site.register(User)
admin.site.register(Client)
admin.site.register(InvoiceLedger)
admin.site.register(ComplianceTask)
admin.site.register(LegalNoticeTracker)
admin.site.register(ConnectorConfig)
admin.site.register(WhatsAppInboundMessage)
admin.site.register(AuditLog)
admin.site.register(Task)
admin.site.register(Document)
admin.site.register(AiProcessingLog)