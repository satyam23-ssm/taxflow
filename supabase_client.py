"""
TaxFlow AI — Dedicated Supabase Integration Module
Handles:
1. Supabase PostgreSQL async connection URL formatting (for SQLAlchemy + asyncpg)
2. Supabase Python SDK client (REST API & Storage Bucket for scanned invoices)
3. Direct health-check when run via `python supabase_client.py`
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables from backend/.env or root .env
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_ENV = ROOT_DIR / "backend" / ".env"
ROOT_ENV = ROOT_DIR / ".env"

if BACKEND_ENV.exists():
    load_dotenv(dotenv_path=BACKEND_ENV)
if ROOT_ENV.exists():
    load_dotenv(dotenv_path=ROOT_ENV)


SUPABASE_URL: str = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY: str = (
    os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    or os.getenv("SUPABASE_KEY", "").strip()
    or os.getenv("SUPABASE_ANON_KEY", "").strip()
)
SUPABASE_BUCKET: str = os.getenv("SUPABASE_BUCKET", "taxflow-invoices")


def get_async_postgres_url(raw_url: Optional[str] = None) -> str:
    """
    Converts a standard Supabase PostgreSQL connection string:
      postgresql://postgres.[ref]:[password]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
    into an asyncpg-compatible SQLAlchemy URL:
      postgresql+asyncpg://postgres.[ref]:[password]@...
    """
    url = (raw_url or os.getenv("DATABASE_URL") or "").strip()
    if not url:
        return "sqlite+aiosqlite:///./taxflow.db"

    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    return url


def get_supabase_client():
    """
    Returns an initialized Supabase SDK client if SUPABASE_URL and SUPABASE_KEY are configured.
    Requires `pip install supabase`.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        from supabase import create_client, Client
        client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return client
    except ImportError:
        print("Warning: 'supabase' package is not installed. Run: pip install supabase")
        return None
    except Exception as exc:
        print(f"Supabase client initialization error: {exc}")
        return None


def upload_invoice_to_supabase_storage(
    file_bytes: bytes,
    filename: str,
    content_type: str = "application/pdf",
    folder: str = "uploads"
) -> Optional[str]:
    """
    Uploads an invoice file (PDF/Image) to the Supabase Storage bucket (`taxflow-invoices`).
    Returns the storage path on success, or None if Supabase is not configured.
    """
    client = get_supabase_client()
    if not client or not file_bytes:
        return None

    storage_path = f"{folder}/{filename}"
    try:
        client.storage.from_(SUPABASE_BUCKET).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": content_type, "upsert": "true"}
        )
        return storage_path
    except Exception as exc:
        print(f"Supabase Storage upload error: {exc}")
        return None


def fetch_supabase_invoices(limit: int = 100) -> List[Dict[str, Any]]:
    """Fetches invoices directly via Supabase REST API (PostgREST)."""
    client = get_supabase_client()
    if not client:
        return []
    try:
        res = (
            client.table("invoice_ledger")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []
    except Exception as exc:
        print(f"Supabase fetch_invoices error: {exc}")
        return []


def insert_supabase_invoice(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Inserts a parsed invoice record directly into Supabase `invoice_ledger`."""
    client = get_supabase_client()
    if not client:
        return None
    try:
        res = client.table("invoice_ledger").insert(record).execute()
        return res.data[0] if res.data else None
    except Exception as exc:
        print(f"Supabase insert_invoice error: {exc}")
        return None


if __name__ == "__main__":
    print("=== TaxFlow AI — Supabase Connection Check ===")
    db_url = get_async_postgres_url()
    print(f"SQLAlchemy URL : {db_url.split('@')[-1] if '@' in db_url else db_url}")
    print(f"SUPABASE_URL   : {SUPABASE_URL or '(not set)'}")
    sb = get_supabase_client()
    if sb:
        print("Supabase Client: Connected successfully!")
        rows = fetch_supabase_invoices(limit=5)
        print(f"Invoices found : {len(rows)}")
    else:
        print("Supabase Client: Not configured yet. Set SUPABASE_URL & SUPABASE_KEY in backend/.env")

