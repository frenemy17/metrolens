from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

# Load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Fallback: manually load .env
    _env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(_env_path):
        for _line in open(_env_path):
            _line = _line.strip()
            if '=' in _line and not _line.startswith('#'):
                _k, _v = _line.split('=', 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))


from api.v1.auth import router as auth_router
from api.v1.inspections import router as inspections_router
from api.v1.reports import router as reports_router
from api.v1.ecommerce import router as ecommerce_router
from api.v1.enforcement import router as enforcement_router
from api.v1.admin import router as admin_router
from api.v1.dashboard import router as dashboard_router
from api.v1.inspections_ui import router as inspections_ui_router

from core.database import engine, Base
import core.models # Ensure models are loaded

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="MetroLens API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(inspections_router, prefix="/api/v1/inspections", tags=["inspections"])
app.include_router(reports_router, prefix="/api/v1/inspections", tags=["reports"])
app.include_router(enforcement_router, prefix="/api/v1/inspections", tags=["enforcement"])
app.include_router(ecommerce_router, prefix="/api/v1/ecommerce", tags=["ecommerce"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(inspections_ui_router, prefix="/api/v1/inspections", tags=["inspections_ui"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
