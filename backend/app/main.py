"""
Label Compliance Checker — FastAPI Application Entry Point
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import engine
from app.models.database import Base
from app.routers.scan import router as scan_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    - On startup: create DB tables, warm up OCR + NLP models.
    - On shutdown: dispose DB engine.
    """
    logger.info("=" * 60)
    logger.info(f"  🏷️  {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"  OCR Engine: {settings.OCR_ENGINE}")
    logger.info("=" * 60)

    # Create database tables
    logger.info("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready.")

    # Pre-warm OCR engine (loads model into memory)
    logger.info("Warming up OCR engine...")
    try:
        from app.services.ocr_service import get_ocr_engine
        get_ocr_engine(settings.OCR_ENGINE)
        logger.info("OCR engine warmed up.")
    except Exception as e:
        logger.error(f"OCR engine warmup failed: {e}")
        logger.warning("OCR will initialize on first request instead.")

    # Pre-warm NLP extractor
    logger.info("Warming up NLP extractor...")
    try:
        from app.routers.scan import get_nlp_extractor
        get_nlp_extractor()
        logger.info("NLP extractor warmed up.")
    except Exception as e:
        logger.error(f"NLP warmup failed: {e}")
        logger.warning("NLP will initialize on first request instead.")

    logger.info("🚀 Application ready!")

    yield

    # Shutdown
    logger.info("Shutting down...")
    await engine.dispose()
    logger.info("Database connections closed. Goodbye!")


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Scan product labels and verify compliance with the "
        "Legal Metrology (Packaged Commodities) Rules, 2011. "
        "Checks 6 mandatory fields: Manufacturer, Generic Name, "
        "Net Quantity, Date of Manufacture, MRP, and Consumer Care Details."
    ),
    lifespan=lifespan,
)

# CORS — allow Flutter app to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

# Include routers
app.include_router(scan_router)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "ocr_engine": settings.OCR_ENGINE,
    }


# Mount Flutter Web App if build exists
web_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../frontend/label_checker/build/web")
)
if os.path.exists(web_dir):
    app.mount("/app", StaticFiles(directory=web_dir, html=True), name="flutter_app")


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to Flutter app or API docs."""
    if os.path.exists(web_dir):
        return RedirectResponse(url="/app/")
    return RedirectResponse(url="/docs")
