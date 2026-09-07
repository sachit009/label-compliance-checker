"""
Label Compliance Checker — Scan API Router
Endpoints for scanning labels and retrieving scan history.
"""
import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.config import settings
from app.db import get_db
from app.models.database import Scan, ComplianceField
from app.models.schemas import (
    ScanResponse,
    ScanHistoryItem,
    ScanHistoryResponse,
    FieldResult,
    OverallStatus,
    FieldStatus,
)
from app.services.ocr_service import get_ocr_engine
from app.services.nlp_service import NLPExtractor
from app.services.compliance import check_compliance

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Scans"])

# NLP extractor will be initialized at startup and injected
_nlp_extractor: Optional[NLPExtractor] = None


def get_nlp_extractor() -> NLPExtractor:
    """Get the singleton NLP extractor instance."""
    global _nlp_extractor
    if _nlp_extractor is None:
        _nlp_extractor = NLPExtractor(settings.SPACY_MODEL)
    return _nlp_extractor


def _validate_image(file: UploadFile) -> None:
    """Validate uploaded file type."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. "
            f"Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}",
        )


@router.post("/scan", response_model=ScanResponse)
async def scan_label(
    file: UploadFile = File(..., description="Product label image to scan"),
    db: AsyncSession = Depends(get_db),
):
    """
    Scan a product label image for Legal Metrology compliance.

    Accepts a JPEG/PNG/WebP image, runs OCR + NLP extraction,
    validates against 6 mandatory fields, and returns compliance status.
    """
    # 1. Validate the upload
    _validate_image(file)

    # 2. Read image bytes
    image_bytes = await file.read()
    file_size_mb = len(image_bytes) / (1024 * 1024)

    if file_size_mb > settings.MAX_IMAGE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"Image too large ({file_size_mb:.1f}MB). "
            f"Maximum allowed: {settings.MAX_IMAGE_SIZE_MB}MB.",
        )

    logger.info(
        f"Scanning image: {file.filename} ({file_size_mb:.1f}MB) "
        f"using {settings.OCR_ENGINE} engine"
    )

    # 3. Save image to disk (optional)
    scan_id = uuid.uuid4()
    image_path = None
    if settings.UPLOAD_DIR:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        ext = os.path.splitext(file.filename)[1].lower()
        image_path = os.path.join(settings.UPLOAD_DIR, f"{scan_id}{ext}")
        with open(image_path, "wb") as f:
            f.write(image_bytes)

    # 4. Run OCR
    try:
        ocr_engine = get_ocr_engine(settings.OCR_ENGINE)
        raw_text = ocr_engine.extract_text(image_bytes)
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

    if not raw_text.strip():
        raise HTTPException(
            status_code=422,
            detail="No text could be extracted from the image. "
            "Ensure the label is clearly visible and well-lit.",
        )

    logger.info(f"OCR extracted {len(raw_text)} characters")

    # 5. Run NLP extraction
    try:
        nlp_extractor = get_nlp_extractor()
        extracted_fields = nlp_extractor.extract_all(raw_text)
    except Exception as e:
        logger.error(f"NLP extraction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Text extraction failed: {str(e)}",
        )

    # 6. Run compliance check
    overall_status, field_results = check_compliance(extracted_fields)

    # 7. Save to database
    try:
        db_scan = Scan(
            id=str(scan_id),
            image_path=image_path,
            raw_ocr_text=raw_text,
            overall_status=overall_status.value,
            ocr_engine_used=settings.OCR_ENGINE,
            created_at=datetime.now(timezone.utc),
        )
        db.add(db_scan)

        for field in field_results:
            db_field = ComplianceField(
                scan_id=str(scan_id),
                field_name=field.field_name,
                status=field.status.value,
                extracted_value=field.value,
                confidence=field.confidence,
                recommendation=field.recommendation,
            )
            db.add(db_field)

        await db.commit()
        logger.info(f"Scan {scan_id} saved to database")
    except Exception as e:
        logger.error(f"Database save failed: {e}")
        # Don't fail the request — still return the results
        await db.rollback()

    # 8. Build response
    compliant_count = sum(1 for f in field_results if f.status == FieldStatus.FOUND)

    return ScanResponse(
        scan_id=str(scan_id),
        overall_status=overall_status,
        fields=field_results,
        raw_text=raw_text,
        ocr_engine=settings.OCR_ENGINE,
        scanned_at=datetime.now(timezone.utc),
        compliant_count=compliant_count,
        total_fields=6,
    )


@router.get("/scans", response_model=ScanHistoryResponse)
async def get_scan_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get paginated scan history with optional status filter.
    """
    # Build query
    query = select(Scan).order_by(Scan.created_at.desc())
    count_query = select(func.count()).select_from(Scan)

    if status:
        try:
            status_enum = DBOverallStatus(status.upper())
            query = query.where(Scan.overall_status == status_enum)
            count_query = count_query.where(Scan.overall_status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}. "
                f"Use: COMPLIANT, NON_COMPLIANT, PARTIALLY_COMPLIANT",
            )

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    scans = result.scalars().all()

    # Build response items
    items = []
    for scan in scans:
        compliant_count = sum(
            1 for f in scan.fields
            if (f.status.value if hasattr(f.status, "value") else str(f.status)) == "FOUND"
        )
        status_val = scan.overall_status.value if hasattr(scan.overall_status, "value") else str(scan.overall_status)
        items.append(
            ScanHistoryItem(
                scan_id=str(scan.id),
                overall_status=OverallStatus(status_val),
                compliant_count=compliant_count,
                total_fields=6,
                scanned_at=scan.created_at,
            )
        )

    return ScanHistoryResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/scans/{scan_id}", response_model=ScanResponse)
async def get_scan_detail(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed results for a specific scan.
    """
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found.")

    # Build field results
    field_results = []
    for f in scan.fields:
        f_status_val = f.status.value if hasattr(f.status, "value") else str(f.status)
        field_results.append(
            FieldResult(
                field_name=f.field_name,
                display_name=_get_display_name(f.field_name),
                status=FieldStatus(f_status_val),
                value=f.extracted_value,
                confidence=f.confidence or 0.0,
                recommendation=f.recommendation,
            )
        )

    compliant_count = sum(1 for f in field_results if f.status == FieldStatus.FOUND)
    overall_status_val = scan.overall_status.value if hasattr(scan.overall_status, "value") else str(scan.overall_status)

    return ScanResponse(
        scan_id=str(scan.id),
        overall_status=OverallStatus(overall_status_val),
        fields=field_results,
        raw_text=scan.raw_ocr_text,
        ocr_engine=scan.ocr_engine_used,
        scanned_at=scan.created_at,
        compliant_count=compliant_count,
        total_fields=6,
    )


def _get_display_name(field_name: str) -> str:
    """Get human-readable display name for a field."""
    display_map = {
        "manufacturer_name_address": "Manufacturer / Packer / Importer Name & Address",
        "generic_name": "Common or Generic Name",
        "net_quantity": "Net Quantity",
        "date_of_manufacture": "Month & Year of Manufacture / Packing",
        "mrp": "MRP (Maximum Retail Price, incl. all taxes)",
        "consumer_care_details": "Consumer Care Details",
    }
    return display_map.get(field_name, field_name)
