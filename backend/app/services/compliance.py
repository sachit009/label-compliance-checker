"""
Label Compliance Checker — Compliance Validation Service
Validates extracted fields against Legal Metrology Rules, 2011.
"""
import logging
from typing import Dict, List

from app.models.schemas import (
    FieldResult,
    FieldStatus,
    OverallStatus,
    ComplianceFieldName,
)
from app.services.nlp_service import ExtractionResult
from app.config import settings

logger = logging.getLogger(__name__)

# Human-readable display names for each compliance field
FIELD_DISPLAY_NAMES = {
    ComplianceFieldName.MANUFACTURER: "Manufacturer / Packer / Importer Name & Address",
    ComplianceFieldName.GENERIC_NAME: "Common or Generic Name",
    ComplianceFieldName.NET_QUANTITY: "Net Quantity",
    ComplianceFieldName.DATE_OF_MFG: "Month & Year of Manufacture / Packing",
    ComplianceFieldName.MRP: "MRP (Maximum Retail Price, incl. all taxes)",
    ComplianceFieldName.CONSUMER_CARE: "Consumer Care Details",
}

# Recommendations for missing fields — per Legal Metrology Rules
FIELD_RECOMMENDATIONS = {
    ComplianceFieldName.MANUFACTURER: (
        "Rule 6(1)(a): The label must declare the name and complete address "
        "of the manufacturer, packer, or importer. Include company name, "
        "street address, city, state, and PIN code."
    ),
    ComplianceFieldName.GENERIC_NAME: (
        "Rule 6(1)(b): The label must clearly state the common or generic "
        "name of the commodity in the package."
    ),
    ComplianceFieldName.NET_QUANTITY: (
        "Rule 6(1)(c): The label must declare the net quantity of the "
        "commodity in standard units of weight (g/kg), measure (ml/L), "
        "or number. Use the metric system."
    ),
    ComplianceFieldName.DATE_OF_MFG: (
        "Rule 6(1)(d): The label must declare the month and year of "
        "manufacture, packing, or import. Format: MM/YYYY or Month YYYY."
    ),
    ComplianceFieldName.MRP: (
        "Rule 6(1)(e): The label must declare the retail sale price (MRP) "
        "inclusive of all taxes. Use '₹' or 'Rs.' prefix."
    ),
    ComplianceFieldName.CONSUMER_CARE: (
        "Rule 6(1)(f): The label must provide consumer care contact details "
        "including name, address, phone number, and email address of the "
        "person responsible for the product."
    ),
}


def check_compliance(
    extracted_fields: Dict[str, ExtractionResult],
) -> tuple[OverallStatus, List[FieldResult]]:
    """
    Validate extracted fields against Legal Metrology Rules, 2011.

    Args:
        extracted_fields: Dictionary mapping field names to ExtractionResult objects.

    Returns:
        Tuple of (overall_status, list of FieldResult objects).
    """
    field_results: List[FieldResult] = []
    found_count = 0
    total_fields = len(ComplianceFieldName)

    for field_enum in ComplianceFieldName:
        field_key = field_enum.value
        extraction = extracted_fields.get(field_key, ExtractionResult())

        # Determine field status
        if extraction.found and extraction.confidence >= settings.CONFIDENCE_THRESHOLD:
            status = FieldStatus.FOUND
            found_count += 1
            recommendation = None
        elif extraction.found and extraction.confidence < settings.CONFIDENCE_THRESHOLD:
            status = FieldStatus.ILLEGIBLE
            recommendation = (
                f"Field detected but confidence is low ({extraction.confidence:.0%}). "
                f"Verify legibility. {FIELD_RECOMMENDATIONS[field_enum]}"
            )
        else:
            status = FieldStatus.MISSING
            recommendation = FIELD_RECOMMENDATIONS[field_enum]

        field_results.append(
            FieldResult(
                field_name=field_key,
                display_name=FIELD_DISPLAY_NAMES[field_enum],
                status=status,
                value=extraction.value,
                confidence=round(extraction.confidence, 2),
                recommendation=recommendation,
            )
        )

    # Determine overall status
    if found_count == total_fields:
        overall_status = OverallStatus.COMPLIANT
    elif found_count == 0:
        overall_status = OverallStatus.NON_COMPLIANT
    else:
        overall_status = OverallStatus.PARTIALLY_COMPLIANT

    logger.info(
        f"Compliance check: {found_count}/{total_fields} fields found → {overall_status}"
    )

    return overall_status, field_results
