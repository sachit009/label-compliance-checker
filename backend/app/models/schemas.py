"""
Label Compliance Checker — Pydantic Request/Response Schemas
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid


# ---------- Enums ----------

class OverallStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    PARTIALLY_COMPLIANT = "PARTIALLY_COMPLIANT"


class FieldStatus(str, Enum):
    FOUND = "FOUND"
    MISSING = "MISSING"
    ILLEGIBLE = "ILLEGIBLE"


# ---------- Field Names ----------

class ComplianceFieldName(str, Enum):
    MANUFACTURER = "manufacturer_name_address"
    GENERIC_NAME = "generic_name"
    NET_QUANTITY = "net_quantity"
    DATE_OF_MFG = "date_of_manufacture"
    MRP = "mrp"
    CONSUMER_CARE = "consumer_care_details"


# ---------- Response Schemas ----------

class FieldResult(BaseModel):
    """Result for a single compliance field."""
    field_name: str = Field(..., description="Name of the compliance field")
    display_name: str = Field(..., description="Human-readable name")
    status: FieldStatus = Field(..., description="Extraction status")
    value: Optional[str] = Field(None, description="Extracted value, if found")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Extraction confidence 0-1")
    recommendation: Optional[str] = Field(
        None,
        description="Recommendation if the field is missing or illegible",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "field_name": "mrp",
                "display_name": "MRP (Maximum Retail Price)",
                "status": "FOUND",
                "value": "₹150",
                "confidence": 0.95,
                "recommendation": None,
            }
        }
    )


class ScanResponse(BaseModel):
    """Full response from a label scan."""
    scan_id: str = Field(..., description="Unique scan identifier")
    overall_status: OverallStatus = Field(..., description="Overall compliance status")
    fields: List[FieldResult] = Field(..., description="Per-field extraction results")
    raw_text: Optional[str] = Field(None, description="Raw OCR text output")
    ocr_engine: str = Field("paddle", description="OCR engine used")
    scanned_at: datetime = Field(..., description="Timestamp of scan")
    compliant_count: int = Field(0, description="Number of fields found")
    total_fields: int = Field(6, description="Total required fields")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "scan_id": "550e8400-e29b-41d4-a716-446655440000",
                "overall_status": "PARTIALLY_COMPLIANT",
                "compliant_count": 4,
                "total_fields": 6,
                "ocr_engine": "paddle",
                "scanned_at": "2026-09-07T16:00:00Z",
            }
        }
    )


class ScanHistoryItem(BaseModel):
    """Compact scan summary for history list views."""
    scan_id: str
    overall_status: OverallStatus
    compliant_count: int
    total_fields: int = 6
    scanned_at: datetime


class ScanHistoryResponse(BaseModel):
    """Paginated scan history response."""
    items: List[ScanHistoryItem]
    total: int
    page: int
    page_size: int


# ---------- Internal Extraction Schema ----------

class ExtractedField(BaseModel):
    """Internal model used during the extraction pipeline."""
    field_name: ComplianceFieldName
    found: bool = False
    value: Optional[str] = None
    confidence: float = 0.0
