from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from .views import (
    ClientViewSet,
    ConnectorViewSet,
    InvoiceLedgerViewSet,
    ReconciliationViewSet,
    VendorChaserViewSet,
    LegalNoticeViewSet,
    ComplianceTaskViewSet,
    TaskViewSet,
    DocumentViewSet,
    AuditLogViewSet,
    GlobalSearchView,
    WhatsAppWebhookView,
)
from .auth_views import RegisterView, LoginView, CurrentUserProfileView
from .report_views import (
    InvoiceUploadOCRView,
    AnalyticsSummaryView,
    ComplianceCalendarView,
    ReportsSummaryView,
    SeedDemoDataView,
)

router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'invoices', InvoiceLedgerViewSet, basename='invoice')
router.register(r'notices', LegalNoticeViewSet, basename='notice')
router.register(r'reconciliation', ReconciliationViewSet, basename='reconciliation')
router.register(r'chaser', VendorChaserViewSet, basename='chaser')
router.register(r'compliance-tasks', ComplianceTaskViewSet, basename='compliance-task')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')
router.register(r'connectors', ConnectorViewSet, basename='connector')

urlpatterns = [
    # Auth endpoints
    path('api/v1/auth/register/', RegisterView.as_view(), name='auth-register'),
    path('api/v1/auth/login/', LoginView.as_view(), name='auth-login'),
    path('api/v1/auth/me/', CurrentUserProfileView.as_view(), name='auth-me'),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('api/v1/auth/token/verify/', TokenVerifyView.as_view(), name='token-verify'),

    # Advanced TaxFlow Features
    path('api/v1/invoices/upload-ocr/', InvoiceUploadOCRView.as_view(), name='invoice-upload-ocr'),
    path('api/v1/analytics/summary/', AnalyticsSummaryView.as_view(), name='analytics-summary'),
    path('api/v1/compliance/calendar/', ComplianceCalendarView.as_view(), name='compliance-calendar'),
    path('api/v1/reports/summary/', ReportsSummaryView.as_view(), name='reports-summary'),
    path('api/v1/system/seed-demo-data/', SeedDemoDataView.as_view(), name='seed-demo-data'),
    path('api/v1/search/', GlobalSearchView.as_view(), name='global-search'),

    # Core REST ViewSets
    path('api/v1/', include(router.urls)),
    path('api/v1/webhooks/whatsapp/', WhatsAppWebhookView.as_view(), name='whatsapp-webhook'),
]
