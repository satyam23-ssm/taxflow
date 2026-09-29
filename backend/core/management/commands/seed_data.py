import os
import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import (
    Organization,
    User,
    Client,
    InvoiceLedger,
    LegalNoticeTracker,
    ComplianceTask,
    AuditLog,
    WhatsAppInboundMessage
)

class Command(BaseCommand):
    help = 'Seeds authentic Indian CA practice data for TaxFlow AI'

    def handle(self, *args, **options):
        self.stdout.write('Clearing existing data...')
        AuditLog.objects.all().delete()
        WhatsAppInboundMessage.objects.all().delete()
        ComplianceTask.objects.all().delete()
        LegalNoticeTracker.objects.all().delete()
        InvoiceLedger.objects.all().delete()
        Client.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        Organization.objects.all().delete()

        self.stdout.write('Seeding authentic Indian CA firm data...')
        with transaction.atomic():
            # 1. Create Organization & User
            org = Organization.objects.create(
                name='Kumar & Associates (Chartered Accountants)',
                subscription_tier=Organization.SubscriptionTier.CA_FIRM
            )

            user = User.objects.create(
                username='rajesh.ca',
                email='rajesh@kumarassociates.in',
                organization=org,
                role=User.Role.CA_FIRM_PARTNER,
                first_name='Rajesh',
                last_name='Kumar',
                phone_number='+919820012345'
            )
            user.set_password('password123')
            user.save()

            # 2. Create 12 Authentic Indian CA Clients
            client_configs = [
                {
                    'legal_name': 'Reliance Retail Limited',
                    'trade_name': 'Reliance Retail',
                    'gstin': '27AABCR1234A1Z5',
                    'pan': 'AABCR1234A',
                    'phone': '+919820011111',
                    'email': 'gst@relianceretail.com',
                    'address': 'Maker Chambers IV, Nariman Point, Mumbai - 400021',
                    'status': Client.ComplianceStatus.COMPLIANT
                },
                {
                    'legal_name': 'Tata Motors Limited',
                    'trade_name': 'Tata Motors',
                    'gstin': '27AABCT2345C1Z1',
                    'pan': 'AABCT2345C',
                    'phone': '+919820022222',
                    'email': 'tax@tatamotors.com',
                    'address': 'Bombay House, 24 Homi Mody Street, Mumbai - 400001',
                    'status': Client.ComplianceStatus.AT_RISK
                },
                {
                    'legal_name': 'Infosys BPM Limited',
                    'trade_name': 'Infosys BPM',
                    'gstin': '29AABCI3456D1Z2',
                    'pan': 'AABCI3456D',
                    'phone': '+919820033333',
                    'email': 'indirect.tax@infosys.com',
                    'address': 'Electronics City, Hosur Road, Bengaluru - 560100',
                    'status': Client.ComplianceStatus.COMPLIANT
                },
                {
                    'legal_name': 'Larsen & Toubro Heavy Engineering',
                    'trade_name': 'L&T Heavy Engg',
                    'gstin': '27AAACL0149A1ZW',
                    'pan': 'AAACL0149A',
                    'phone': '+919820044444',
                    'email': 'finance@larsentoubro.com',
                    'address': 'L&T House, Ballard Estate, Mumbai - 400001',
                    'status': Client.ComplianceStatus.AT_RISK
                },
                {
                    'legal_name': 'Sun Pharma Laboratories Ltd',
                    'trade_name': 'Sun Pharma Labs',
                    'gstin': '24AAACS1234M1Z8',
                    'pan': 'AAACS1234M',
                    'phone': '+919820055555',
                    'email': 'compliance@sunpharma.com',
                    'address': 'Sun House, Goregaon East, Mumbai - 400063',
                    'status': Client.ComplianceStatus.COMPLIANT
                },
                {
                    'legal_name': 'Zomato Hyperpure Private Limited',
                    'trade_name': 'Zomato Hyperpure',
                    'gstin': '07AABCZ9876Q1Z4',
                    'pan': 'AABCZ9876Q',
                    'phone': '+919820066666',
                    'email': 'accounts@zomato.com',
                    'address': 'Ground Floor, Pioneer Square, Sector 62, Gurugram - 122098',
                    'status': Client.ComplianceStatus.PENDING_DOCS
                },
                {
                    'legal_name': 'Zenith Technologies Pvt Ltd',
                    'trade_name': 'Zenith Tech',
                    'gstin': '27AAACW2345Z1Z1',
                    'pan': 'AAACW2345Z',
                    'phone': '+919876543210',
                    'email': 'cfo@zenithtech.in',
                    'address': 'Bandra Kurla Complex, Mumbai - 400051',
                    'status': Client.ComplianceStatus.COMPLIANT
                },
                {
                    'legal_name': 'NexGen Green Energy Solutions',
                    'trade_name': 'NexGen Energy',
                    'gstin': '27AAACN5522K1Z9',
                    'pan': 'AAACN5522K',
                    'phone': '+919820077777',
                    'email': 'contact@nexgenenergy.in',
                    'address': 'Shivaji Nagar, Pune - 411005',
                    'status': Client.ComplianceStatus.COMPLIANT
                },
                {
                    'legal_name': 'Bharat Forge Precision Gears Ltd',
                    'trade_name': 'Bharat Forge',
                    'gstin': '27AABCB2211D1ZX',
                    'pan': 'AABCB2211D',
                    'phone': '+919820088888',
                    'email': 'taxation@bharatforge.com',
                    'address': 'Mundhwa, Pune - 411036',
                    'status': Client.ComplianceStatus.COMPLIANT
                },
                {
                    'legal_name': 'Havells India Commercial Division',
                    'trade_name': 'Havells Commercial',
                    'gstin': '07AAACH0102M1Z0',
                    'pan': 'AAACH0102M',
                    'phone': '+919820099999',
                    'email': 'invoices@havells.com',
                    'address': 'QRG Towers, 2D, Expressway, Noida - 201304',
                    'status': Client.ComplianceStatus.COMPLIANT
                },
                {
                    'legal_name': 'Godrej Consumer Products Ltd',
                    'trade_name': 'Godrej Consumer',
                    'gstin': '27AAACG0582B1ZW',
                    'pan': 'AAACG0582B',
                    'phone': '+919820100000',
                    'email': 'finance@godrejcp.com',
                    'address': 'Godrej One, Pirojshanagar, Vikhroli, Mumbai - 400079',
                    'status': Client.ComplianceStatus.COMPLIANT
                },
                {
                    'legal_name': 'Wipro Infrastructure Engineering',
                    'trade_name': 'Wipro Infra Engg',
                    'gstin': '29AABCW4567E1Z3',
                    'pan': 'AABCW4567E',
                    'phone': '+919820111111',
                    'email': 'gsthelpdesk@wipro.com',
                    'address': 'Sarjapur Road, Doddakannelli, Bengaluru - 560035',
                    'status': Client.ComplianceStatus.COMPLIANT
                }
            ]

            created_clients = []
            for cfg in client_configs:
                c = Client.objects.create(
                    organization=org,
                    legal_name=cfg['legal_name'],
                    trade_name=cfg['trade_name'],
                    gstin=cfg['gstin'],
                    pan=cfg['pan'],
                    phone_number=cfg['phone'],
                    email=cfg['email'],
                    address=cfg['address'],
                    compliance_status=cfg['status'],
                    is_active=True
                )
                created_clients.append(c)

            c_reliance = created_clients[0]
            c_tata = created_clients[1]
            c_infosys = created_clients[2]
            c_lt = created_clients[3]
            c_zenith = created_clients[6]

            # 3. Create Authentic Invoices
            # --- Matched Invoices ---
            InvoiceLedger.objects.create(
                organization=org,
                client=c_reliance,
                invoice_number='INV-2026-8812',
                invoice_date=datetime.date(2026, 5, 10),
                vendor_name='Tata Communications Ltd',
                vendor_gstin='27AAACT2727Q1ZW',
                buyer_gstin=c_reliance.gstin,
                hsn_code='998313',
                taxable_value=Decimal('150000.00'),
                cgst=Decimal('13500.00'),
                sgst=Decimal('13500.00'),
                igst=Decimal('0.00'),
                total_amount=Decimal('177000.00'),
                portal_taxable_value=Decimal('150000.00'),
                portal_tax_amount=Decimal('27000.00'),
                source=InvoiceLedger.Source.ERP,
                processing_status=InvoiceLedger.ProcessingStatus.APPROVED,
                matching_status=InvoiceLedger.MatchingStatus.MATCHED,
                roi_minutes_saved=35
            )

            InvoiceLedger.objects.create(
                organization=org,
                client=c_infosys,
                invoice_number='AWS-IN-2026-904',
                invoice_date=datetime.date(2026, 5, 14),
                vendor_name='Amazon Web Services India Pvt Ltd',
                vendor_gstin='07AABCA3628L1ZV',
                buyer_gstin=c_infosys.gstin,
                hsn_code='998315',
                taxable_value=Decimal('420000.00'),
                cgst=Decimal('0.00'),
                sgst=Decimal('0.00'),
                igst=Decimal('75600.00'),
                total_amount=Decimal('495600.00'),
                portal_taxable_value=Decimal('420000.00'),
                portal_tax_amount=Decimal('75600.00'),
                source=InvoiceLedger.Source.ERP,
                processing_status=InvoiceLedger.ProcessingStatus.APPROVED,
                matching_status=InvoiceLedger.MatchingStatus.MATCHED,
                roi_minutes_saved=35
            )

            # --- Mismatched Invoice 1: Tax value difference ---
            InvoiceLedger.objects.create(
                organization=org,
                client=c_tata,
                invoice_number='INV-99283',
                invoice_date=datetime.date(2026, 5, 12),
                vendor_name='Steel Authority of India Ltd (SAIL)',
                vendor_gstin='27TEST9999X1Z9',
                buyer_gstin=c_tata.gstin,
                hsn_code='720851',
                taxable_value=Decimal('150000.00'),
                cgst=Decimal('13500.00'),
                sgst=Decimal('13500.00'),
                igst=Decimal('0.00'),
                total_amount=Decimal('177000.00'),
                portal_taxable_value=Decimal('69444.00'),
                portal_tax_amount=Decimal('12500.00'),
                ai_finding='Tax value mismatch between Books & GSTR-2B',
                ai_reason='Vendor uploaded invoice in GSTR-1 with taxable value of ₹69,444.00 instead of ₹1,50,000.00 recorded in books. ITC variance is ₹14,500.',
                ai_confidence=0.98,
                ai_recommended_action='Generate Vendor Chase requesting supplier to amend invoice in Table 9 of next GSTR-1.',
                vendor_chaser_status=InvoiceLedger.VendorChaserStatus.NOT_CHASED,
                source=InvoiceLedger.Source.ERP,
                processing_status=InvoiceLedger.ProcessingStatus.APPROVED,
                matching_status=InvoiceLedger.MatchingStatus.MISMATCHED,
                roi_minutes_saved=45
            )

            # --- Mismatched Invoice 2: Missing completely in GSTR-2B ---
            InvoiceLedger.objects.create(
                organization=org,
                client=c_lt,
                invoice_number='LT-SUP-4011',
                invoice_date=datetime.date(2026, 5, 18),
                vendor_name='Precision Hydraulics India Ltd',
                vendor_gstin='29TEST8888Y1Z2',
                buyer_gstin=c_lt.gstin,
                hsn_code='841221',
                taxable_value=Decimal('102222.00'),
                cgst=Decimal('0.00'),
                sgst=Decimal('0.00'),
                igst=Decimal('18400.00'),
                total_amount=Decimal('120622.00'),
                portal_taxable_value=None,
                portal_tax_amount=None,
                ai_finding='Invoice completely missing from GSTR-2B',
                ai_reason='Invoice present in Purchase Register but not furnished by Precision Hydraulics India Ltd in GSTR-1 for May 2026. ₹18,400 ITC at risk.',
                ai_confidence=0.99,
                ai_recommended_action='Vendor follow-up recommended before GSTR-3B filing.',
                vendor_chaser_status=InvoiceLedger.VendorChaserStatus.NOT_CHASED,
                source=InvoiceLedger.Source.MANUAL_UPLOAD,
                processing_status=InvoiceLedger.ProcessingStatus.APPROVED,
                matching_status=InvoiceLedger.MatchingStatus.MISSING_IN_PORTAL,
                roi_minutes_saved=45
            )

            # --- WhatsApp Ingestion: Pending CA Review ---
            wa_inv = InvoiceLedger.objects.create(
                organization=org,
                client=c_zenith,
                invoice_number='TS/26-27/045',
                invoice_date=datetime.date(2026, 5, 14),
                vendor_name='Tata Steel Ltd',
                vendor_gstin='27AABCT2345C1Z1',
                buyer_gstin=c_zenith.gstin,
                hsn_code='720810',
                taxable_value=Decimal('150000.00'),
                cgst=Decimal('13500.00'),
                sgst=Decimal('13500.00'),
                igst=Decimal('0.00'),
                total_amount=Decimal('177000.00'),
                source=InvoiceLedger.Source.WHATSAPP,
                processing_status=InvoiceLedger.ProcessingStatus.PENDING_REVIEW,
                raw_extracted_data={
                    "vendor_name": "Tata Steel Ltd",
                    "vendor_gstin": "27AABCT2345C1Z1",
                    "invoice_number": "TS/26-27/045",
                    "invoice_date": "2026-05-14",
                    "taxable_value": 150000.00,
                    "cgst": 13500.00,
                    "sgst": 13500.00,
                    "total_amount": 177000.00,
                    "confidence_score": 0.98,
                    "engine": "gemini_vision_pro"
                },
                roi_minutes_saved=30
            )

            # 4. Create Legal Notice Cases
            LegalNoticeTracker.objects.create(
                organization=org,
                client=c_reliance,
                notice_type='ASMT-10',
                notice_reference='ZA2705260123456',
                issue_date=datetime.date(2026, 5, 10),
                deadline_date=datetime.date(2026, 6, 24),
                cited_sections=['Section 61', 'Rule 99', 'Circular 183'],
                disputed_tax_value=Decimal('225000.00'),
                raw_notice_text='Scrutiny of returns for FY 2024-25. Difference of ₹2,25,000 detected between GSTR-3B claimed ITC and GSTR-2A auto-populated data.',
                ai_summary='The Proper Officer detected a discrepancy between ITC claimed in GSTR-3B (₹12,45,000) and ITC available in GSTR-2A/2B (₹10,20,000) for FY 2024-25. Difference of ₹2,25,000 demands explanation under Section 61.',
                ai_recommendation='Our system matched ₹2,00,000 of the missing ITC to invoices filed late by vendors in subsequent months. Prepare ASMT-11 citing circular 183/15/2022-GST for the remainder.',
                generated_asmt11_draft="""BEFORE THE SUPERINTENDENT OF CENTRAL / STATE TAX
WARD 14, GST COMMISSIONERATE, MUMBAI

IN THE MATTER OF:
M/s Reliance Retail Limited (GSTIN: 27AABCR1234A1Z5) ... Assessee / Taxpayer
VERSUS
THE PROPER OFFICER, GST ... Department

REPLY TO FORM GST ASMT-10 (REF: ZA2705260123456)
TAX PERIOD: FY 2024-25 | DEMAND DISPUTED: INR 2,25,000.00

MOST RESPECTFULLY SUBMITTED:

1. FULFILLMENT OF ALL STATUTORY CONDITIONS UNDER SECTION 16(2):
It is submitted that the Assessee satisfies all cumulative conditions specified under Section 16(2) of the CGST Act, 2017:
(a) The Assessee holds genuine tax invoices issued by registered suppliers;
(b) Goods/services were physically received;
(c) Tax was charged and discharged to the government;
(d) Returns under Section 39 in Form GSTR-3B have been furnished regularly.

2. CLARIFICATION AS PER CBIC CIRCULAR NO. 183/15/2022-GST:
Out of the alleged variance of ₹2,25,000, ITC amounting to ₹2,00,000 relates to suppliers who filed GSTR-1 belatedly in subsequent tax periods. The reconciliation statement is annexed as Annexure-A.

3. SETTLED JURISPRUDENCE (D.Y. BEATHEL ENTERPRISES):
In D.Y. Beathel Enterprises v. State Tax Officer (Madras High Court), it was held that recovery proceedings must first be directed against the defaulting seller before penalizing the bona fide purchasing dealer.

4. PRAYER:
In view of the documentary evidence annexed, it is respectfully prayed that the proposed proceedings under Section 61 be dropped in toto.

FOR M/S Reliance Retail Limited
(Authorised Signatory / Tax Practitioner)
""",
                is_resolved=False
            )

            # 5. Create Statutory Compliance Tasks
            deadlines = [
                {
                    'title': 'GSTR-1 Monthly Outward Supplies Filing',
                    'type': ComplianceTask.ComplianceType.GSTR1,
                    'desc': 'Outward Supplies Statement (Monthly filers > ₹5 Cr turnover)',
                    'due': datetime.date(2026, 7, 11),
                    'status': ComplianceTask.TaskStatus.UPCOMING,
                    'penalty': 50,
                    'app': 'All Regular Taxpayers'
                },
                {
                    'title': 'GSTR-1 (IFF) QRMP Invoice Furnishing',
                    'type': ComplianceTask.ComplianceType.IFF,
                    'desc': 'Invoice Furnishing Facility for QRMP Scheme (Months 1 & 2)',
                    'due': datetime.date(2026, 7, 13),
                    'status': ComplianceTask.TaskStatus.UPCOMING,
                    'penalty': 50,
                    'app': 'QRMP Scheme Taxpayers'
                },
                {
                    'title': 'GSTR-3B Monthly Return & Tax Payment',
                    'type': ComplianceTask.ComplianceType.GSTR3B,
                    'desc': 'Summary Return and monthly tax payment discharge',
                    'due': datetime.date(2026, 7, 20),
                    'status': ComplianceTask.TaskStatus.CRITICAL,
                    'penalty': 50,
                    'app': 'All Monthly Filers'
                },
                {
                    'title': 'PMT-06 Monthly Challan Payment',
                    'type': ComplianceTask.ComplianceType.PMT06,
                    'desc': 'Challan for Monthly Payment under QRMP Scheme',
                    'due': datetime.date(2026, 7, 25),
                    'status': ComplianceTask.TaskStatus.UPCOMING,
                    'penalty': 0,
                    'app': 'QRMP Quarterly Taxpayers'
                }
            ]
            for d in deadlines:
                ComplianceTask.objects.create(
                    organization=org,
                    title=d['title'],
                    compliance_type=d['type'],
                    description=d['desc'],
                    due_date=d['due'],
                    status=d['status'],
                    penalty_per_day=d['penalty'],
                    applicable_to=d['app']
                )

            # 6. Create Initial Audit Logs
            AuditLog.objects.create(
                organization=org,
                user=user,
                action='TaxFlow AI Practice Workspace initialized with 12 active CA clients',
                entity_type='FIRM'
            )
            AuditLog.objects.create(
                organization=org,
                user=user,
                action='Gemini Vision OCR extracted invoice TS/26-27/045 for Zenith Tech',
                entity_type='INVOICE'
            )
            AuditLog.objects.create(
                organization=org,
                user=user,
                action='GSTR-2B Sync flagged ₹18,400 ITC mismatch for L&T Heavy Engg',
                entity_type='RECONCILIATION'
            )

        self.stdout.write(self.style.SUCCESS('Successfully seeded TaxFlow AI production-ready CA practice data!'))
