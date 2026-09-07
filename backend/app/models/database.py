"""
Label Compliance Checker — SQLAlchemy Database Models
Compatible with both SQLite (local dev) and PostgreSQL (production).
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Float, DateTime, ForeignKey,
)
from sqlalchemy.orm import DeclarativeBase, relationship
import enum


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class OverallStatus(str, enum.Enum):
    """Overall compliance status of a scan."""
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    PARTIALLY_COMPLIANT = "PARTIALLY_COMPLIANT"


class FieldStatus(str, enum.Enum):
    """Status of an individual compliance field."""
    FOUND = "FOUND"
    MISSING = "MISSING"
    ILLEGIBLE = "ILLEGIBLE"


class Scan(Base):
    """Represents a single label scan and its overall result."""
    __tablename__ = "scans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    image_path = Column(String(500), nullable=True)
    raw_ocr_text = Column(Text, nullable=True)
    overall_status = Column(
        String(30),
        nullable=False,
        default=OverallStatus.NON_COMPLIANT.value,
    )
    ocr_engine_used = Column(String(50), nullable=False, default="paddle")
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationship to compliance fields
    fields = relationship(
        "ComplianceField",
        back_populates="scan",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self):
        return f"<Scan {self.id} — {self.overall_status}>"


class ComplianceField(Base):
    """Represents the extraction result for a single compliance field."""
    __tablename__ = "compliance_fields"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id = Column(
        String(36),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
    )
    field_name = Column(String(100), nullable=False)
    status = Column(
        String(20),
        nullable=False,
        default=FieldStatus.MISSING.value,
    )
    extracted_value = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True, default=0.0)
    recommendation = Column(Text, nullable=True)

    # Relationship back to scan
    scan = relationship("Scan", back_populates="fields")

    def __repr__(self):
        return f"<ComplianceField {self.field_name}: {self.status}>"
