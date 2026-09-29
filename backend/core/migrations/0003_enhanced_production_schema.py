# Generated for TaxFlow AI Production MVP Schema

import django.db.models.deletion
import uuid
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_whatsappinboundmessage_connectorconfig'),
    ]

    operations = [
        # Client Enhancements
        migrations.AlterModelOptions(
            name='client',
            options={'ordering': ['trade_name', 'legal_name']},
        ),
        migrations.AddField(
            model_name='client',
            name='address',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='client',
            name='assigned_ca',
            field=models.CharField(blank=True, default='CA Rajesh Kumar', max_length=100),
        ),
        migrations.AddField(
            model_name='client',
            name='compliance_status',
            field=models.CharField(choices=[('COMPLIANT', 'Compliant'), ('PENDING_DOCS', 'Pending Documents'), ('AT_RISK', 'At Risk')], db_index=True, default='COMPLIANT', max_length=30),
        ),
        migrations.AddField(
            model_name='client',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='client',
            name='notes',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='client',
            name='pan',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='client',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),

        # InvoiceLedger Enhancements
        migrations.AlterModelOptions(
            name='invoiceledger',
            options={'ordering': ['-invoice_date', '-created_at']},
        ),
        migrations.AddField(
            model_name='invoiceledger',
            name='vendor_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='invoiceledger',
            name='hsn_code',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='invoiceledger',
            name='portal_taxable_value',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name='invoiceledger',
            name='portal_tax_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name='invoiceledger',
            name='ai_finding',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='invoiceledger',
            name='ai_reason',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='invoiceledger',
            name='ai_confidence',
            field=models.FloatField(default=0.98),
        ),
        migrations.AddField(
            model_name='invoiceledger',
            name='ai_recommended_action',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='invoiceledger',
            name='vendor_chaser_status',
            field=models.CharField(choices=[('NOT_CHASED', 'Not Chased'), ('CHASE_GENERATED', 'Chase Generated'), ('CHASE_SENT', 'Sent via WhatsApp'), ('CHASE_SENT_EMAIL', 'Sent via Email'), ('VENDOR_RESPONDED', 'Vendor Responded'), ('RESOLVED', 'Resolved & Recovered')], db_index=True, default='NOT_CHASED', max_length=30),
        ),
        migrations.AddField(
            model_name='invoiceledger',
            name='vendor_chaser_message',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='invoiceledger',
            name='chaser_history',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='invoiceledger',
            name='roi_minutes_saved',
            field=models.IntegerField(default=30),
        ),
        migrations.AlterField(
            model_name='invoiceledger',
            name='source',
            field=models.CharField(choices=[('WHATSAPP', 'WhatsApp'), ('MANUAL', 'Manual'), ('MANUAL_UPLOAD', 'OCR Upload'), ('ERP', 'ERP')], default='MANUAL', max_length=20),
        ),
        migrations.AlterField(
            model_name='invoiceledger',
            name='processing_status',
            field=models.CharField(choices=[('QUEUED', 'Queued'), ('PARSED', 'Parsed'), ('PENDING_REVIEW', 'Pending Review'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')], db_index=True, default='QUEUED', max_length=20),
        ),

        # LegalNoticeTracker Enhancements
        migrations.AlterModelOptions(
            name='legalnoticetracker',
            options={'ordering': ['deadline_date', '-created_at']},
        ),
        migrations.AddField(
            model_name='legalnoticetracker',
            name='ai_summary',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='legalnoticetracker',
            name='ai_recommendation',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='legalnoticetracker',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),

        # AuditLog Enhancements
        migrations.AddField(
            model_name='auditlog',
            name='entity_type',
            field=models.CharField(blank=True, default='SYSTEM', max_length=100),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='entity_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),

        # ComplianceTask Model
        migrations.CreateModel(
            name='ComplianceTask',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('compliance_type', models.CharField(choices=[('GSTR-1', 'GSTR-1 (Outward Supplies)'), ('GSTR-3B', 'GSTR-3B (Monthly Return & Payment)'), ('IFF', 'IFF (QRMP Invoice Furnishing)'), ('CMP-08', 'CMP-08 (Composition Challan)'), ('PMT-06', 'PMT-06 (QRMP Tax Challan)'), ('GSTR-9', 'GSTR-9 (Annual Return)'), ('ASMT-10', 'ASMT-10 Notice Reply'), ('AUDIT', 'Statutory Tax Audit'), ('CUSTOM', 'Custom Task')], default='GSTR-3B', max_length=50)),
                ('due_date', models.DateField(db_index=True)),
                ('status', models.CharField(choices=[('UPCOMING', 'Upcoming'), ('CRITICAL', 'Critical'), ('OVERDUE', 'Overdue'), ('COMPLETED', 'Completed')], db_index=True, default='UPCOMING', max_length=30)),
                ('penalty_per_day', models.IntegerField(default=50)),
                ('applicable_to', models.CharField(default='All Regular GST Taxpayers', max_length=255)),
                ('assigned_to', models.CharField(blank=True, default='CA Rajesh Kumar', max_length=100)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('client', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='compliance_tasks', to='core.client')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='compliance_tasks', to='core.organization')),
            ],
            options={
                'ordering': ['due_date', 'status'],
            },
        ),
    ]
