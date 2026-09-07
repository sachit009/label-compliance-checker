"""
Tests for Compliance Validation Service
Verifies correct status determination and recommendation generation.
"""
import pytest
from app.services.nlp_service import ExtractionResult
from app.services.compliance import check_compliance
from app.models.schemas import OverallStatus, FieldStatus


def _make_extraction_results(
    manufacturer=None,
    generic_name=None,
    net_quantity=None,
    date_of_mfg=None,
    mrp=None,
    consumer_care=None,
):
    """Helper to create extraction results with defaults."""
    default = ExtractionResult(found=False, value=None, confidence=0.0)
    return {
        "manufacturer_name_address": manufacturer or default,
        "generic_name": generic_name or default,
        "net_quantity": net_quantity or default,
        "date_of_manufacture": date_of_mfg or default,
        "mrp": mrp or default,
        "consumer_care_details": consumer_care or default,
    }


class TestComplianceStatus:
    def test_all_fields_found_is_compliant(self):
        found = ExtractionResult(found=True, value="test", confidence=0.9)
        fields = _make_extraction_results(
            manufacturer=found,
            generic_name=found,
            net_quantity=found,
            date_of_mfg=found,
            mrp=found,
            consumer_care=found,
        )
        overall, results = check_compliance(fields)
        assert overall == OverallStatus.COMPLIANT
        assert all(r.status == FieldStatus.FOUND for r in results)

    def test_no_fields_found_is_non_compliant(self):
        fields = _make_extraction_results()
        overall, results = check_compliance(fields)
        assert overall == OverallStatus.NON_COMPLIANT
        assert all(r.status == FieldStatus.MISSING for r in results)

    def test_some_fields_found_is_partially_compliant(self):
        found = ExtractionResult(found=True, value="test", confidence=0.9)
        fields = _make_extraction_results(
            mrp=found,
            net_quantity=found,
        )
        overall, results = check_compliance(fields)
        assert overall == OverallStatus.PARTIALLY_COMPLIANT

    def test_low_confidence_marks_illegible(self):
        low_conf = ExtractionResult(found=True, value="blurry", confidence=0.3)
        fields = _make_extraction_results(mrp=low_conf)
        overall, results = check_compliance(fields)

        # Find the MRP field result
        mrp_result = next(r for r in results if r.field_name == "mrp")
        assert mrp_result.status == FieldStatus.ILLEGIBLE
        assert "confidence" in mrp_result.recommendation.lower()


class TestFieldResults:
    def test_found_fields_have_no_recommendation(self):
        found = ExtractionResult(found=True, value="₹150", confidence=0.95)
        fields = _make_extraction_results(mrp=found)
        _, results = check_compliance(fields)

        mrp_result = next(r for r in results if r.field_name == "mrp")
        assert mrp_result.recommendation is None

    def test_missing_fields_have_recommendation(self):
        fields = _make_extraction_results()
        _, results = check_compliance(fields)

        for result in results:
            assert result.recommendation is not None
            assert "Rule" in result.recommendation

    def test_all_six_fields_present_in_results(self):
        fields = _make_extraction_results()
        _, results = check_compliance(fields)
        assert len(results) == 6

        expected_fields = {
            "manufacturer_name_address",
            "generic_name",
            "net_quantity",
            "date_of_manufacture",
            "mrp",
            "consumer_care_details",
        }
        actual_fields = {r.field_name for r in results}
        assert actual_fields == expected_fields

    def test_display_names_are_human_readable(self):
        fields = _make_extraction_results()
        _, results = check_compliance(fields)

        for result in results:
            assert len(result.display_name) > 5
            assert result.display_name != result.field_name

    def test_confidence_is_rounded(self):
        found = ExtractionResult(found=True, value="test", confidence=0.8567)
        fields = _make_extraction_results(mrp=found)
        _, results = check_compliance(fields)

        mrp_result = next(r for r in results if r.field_name == "mrp")
        # Check confidence has at most 2 decimal places
        assert mrp_result.confidence == 0.86
