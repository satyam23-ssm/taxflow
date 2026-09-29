import asyncio
import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

import sys
from pathlib import Path

# Add backend directory to sys.path if not present
backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    from .database import engine, async_session, Base
    from .models import (
        Organization,
        User,
        Client,
        InvoiceLedger,
        LegalNoticeTracker,
        ComplianceTask,
        AuditLog,
        WhatsAppInboundMessage,
        Task,
        Document
    )
    from .auth import get_password_hash
except (ImportError, ValueError):
    from app.database import engine, async_session, Base
    from app.models import (
        Organization,
        User,
        Client,
        InvoiceLedger,
        LegalNoticeTracker,
        ComplianceTask,
        AuditLog,
        WhatsAppInboundMessage,
        Task,
        Document
    )
    from app.auth import get_password_hash


async def seed_database(db: AsyncSession):
    # 1. Clear existing data
    await db.execute(delete(AuditLog))
    await db.execute(delete(WhatsAppInboundMessage))
    await db.execute(delete(Task))
    await db.execute(delete(Document))
    await db.execute(delete(ComplianceTask))
    await db.execute(delete(LegalNoticeTracker))
    await db.execute(delete(InvoiceLedger))
    await db.execute(delete(Client))
    await db.execute(delete(User))
    await db.execute(delete(Organization))
    await db.commit()

    # 2. Create Organization
    org = Organization(
        name="Kumar & Associates (Chartered Accountants)",
        subscription_tier="CA_FIRM"
    )
    db.add(org)
    await db.commit()
    await db.refresh(org)

    # 3. Create Firm Admin and Employees
    employees_data = [
        {
            "username": "rajesh.ca",
            "email": "rajesh@kumarassociates.in",
            "first_name": "Rajesh",
            "last_name": "Kumar",
            "role": "CA_FIRM_PARTNER",
            "designation": "Managing Partner (Admin)",
            "work_status": "WORKING",
            "phone_number": "+919820012345",
            "is_staff": True,
            "is_superuser": True
        },
        {
            "username": "priya.tax",
            "email": "priya@kumarassociates.in",
            "first_name": "Priya",
            "last_name": "Sharma",
            "role": "STAFF_ACCOUNTANT",
            "designation": "Senior GST Specialist",
            "work_status": "WORKING",
            "phone_number": "+919820054321",
            "is_staff": False,
            "is_superuser": False
        },
        {
            "username": "amit.gst",
            "email": "amit@kumarassociates.in",
            "first_name": "Amit",
            "last_name": "Patel",
            "role": "ARTICLE_ASSISTANT",
            "designation": "Article Assistant (GST)",
            "work_status": "WORKING",
            "phone_number": "+919820067890",
            "is_staff": False,
            "is_superuser": False
        },
        {
            "username": "neha.audit",
            "email": "neha@kumarassociates.in",
            "first_name": "Neha",
            "last_name": "Verma",
            "role": "STAFF_ACCOUNTANT",
            "designation": "Tax Auditor",
            "work_status": "IN_REVIEW",
            "phone_number": "+919820078901",
            "is_staff": False,
            "is_superuser": False
        },
        {
            "username": "rohan.intern",
            "email": "rohan@kumarassociates.in",
            "first_name": "Rohan",
            "last_name": "Mehta",
            "role": "ARTICLE_ASSISTANT",
            "designation": "Audit Trainee",
            "work_status": "ON_LEAVE",
            "phone_number": "+919820089012",
            "is_staff": False,
            "is_superuser": False
        }
    ]

    seeded_users = {}
    for ed in employees_data:
        u = User(
            username=ed["username"],
            email=ed["email"],
            hashed_password=get_password_hash("password123"),
            organization_id=org.id,
            role=ed["role"],
            designation=ed["designation"],
            work_status=ed["work_status"],
            first_name=ed["first_name"],
            last_name=ed["last_name"],
            phone_number=ed["phone_number"],
            is_staff=ed["is_staff"],
            is_superuser=ed["is_superuser"]
        )
        db.add(u)
        seeded_users[ed["username"]] = u

    await db.commit()
    for u in seeded_users.values():
        await db.refresh(u)

    user = seeded_users["rajesh.ca"]

    # 4. Create 12 Authentic Indian CA Clients
    client_configs = [
        {
            'legal_name': 'Reliance Retail Limited',
            'trade_name': 'Reliance Retail',
            'gstin': '27AABCR1234A1Z5',
            'pan': 'AABCR1234A',
            'phone': '+919820011111',
            'email': 'gst@relianceretail.com',
            'address': 'Maker Chambers IV, Nariman Point, Mumbai - 400021',
            'status': 'COMPLIANT'
        },
        {
            'legal_name': 'Tata Motors Limited',
            'trade_name': 'Tata Motors',
            'gstin': '27AABCT2345C1Z1',
            'pan': 'AABCT2345C',
            'phone': '+919820022222',
            'email': 'tax@tatamotors.com',
            'address': 'Bombay House, 24 Homi Mody Street, Mumbai - 400001',
            'status': 'AT_RISK'
        },
        {
            'legal_name': 'Infosys BPM Limited',
            'trade_name': 'Infosys BPM',
            'gstin': '29AABCI3456D1Z2',
            'pan': 'AABCI3456D',
            'phone': '+919820033333',
            'email': 'indirect.tax@infosys.com',
            'address': 'Electronics City, Hosur Road, Bengaluru - 560100',
            'status': 'COMPLIANT'
        },
        {
            'legal_name': 'Larsen & Toubro Heavy Engineering',
            'trade_name': 'L&T Heavy Engg',
            'gstin': '27AAACL0149A1ZW',
            'pan': 'AAACL0149A',
            'phone': '+919820044444',
            'email': 'finance@larsentoubro.com',
            'address': 'L&T House, Ballard Estate, Mumbai - 400001',
            'status': 'AT_RISK'
        },
        {
            'legal_name': 'Sun Pharma Laboratories Ltd',
            'trade_name': 'Sun Pharma Labs',
            'gstin': '24AAACS1234M1Z8',
            'pan': 'AAACS1234M',
            'phone': '+919820055555',
            'email': 'compliance@sunpharma.com',
            'address': 'Sun House, Goregaon East, Mumbai - 400063',
            'status': 'COMPLIANT'
        },
        {
            'legal_name': 'Zomato Hyperpure Private Limited',
            'trade_name': 'Zomato Hyperpure',
            'gstin': '07AABCZ9876Q1Z4',
            'pan': 'AABCZ9876Q',
            'phone': '+919820066666',
            'email': 'accounts@zomato.com',
            'address': 'Ground Floor, Pioneer Square, Sector 62, Gurugram - 122098',
            'status': 'PENDING_DOCS'
        },
        {
            'legal_name': 'Zenith Technologies Pvt Ltd',
            'trade_name': 'Zenith Tech',
            'gstin': '27AAACW2345Z1Z1',
            'pan': 'AAACW2345Z',
            'phone': '+919876543210',
            'email': 'cfo@zenithtech.in',
            'address': 'Bandra Kurla Complex, Mumbai - 400051',
            'status': 'COMPLIANT'
        },
        {
            'legal_name': 'NexGen Green Energy Solutions',
            'trade_name': 'NexGen Energy',
            'gstin': '27AAACN5522K1Z9',
            'pan': 'AAACN5522K',
            'phone': '+919820077777',
            'email': 'contact@nexgenenergy.in',
            'address': 'Shivaji Nagar, Pune - 411005',
            'status': 'COMPLIANT'
        },
        {
            'legal_name': 'Bharat Forge Precision Gears Ltd',
            'trade_name': 'Bharat Forge',
            'gstin': '27AABCB2211D1ZX',
            'pan': 'AABCB2211D',
            'phone': '+919820088888',
            'email': 'taxation@bharatforge.com',
            'address': 'Mundhwa, Pune - 411036',
            'status': 'COMPLIANT'
        },
        {
            'legal_name': 'Havells India Commercial Division',
            'trade_name': 'Havells Commercial',
            'gstin': '07AAACH0102M1Z0',
            'pan': 'AAACH0102M',
            'phone': '+919820099999',
            'email': 'compliance@havells.com',
            'address': 'QRG Towers, 2D Expressway, Noida - 201304',
            'status': 'COMPLIANT'
        },
        {
            'legal_name': 'Asian Paints Industrial Coatings',
            'trade_name': 'Asian Paints',
            'gstin': '27AAACA1234P1Z3',
            'pan': 'AAACA1234P',
            'phone': '+919820011223',
            'email': 'gstin@asianpaints.com',
            'address': 'Santacruz East, Mumbai - 400055',
            'status': 'COMPLIANT'
        },
        {
            'legal_name': 'Godrej Consumer Products Ltd',
            'trade_name': 'Godrej Consumer',
            'gstin': '27AAACG1234F1Z8',
            'pan': 'AAACG1234F',
            'phone': '+919820044556',
            'email': 'tax@godrejcp.com',
            'address': 'Pirojshanagar, Vikhroli East, Mumbai - 400079',
            'status': 'COMPLIANT'
        }
    ]

    client_objs = []
    for c in client_configs:
        obj = Client(
            organization_id=org.id,
            legal_name=c['legal_name'],
            trade_name=c['trade_name'],
            gstin=c['gstin'],
            pan=c['pan'],
            phone_number=c['phone'],
            email=c['email'],
            address=c['address'],
            compliance_status=c['status'],
            assigned_ca='CA Rajesh Kumar'
        )
        db.add(obj)
        client_objs.append(obj)

    await db.commit()
    for c in client_objs:
        await db.refresh(c)

    c_zenith = next((c for c in client_objs if 'Zenith' in c.trade_name), client_objs[0])
    c_tata = next((c for c in client_objs if 'Tata' in c.trade_name), client_objs[1])
    c_rel = next((c for c in client_objs if 'Reliance' in c.trade_name), client_objs[0])
    c_lt = next((c for c in client_objs if 'L&T' in c.trade_name), client_objs[3])
    c_sun = next((c for c in client_objs if 'Sun' in c.trade_name), client_objs[4])

    # 5. Invoices & ITC Ledger
    invoices_data = [
        # Mismatch 1: Value mismatch
        {
            'client': c_zenith,
            'num': 'INV-2026-0891',
            'date': date(2026, 5, 12),
            'vname': 'CloudScale Data Services Pvt Ltd',
            'vgstin': '27AAACC4455P1Z8',
            'taxable': Decimal('150000.00'),
            'cgst': Decimal('13500.00'),
            'sgst': Decimal('13500.00'),
            'igst': Decimal('0.00'),
            'matching': 'MISMATCHED',
            'portal_taxable': Decimal('120000.00'),
            'portal_tax': Decimal('21600.00'),
            'finding': 'Vendor reported ₹1,20,000 in GSTR-1, but invoice is ₹1,50,000.',
            'reason': 'Supplier omitted addon cloud infrastructure line items in GSTR-1 Table 4B.',
            'action': 'Issue automated Vendor Chaser to supplier requesting GSTR-1 amendment.',
            'status': 'APPROVED',
            'chaser_status': 'CHASE_SENT',
            'chaser_msg': 'Dear CloudScale Accounts, Invoice INV-2026-0891 appears as ₹1,20,000 in GSTR-2B instead of ₹1,50,000. Please file amendment in Table 9.',
            'source': 'MANUAL_UPLOAD'
        },
        # Mismatch 2: Missing in 2B
        {
            'client': c_tata,
            'num': 'TM-ENG-4412',
            'date': date(2026, 5, 18),
            'vname': 'Precision Auto Tools Mumbai',
            'vgstin': '27AABCP9911K1Z2',
            'taxable': Decimal('480000.00'),
            'cgst': Decimal('43200.00'),
            'sgst': Decimal('43200.00'),
            'igst': Decimal('0.00'),
            'matching': 'MISSING_IN_PORTAL',
            'portal_taxable': None,
            'portal_tax': None,
            'finding': 'Invoice completely missing from GSTR-2B (tax period May 2026).',
            'reason': 'Vendor has not filed GSTR-1 for May 2026 by statutory cutoff date 11th June.',
            'action': 'ITC is blocked under Section 16(2)(aa). Dispatch formal WhatsApp chase to supplier.',
            'status': 'APPROVED',
            'chaser_status': 'CHASE_GENERATED',
            'source': 'ERP_SYNC'
        },
        # Mismatch 3: GSTIN Inactive
        {
            'client': c_lt,
            'num': 'LT-FAB-8821',
            'date': date(2026, 5, 22),
            'vname': 'Sterling Steel Alloys Ltd',
            'vgstin': '27AAACS8833J1Z0',
            'taxable': Decimal('750000.00'),
            'cgst': Decimal('0.00'),
            'sgst': Decimal('0.00'),
            'igst': Decimal('135000.00'),
            'matching': 'MISMATCHED',
            'portal_taxable': Decimal('750000.00'),
            'portal_tax': Decimal('0.00'),
            'finding': 'Tax marked as in-eligible in GSTR-2B due to vendor GSTIN suspension.',
            'reason': 'Vendor GSTIN was suspended on 01-May-2026 under Rule 21A for non-filing of returns.',
            'action': 'Do not claim ITC in GSTR-3B Table 4(A)(5). Move to Ineligible ITC Table 4(B)(2).',
            'status': 'APPROVED',
            'chaser_status': 'NOT_CHASED',
            'source': 'MANUAL_UPLOAD'
        },
        # Matched 1
        {
            'client': c_rel,
            'num': 'RIL-MUM-9012',
            'date': date(2026, 5, 4),
            'vname': 'Reliance Jio Infocomm Ltd',
            'vgstin': '27AAACR5537N1ZO',
            'taxable': Decimal('620000.00'),
            'cgst': Decimal('55800.00'),
            'sgst': Decimal('55800.00'),
            'igst': Decimal('0.00'),
            'matching': 'MATCHED',
            'portal_taxable': Decimal('620000.00'),
            'portal_tax': Decimal('111600.00'),
            'finding': 'Exact match with GSTR-2B return. ITC eligible under Section 16.',
            'status': 'APPROVED',
            'chaser_status': 'NOT_CHASED',
            'source': 'ERP_SYNC'
        },
        # Matched 2
        {
            'client': c_sun,
            'num': 'SP-LAB-1022',
            'date': date(2026, 5, 8),
            'vname': 'Borosil Scientific Instruments',
            'vgstin': '27AAACB2233M1Z4',
            'taxable': Decimal('280000.00'),
            'cgst': Decimal('25200.00'),
            'sgst': Decimal('25200.00'),
            'igst': Decimal('0.00'),
            'matching': 'MATCHED',
            'portal_taxable': Decimal('280000.00'),
            'portal_tax': Decimal('50400.00'),
            'finding': '100% verified against GSTN portal.',
            'status': 'APPROVED',
            'chaser_status': 'NOT_CHASED',
            'source': 'MANUAL_UPLOAD'
        },
        # Pending review (OCR)
        {
            'client': c_zenith,
            'num': 'INV-2026-9901',
            'date': date(2026, 6, 2),
            'vname': 'Modern Office Ergonomics LLP',
            'vgstin': '27AABCM7711D1Z9',
            'taxable': Decimal('95000.00'),
            'cgst': Decimal('8550.00'),
            'sgst': Decimal('8550.00'),
            'igst': Decimal('0.00'),
            'matching': None,
            'portal_taxable': None,
            'portal_tax': None,
            'status': 'PENDING_REVIEW',
            'chaser_status': 'NOT_CHASED',
            'source': 'WHATSAPP'
        },
        # Matched 3
        {
            'client': c_zenith,
            'num': 'AWS-IN-2026-44',
            'date': date(2026, 5, 28),
            'vname': 'Amazon Web Services India Pvt Ltd',
            'vgstin': '27AACA7711G1Z6',
            'taxable': Decimal('340000.00'),
            'cgst': Decimal('30600.00'),
            'sgst': Decimal('30600.00'),
            'igst': Decimal('0.00'),
            'matching': 'MATCHED',
            'portal_taxable': Decimal('340000.00'),
            'portal_tax': Decimal('61200.00'),
            'finding': 'Perfect match with GSTR-2B table B2B supplies.',
            'status': 'APPROVED',
            'chaser_status': 'NOT_CHASED',
            'source': 'ERP_SYNC'
        }
    ]

    for inv in invoices_data:
        tot = inv['taxable'] + inv['cgst'] + inv['sgst'] + inv['igst']
        item = InvoiceLedger(
            organization_id=org.id,
            client_id=inv['client'].id,
            source=inv.get('source', 'MANUAL_UPLOAD'),
            processing_status=inv.get('status', 'APPROVED'),
            matching_status=inv.get('matching'),
            buyer_gstin=inv['client'].gstin,
            invoice_number=inv['num'],
            invoice_date=inv['date'],
            vendor_name=inv['vname'],
            vendor_gstin=inv['vgstin'],
            hsn_code='998313',
            taxable_value=inv['taxable'],
            cgst=inv['cgst'],
            sgst=inv['sgst'],
            igst=inv['igst'],
            cess=Decimal('0.00'),
            total_amount=tot,
            portal_taxable_value=inv.get('portal_taxable'),
            portal_tax_amount=inv.get('portal_tax'),
            ai_finding=inv.get('finding'),
            ai_reason=inv.get('reason'),
            ai_recommended_action=inv.get('action'),
            vendor_chaser_status=inv.get('chaser_status', 'NOT_CHASED'),
            vendor_chaser_message=inv.get('chaser_msg'),
            roi_minutes_saved=35
        )
        db.add(item)

    await db.commit()

    # 6. Legal Notices
    notices_data = [
        {
            'client': c_zenith,
            'type': 'DRC-01A',
            'ref': 'GST/MUM/DRC01A/2026/0942',
            'issue': date(2026, 5, 20),
            'deadline': date(2026, 6, 25),
            'demand': Decimal('342000.00'),
            'sections': ['Section 73(5)', 'Rule 142(1A)', 'Section 16(2)(c)'],
            'summary': 'Intimation of tax liability prior to notice under Section 73(5) citing alleged difference between ITC claimed in GSTR-3B vs ITC auto-populated in GSTR-2B for FY 2024-25.',
            'draft': """TO,
THE PROPER OFFICER / SUPERINTENDENT OF CENTRAL TAX,
RANGE II, DIVISION IV, MUMBAI SOUTH COMMISSIONERATE.

Subject: Submissions in response to Intimation in FORM GST DRC-01A bearing Reference No. GST/MUM/DRC01A/2026/0942 dated 20-05-2026.

Respected Sir/Madam,

1. PRELIMINARY SUBMISSION:
The Taxpayer, M/s Zenith Technologies Pvt Ltd (GSTIN: 27AAACW2345Z1Z1), respectfully submits that the proposed demand of ₹3,42,000/- is wholly unsustainable on law and facts.

2. STATUTORY COMPLIANCE UNDER SECTION 16:
The Taxpayer satisfies all conditions prescribed under Section 16(2) of the CGST Act, 2017:
(a) The Taxpayer is in possession of authentic tax invoices issued by suppliers;
(b) The goods and services have been duly received;
(c) The suppliers have paid tax to the government in terms of CBIC Circular No. 183/15/2022-GST;
(d) The Taxpayer has filed its regular monthly return in FORM GSTR-3B.

3. SETTLED JUDICIAL PRECEDENTS:
It is a settled proposition of law that ITC cannot be denied to a bona fide purchasing dealer merely on account of technical variances or portal delays by suppliers:
- Union of India v. Bharti Airtel Ltd [2021] (Supreme Court of India)
- Suncraft Energy Private Limited v. Assistant Commissioner [2023] (Calcutta HC, SLP dismissed by Supreme Court)
- D.Y. Beathel Enterprises v. State Tax Officer [2021] (Madras HC)

In view of the above statutory provisions and binding judgments, we humbly pray that the proposed proceedings in Form DRC-01A be dropped immediately.

Yours faithfully,
For Zenith Technologies Pvt Ltd
Authorized Signatory / CA Rajesh Kumar"""
        },
        {
            'client': c_tata,
            'type': 'ASMT-10',
            'ref': 'GST/PUN/ASMT10/2026/1102',
            'issue': date(2026, 5, 14),
            'deadline': date(2026, 6, 18),
            'demand': Decimal('185000.00'),
            'sections': ['Section 61', 'Rule 99', 'Section 16(4)'],
            'summary': 'Scrutiny Notice issued under Section 61 for discrepancy between taxable turnover declared in GSTR-1 and summary return GSTR-3B.',
            'draft': """TO,
THE ASSISTANT COMMISSIONER OF STATE TAX,
PUNE CIRCLE - 3, MAHARASHTRA.

Subject: Reply in Form GST ASMT-11 to Scrutiny Notice under Section 61 (Ref: GST/PUN/ASMT10/2026/1102).

Respected Sir,
With reference to the scrutiny notice for FY 2024-25, the alleged turnover variance of ₹1,85,000/- is an timing reconciliation item arising from credit notes issued under Section 34 of the CGST Act. The reconciliation statement along with Annexure 1 is submitted herewith.

Prayed accordingly.
For Tata Motors Limited"""
        },
        {
            'client': c_rel,
            'type': 'DRC-01',
            'ref': 'GST/DEL/DRC01/2026/0411',
            'issue': date(2026, 4, 10),
            'deadline': date(2026, 7, 10),
            'demand': Decimal('718000.00'),
            'sections': ['Section 73', 'Section 17(5)(h)', 'Section 50(1)'],
            'summary': 'Show Cause Notice under Section 73 alleging wrongful availment of input tax credit on corporate promotional gifts and destroyed inventory.',
            'draft': """SUBMISSION BEFORE THE ADJUDICATING AUTHORITY:
In the matter of Show Cause Notice No. GST/DEL/DRC01/2026/0411.
The taxpayer has reversed blocked credit under Rule 42/43 with statutory interest under Section 50(1). Evidence attached."""
        }
    ]

    for n in notices_data:
        nt = LegalNoticeTracker(
            organization_id=org.id,
            client_id=n['client'].id,
            notice_type=n['type'],
            notice_reference=n['ref'],
            issue_date=n['issue'],
            deadline_date=n['deadline'],
            disputed_tax_value=n['demand'],
            cited_sections=n['sections'],
            ai_summary=n['summary'],
            generated_asmt11_draft=n['draft'],
            raw_notice_text=f"Statutory Notice {n['type']} Reference {n['ref']}. Demanding {n['demand']} under {', '.join(n['sections'])}.",
            is_resolved=False
        )
        db.add(nt)

    await db.commit()

    # 7. Compliance Tasks
    tasks_data = [
        {
            'title': 'GSTR-1 Monthly Return (Regular Taxpayers)',
            'type': 'GSTR-1',
            'due': date(2026, 7, 11),
            'status': 'UPCOMING',
            'penalty': 50,
            'app': 'All Regular Monthly GST Taxpayers',
            'desc': 'Filing of outward supplies statement for turnover > ₹5 Crore'
        },
        {
            'title': 'GSTR-1 (IFF) QRMP Invoices',
            'type': 'IFF',
            'due': date(2026, 7, 13),
            'status': 'UPCOMING',
            'penalty': 50,
            'app': 'QRMP Quarterly Taxpayers',
            'desc': 'Optional Invoice Furnishing Facility for B2B supplies under QRMP scheme'
        },
        {
            'title': 'GSTR-3B Summary Return & Tax Payment',
            'type': 'GSTR-3B',
            'due': date(2026, 7, 20),
            'status': 'CRITICAL',
            'penalty': 50,
            'app': 'All Regular GST Registered Taxpayers',
            'desc': 'Monthly self-assessed summary return and discharge of tax liability'
        },
        {
            'title': 'PMT-06 Monthly Challan Payment',
            'type': 'PMT-06',
            'due': date(2026, 7, 25),
            'status': 'UPCOMING',
            'penalty': 0,
            'app': 'QRMP Quarterly Scheme Taxpayers',
            'desc': 'Monthly payment of 35% fixed sum or self-assessed liability under QRMP'
        },
        {
            'title': 'GSTR-9 Annual Return Preparation',
            'type': 'GSTR-9',
            'due': date(2026, 12, 31),
            'status': 'UPCOMING',
            'penalty': 200,
            'app': 'Turnover > ₹2 Crore',
            'desc': 'Consolidated annual return and ITC reconciliation for FY 2025-26'
        }
    ]

    for td in tasks_data:
        ct = ComplianceTask(
            organization_id=org.id,
            title=td['title'],
            compliance_type=td['type'],
            due_date=td['due'],
            status=td['status'],
            penalty_per_day=td['penalty'],
            applicable_to=td['app'],
            description=td['desc'],
            assigned_to='CA Rajesh Kumar'
        )
    await db.commit()

    # 7b. Firm Tasks Assigned to Employees
    u_priya = seeded_users.get("priya.tax")
    u_amit = seeded_users.get("amit.gst")
    u_neha = seeded_users.get("neha.audit")
    u_rohan = seeded_users.get("rohan.intern")

    firm_tasks = [
        {
            "title": "Reconcile May/June GSTR-2B Mismatches & Follow Up",
            "desc": "Check CloudScale and Borosil variances. Cross-verify credit notes in books vs GSTN portal.",
            "client": c_zenith,
            "assigned_user": u_priya,
            "assigned_name": "Priya Sharma",
            "priority": "HIGH",
            "status": "IN_PROGRESS",
            "due": date(2026, 6, 20)
        },
        {
            "title": "Draft ASMT-11 Scrutiny Defense for Turnover Discrepancy",
            "desc": "Review Section 61 notice from Pune Ward 3. Cite CBIC Circular 183 and prepare reconciliation Annexure.",
            "client": c_tata,
            "assigned_user": u_amit,
            "assigned_name": "Amit Patel",
            "priority": "URGENT",
            "status": "OPEN",
            "due": date(2026, 6, 18)
        },
        {
            "title": "Audit Reliance Retail Ineligible ITC under Sec 17(5)",
            "desc": "Identify blocked credits on corporate gifts and warehouse losses for FY 2025-26 audit file.",
            "client": c_rel,
            "assigned_user": u_neha,
            "assigned_name": "Neha Verma",
            "priority": "MEDIUM",
            "status": "IN_PROGRESS",
            "due": date(2026, 6, 28)
        },
        {
            "title": "Follow up with Borosil on E-way Bill E-Invoicing discrepancy",
            "desc": "Ensure IRN QR code is present and matching the physical invoice copy uploaded by client.",
            "client": c_sun,
            "assigned_user": u_priya,
            "assigned_name": "Priya Sharma",
            "priority": "MEDIUM",
            "status": "OPEN",
            "due": date(2026, 6, 22)
        },
        {
            "title": "GSTR-3B Return Preparation and Net Tax Challan Generation",
            "desc": "Finalize Table 3.1 outward liabilities, offset with eligible Table 4 ITC, and prepare PMT-06 challan.",
            "client": c_zenith,
            "assigned_user": u_amit,
            "assigned_name": "Amit Patel",
            "priority": "HIGH",
            "status": "COMPLETED",
            "due": date(2026, 6, 15)
        },
        {
            "title": "Verify HSN Code 998313 for CloudScale Invoices",
            "desc": "Verify 6-digit HSN classification conformity with GST rate notifications.",
            "client": c_zenith,
            "assigned_user": u_rohan,
            "assigned_name": "Rohan Mehta",
            "priority": "LOW",
            "status": "OPEN",
            "due": date(2026, 6, 25)
        }
    ]

    for ft in firm_tasks:
        t = Task(
            organization_id=org.id,
            client_id=ft["client"].id if ft["client"] else None,
            title=ft["title"],
            description=ft["desc"],
            priority=ft["priority"],
            status=ft["status"],
            source="ADMIN_DELEGATION",
            assigned_user_id=ft["assigned_user"].id if ft["assigned_user"] else None,
            assigned_to=ft["assigned_name"],
            due_date=ft["due"],
            completed_at=datetime.utcnow() if ft["status"] == "COMPLETED" else None,
            activity_history=[
                {"timestamp": datetime.utcnow().isoformat(), "action": f"Task assigned to {ft['assigned_name']} by CA Rajesh Kumar (Admin)"}
            ]
        )
        db.add(t)

    await db.commit()

    # 8. WhatsApp Messages
    wa_msgs = [
        {
            'client': c_zenith,
            'phone': c_zenith.phone_number,
            'type': 'image',
            'text': 'Attached invoice for hardware server rack purchased from CloudScale.',
            'media_id': 'WA-MEDIA-90812'
        },
        {
            'client': c_tata,
            'phone': c_tata.phone_number,
            'type': 'text',
            'text': 'Sir, please file DRC-01A reply before the 25th deadline. Director has signed authorization.',
            'media_id': ''
        }
    ]

    for wm in wa_msgs:
        m = WhatsAppInboundMessage(
            organization_id=org.id,
            client_id=wm['client'].id,
            direction='INBOUND',
            processing_status='PROCESSED',
            sender_phone=wm['phone'],
            message_type=wm['type'],
            text_body=wm['text'],
            media_id=wm['media_id']
        )
        db.add(m)

    # 9. Audit Logs
    audit_entries = [
        "CA Rajesh Kumar logged in to TaxFlow AI (Session Started).",
        "System executed auto GSTR-2B sync: 12 invoices verified, 3 discrepancies detected.",
        "Gemini OCR extracted invoice TM-ENG-4412 with 98% confidence score.",
        "Dispatched WhatsApp Vendor Chaser to CloudScale Data Services Pvt Ltd.",
        "Generated statutory ASMT-11 reply for DRC-01A (Ref: GST/MUM/DRC01A/2026/0942).",
        "Broadcasted statutory filing reminders to all 12 active CA firm clients."
    ]

    for ae in audit_entries:
        al = AuditLog(
            organization_id=org.id,
            user_id=user.id,
            action=ae,
            entity_type='SYSTEM'
        )
        db.add(al)

    await db.commit()


async def run():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        await seed_database(session)
    print("Database successfully created and seeded!")


if __name__ == "__main__":
    asyncio.run(run())
