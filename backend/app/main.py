import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .database import engine, Base, async_session
from .config import settings
from .seed import seed_database
from .models import User
from sqlalchemy import select

# Routers
from .routers import auth, clients, invoices, reconciliation, chaser, notices, compliance, connectors, analytics, audit, tasks_and_docs, team

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Check if database has users; if empty, seed demo data
    async with async_session() as session:
        result = await session.execute(select(User).limit(1))
        if not result.scalar_one_or_none():
            try:
                await seed_database(session)
                print("Default CA Practice database auto-seeded.")
            except Exception as e:
                print(f"Auto-seed exception: {e}")

    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="TaxFlow AI API",
    description="Next-generation autonomous tax compliance, ITC reconciliation, and legal notice defense system for Indian CA firms.",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(clients.router)
app.include_router(invoices.router)
app.include_router(reconciliation.router)
app.include_router(chaser.router)
app.include_router(notices.router)
app.include_router(compliance.router)
app.include_router(connectors.router)
app.include_router(analytics.router)
app.include_router(audit.router)
app.include_router(tasks_and_docs.router)
app.include_router(team.router)


# Static file mounts
css_dir = FRONTEND_DIR / "css"
js_dir = FRONTEND_DIR / "js"
if css_dir.exists():
    app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")
if js_dir.exists():
    app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")


# Serve Frontend HTML Pages
def serve_html(filename: str):
    file_path = FRONTEND_DIR / filename
    if file_path.exists():
        return FileResponse(str(file_path), media_type="text/html")
    return HTMLResponse(content=f"<h1>File not found: {filename}</h1>", status_code=404)


@app.get("/", include_in_schema=False)
async def home():
    return serve_html("index.html")


@app.get("/index.html", include_in_schema=False)
async def index_page():
    return serve_html("index.html")


@app.get("/login.html", include_in_schema=False)
async def login_page():
    return serve_html("login.html")


@app.get("/dashboard.html", include_in_schema=False)
async def dashboard_page():
    return serve_html("dashboard.html")
