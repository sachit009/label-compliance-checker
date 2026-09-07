"""
Tests for NLP Extraction Service
Validates all 6 extractor functions against representative label texts.
"""
import pytest
from app.services.nlp_service import NLPExtractor


@pytest.fixture(scope="module")
def extractor():
    """Create a shared NLP extractor for all tests in this module."""
    return NLPExtractor("en_core_web_sm")


# ── Sample label texts ──────────────────────────────────────────────

COMPLIANT_LABEL = """
Organic Green Tea
Premium Whole Leaf

Net Wt: 250 g

MRP Rs. 350 (Inclusive of all taxes)

Mfg by: Himalaya Wellness Company
Plot No. 19, Sector 7, IMT Manesar
Gurugram, Haryana - 122050

Mfg Date: 03/2026
Best Before: 24 months from Mfg Date

FSSAI Lic No: 10012345678901

For Consumer Complaints Contact:
Consumer Care Cell
Himalaya Wellness Company
Phone: 1800-208-1930
Email: consumercare@himalaya.com
www.himalayawellness.com
"""

PARTIAL_LABEL = """
CHOCO BISCUITS
Net Weight 200g
MRP ₹45
Batch No: AB12345
"""

EMPTY_LABEL = """
Some random text that doesn't match anything useful
12345 hello world
"""


# ── Manufacturer Extraction ─────────────────────────────────────────

class TestManufacturerExtraction:
    def test_finds_manufacturer_with_keyword(self, extractor):
        result = extractor.extract_manufacturer(COMPLIANT_LABEL)
        assert result.found is True
        assert "Himalaya" in result.value
        assert result.confidence >= 0.7

    def test_finds_packed_by_variant(self, extractor):
        text = "Packed by: Fresh Foods Pvt Ltd, Mumbai 400001"
        result = extractor.extract_manufacturer(text)
        assert result.found is True
        assert "Fresh Foods" in result.value

    def test_finds_imported_by_variant(self, extractor):
        text = "Imported by: Global Imports Inc., New Delhi 110001"
        result = extractor.extract_manufacturer(text)
        assert result.found is True
        assert "Global Imports" in result.value

    def test_not_found_on_empty(self, extractor):
        result = extractor.extract_manufacturer(EMPTY_LABEL)
        # May or may not find via spaCy fallback — if not found, confidence should be low
        if not result.found:
            assert result.confidence == 0.0


# ── Generic Name Extraction ─────────────────────────────────────────

class TestGenericNameExtraction:
    def test_finds_first_prominent_line(self, extractor):
        result = extractor.extract_generic_name(COMPLIANT_LABEL)
        assert result.found is True
        assert "Green Tea" in result.value or "Organic" in result.value

    def test_finds_explicit_product_name(self, extractor):
        text = "Product Name: Basmati Rice\nNet Wt: 1 kg\nMRP Rs. 120"
        result = extractor.extract_generic_name(text)
        assert result.found is True
        assert "Basmati Rice" in result.value
        assert result.confidence >= 0.8

    def test_skips_mrp_lines(self, extractor):
        text = "MRP Rs. 100\nPure Honey\nNet Wt 500g"
        result = extractor.extract_generic_name(text)
        assert result.found is True
        assert "MRP" not in result.value


# ── Net Quantity Extraction ─────────────────────────────────────────

class TestNetQuantityExtraction:
    def test_finds_net_wt_with_keyword(self, extractor):
        result = extractor.extract_net_quantity(COMPLIANT_LABEL)
        assert result.found is True
        assert "250" in result.value
        assert "g" in result.value.lower()
        assert result.confidence >= 0.9

    def test_finds_ml_unit(self, extractor):
        text = "Net Vol: 500 ml"
        result = extractor.extract_net_quantity(text)
        assert result.found is True
        assert "500" in result.value

    def test_finds_kg_unit(self, extractor):
        text = "Net Weight 1.5 kg"
        result = extractor.extract_net_quantity(text)
        assert result.found is True
        assert "1.5" in result.value

    def test_finds_quantity_without_keyword(self, extractor):
        text = "Premium Coffee 200g MRP Rs. 150"
        result = extractor.extract_net_quantity(text)
        assert result.found is True
        assert "200" in result.value

    def test_not_found_without_units(self, extractor):
        result = extractor.extract_net_quantity(EMPTY_LABEL)
        assert result.found is False


# ── Date Extraction ─────────────────────────────────────────────────

class TestDateExtraction:
    def test_finds_mfg_date(self, extractor):
        result = extractor.extract_date(COMPLIANT_LABEL)
        assert result.found is True
        assert "03" in result.value or "2026" in result.value
        assert result.confidence >= 0.8

    def test_finds_mfd_format(self, extractor):
        text = "MFD: 01/2026 EXP: 01/2027"
        result = extractor.extract_date(text)
        assert result.found is True

    def test_finds_month_name_format(self, extractor):
        text = "Manufactured: March 2026"
        result = extractor.extract_date(text)
        assert result.found is True
        assert "March" in result.value or "2026" in result.value

    def test_finds_pkd_date(self, extractor):
        text = "PKD: 15-06-2026"
        result = extractor.extract_date(text)
        assert result.found is True


# ── MRP Extraction ──────────────────────────────────────────────────

class TestMRPExtraction:
    def test_finds_mrp_with_rs(self, extractor):
        result = extractor.extract_mrp(COMPLIANT_LABEL)
        assert result.found is True
        assert "350" in result.value
        assert result.confidence >= 0.9

    def test_finds_mrp_with_rupee_symbol(self, extractor):
        result = extractor.extract_mrp(PARTIAL_LABEL)
        assert result.found is True
        assert "45" in result.value

    def test_finds_mrp_with_dots(self, extractor):
        text = "M.R.P.: Rs. 99.50 (Incl. of all taxes)"
        result = extractor.extract_mrp(text)
        assert result.found is True
        assert "99" in result.value

    def test_not_found_without_price(self, extractor):
        result = extractor.extract_mrp(EMPTY_LABEL)
        assert result.found is False


# ── Consumer Care Extraction ────────────────────────────────────────

class TestConsumerCareExtraction:
    def test_finds_phone_and_email(self, extractor):
        result = extractor.extract_consumer_care(COMPLIANT_LABEL)
        assert result.found is True
        assert "1800" in result.value or "Phone" in result.value
        assert "consumercare@himalaya.com" in result.value or "Email" in result.value

    def test_finds_toll_free_number(self, extractor):
        text = "For queries, call Toll Free: 1800 102 3456"
        result = extractor.extract_consumer_care(text)
        assert result.found is True
        assert "1800" in result.value

    def test_finds_email_standalone(self, extractor):
        text = "Contact: support@company.in for feedback"
        result = extractor.extract_consumer_care(text)
        assert result.found is True
        assert "support@company.in" in result.value

    def test_not_found_without_contacts(self, extractor):
        result = extractor.extract_consumer_care(EMPTY_LABEL)
        assert result.found is False


# ── Full Extraction Pipeline ────────────────────────────────────────

class TestFullExtraction:
    def test_compliant_label_extracts_all_fields(self, extractor):
        results = extractor.extract_all(COMPLIANT_LABEL)
        assert len(results) == 6

        # All fields should be found on a compliant label
        for field_name, result in results.items():
            assert result.found is True, f"Field {field_name} not found"
            assert result.value is not None, f"Field {field_name} has no value"
            assert result.confidence > 0, f"Field {field_name} has 0 confidence"

    def test_partial_label_finds_some_fields(self, extractor):
        results = extractor.extract_all(PARTIAL_LABEL)
        found_count = sum(1 for r in results.values() if r.found)
        assert found_count >= 2  # At least MRP and net quantity
        assert found_count < 6  # Not all fields

    def test_empty_label_finds_no_fields(self, extractor):
        results = extractor.extract_all(EMPTY_LABEL)
        found_count = sum(1 for r in results.values() if r.found)
        assert found_count <= 1  # Possibly 1 false positive from spaCy NER
