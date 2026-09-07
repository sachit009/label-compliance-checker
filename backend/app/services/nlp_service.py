"""
Label Compliance Checker — NLP Extraction Service
spaCy + Regex engine to extract 6 mandatory compliance fields from OCR text.
"""
import re
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Result of extracting a single compliance field."""
    found: bool = False
    value: Optional[str] = None
    confidence: float = 0.0


class NLPExtractor:
    """
    Extracts the 6 mandatory compliance fields from OCR text using
    spaCy Named Entity Recognition + custom regex patterns.
    """

    def __init__(self, spacy_model: str = "en_core_web_sm"):
        self._nlp = None
        try:
            import spacy
            logger.info(f"Loading spaCy model: {spacy_model}")
            try:
                self._nlp = spacy.load(spacy_model)
            except OSError:
                logger.warning(f"Model {spacy_model} not found. Downloading...")
                try:
                    spacy.cli.download(spacy_model)
                    self._nlp = spacy.load(spacy_model)
                except Exception as e:
                    logger.warning(f"Failed to download spaCy model: {e}")
                    self._nlp = None

            if self._nlp:
                self._add_custom_rules()
                logger.info("NLP Extractor ready with spaCy NER.")
            else:
                logger.info("NLP Extractor running in regex-only mode.")
        except (ImportError, Exception) as e:
            logger.info(f"spaCy not available ({e}). NLP Extractor running in regex-only mode.")

    def _add_custom_rules(self):
        """Add custom entity recognition rules for Indian product labels."""
        ruler = self._nlp.add_pipe("entity_ruler", before="ner")
        patterns = [
            # MRP patterns
            {"label": "MRP", "pattern": [
                {"LOWER": {"IN": ["mrp", "m.r.p", "m.r.p."]}},
            ]},
            {"label": "MRP", "pattern": [
                {"LOWER": "maximum"}, {"LOWER": "retail"}, {"LOWER": "price"},
            ]},
            # Net quantity keywords
            {"label": "NET_QTY", "pattern": [
                {"LOWER": {"IN": ["net", "nett"]}},
                {"LOWER": {"IN": ["wt", "wt.", "weight", "qty", "qty.", "quantity", "vol", "vol.", "volume", "content", "contents"]}},
            ]},
            # Manufacturing date keywords
            {"label": "MFG_DATE", "pattern": [
                {"LOWER": {"IN": ["mfg", "mfd", "mfg.", "mfd.", "manufactured", "manufacturing"]}},
            ]},
            {"label": "MFG_DATE", "pattern": [
                {"LOWER": {"IN": ["pkd", "pkd.", "packed", "packing"]}},
            ]},
            {"label": "MFG_DATE", "pattern": [
                {"LOWER": "date"}, {"LOWER": "of"},
                {"LOWER": {"IN": ["mfg", "manufacture", "manufacturing", "packing", "import"]}},
            ]},
            # Expiry / Best Before
            {"label": "EXP_DATE", "pattern": [
                {"LOWER": {"IN": ["exp", "exp.", "expiry", "expd"]}},
            ]},
            {"label": "EXP_DATE", "pattern": [
                {"LOWER": "best"}, {"LOWER": "before"},
            ]},
            {"label": "EXP_DATE", "pattern": [
                {"LOWER": "use"}, {"LOWER": "by"},
            ]},
            {"label": "EXP_DATE", "pattern": [
                {"LOWER": "bb"},
            ]},
        ]
        ruler.add_patterns(patterns)

    def extract_all(self, text: str) -> Dict[str, ExtractionResult]:
        """
        Extract all 6 mandatory fields from the given text.

        Returns:
            Dictionary mapping field names to ExtractionResult objects.
        """
        return {
            "manufacturer_name_address": self.extract_manufacturer(text),
            "generic_name": self.extract_generic_name(text),
            "net_quantity": self.extract_net_quantity(text),
            "date_of_manufacture": self.extract_date(text),
            "mrp": self.extract_mrp(text),
            "consumer_care_details": self.extract_consumer_care(text),
        }

    # ── 1. Manufacturer Name & Address ──────────────────────────────

    def extract_manufacturer(self, text: str) -> ExtractionResult:
        """
        Extract manufacturer/packer/importer name and address.
        Strategy: Look for keywords like 'Mfg by', 'Manufactured by', etc.
        then extract the following text. Also uses spaCy ORG + GPE entities.
        """
        # Keyword anchors for manufacturer
        mfg_patterns = [
            r"(?:Mfg\.?\s*(?:by|at)?|Manufactured\s*(?:by|at)?|Packed\s*(?:by|at)?|"
            r"Imported\s*(?:by)?|Marketed\s*(?:by)?|Distributed\s*(?:by)?)"
            r"[\s:.\-]*(.+?)(?:\n|Mfg|Packed|MRP|Net|Best|Exp|Use\s*by|$)",
        ]

        for pattern in mfg_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                value = match.group(1).strip()
                # Clean up: remove trailing punctuation artifacts
                value = re.sub(r"[,.\s]+$", "", value)
                if len(value) > 5:  # Minimum meaningful length
                    return ExtractionResult(
                        found=True,
                        value=value,
                        confidence=0.85,
                    )

        # Fallback: use spaCy ORG entities combined with address indicators if available
        if self._nlp:
            doc = self._nlp(text)
            orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
            gpes = [ent.text for ent in doc.ents if ent.label_ in ("GPE", "LOC")]

            # Look for PIN code pattern (Indian postal code)
            pin_match = re.search(r"\b\d{6}\b", text)

            if orgs:
                address_parts = []
                if orgs:
                    address_parts.append(orgs[0])
                if gpes:
                    address_parts.extend(gpes[:2])
                if pin_match:
                    address_parts.append(f"PIN: {pin_match.group()}")

                combined = ", ".join(address_parts)
                return ExtractionResult(found=True, value=combined, confidence=0.6)

        return ExtractionResult(found=False, confidence=0.0)

    # ── 2. Generic / Common Name ────────────────────────────────────

    def extract_generic_name(self, text: str) -> ExtractionResult:
        """
        Extract the generic/common name of the commodity.
        Strategy: Look for explicit 'Product:' / 'Name:' anchors,
        or use the first prominent text line.
        """
        # Explicit anchors
        name_patterns = [
            r"(?:Product\s*(?:Name)?|Common\s*Name|Generic\s*Name|Item)"
            r"[\s:.\-]+(.+?)(?:\n|$)",
        ]

        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                value = re.sub(r"[,.\s]+$", "", value)
                if len(value) > 2:
                    return ExtractionResult(found=True, value=value, confidence=0.9)

        # Fallback: first non-trivial line (product labels often start with name)
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        for line in lines[:3]:  # Check first 3 lines
            # Skip lines that look like other fields
            if re.search(
                r"(?:MRP|M\.R\.P|Net|Mfg|Packed|Exp|Best|Consumer|Customer|"
                r"Batch|Lot|FSSAI|Lic|Ingr|Nutritional)",
                line,
                re.IGNORECASE,
            ):
                continue
            # Skip very short lines or lines that are mostly numbers
            if len(line) > 3 and not re.match(r"^[\d\s.,-]+$", line):
                return ExtractionResult(found=True, value=line, confidence=0.5)

        return ExtractionResult(found=False, confidence=0.0)

    # ── 3. Net Quantity ─────────────────────────────────────────────

    def extract_net_quantity(self, text: str) -> ExtractionResult:
        """
        Extract net quantity in standard units.
        Strategy: Regex for quantity + unit patterns.
        """
        # Pattern: number followed by a unit
        qty_pattern = (
            r"(?:Net\s*(?:Wt\.?|Weight|Qty\.?|Quantity|Vol\.?|Volume|Content[s]?)"
            r"[\s:.\-]*)?(\d+\.?\d*)\s*"
            r"(g(?:m|rams?)?|kg|ml|mL|l(?:itre)?|L|cm|mm|m|oz|pcs?|pieces?|units?|nos?|capsules?|tablets?)\b"
        )

        matches = re.findall(qty_pattern, text, re.IGNORECASE)

        if matches:
            # Prefer match near "Net" keyword
            net_match = re.search(
                r"(?:Net|Nett)\s*(?:Wt\.?|Weight|Qty\.?|Quantity|Vol\.?|Volume|Content[s]?)"
                r"[\s:.\-]*(\d+\.?\d*)\s*"
                r"(g(?:m|rams?)?|kg|ml|mL|l(?:itre)?|L|cm|mm|m)\b",
                text,
                re.IGNORECASE,
            )

            if net_match:
                value = f"{net_match.group(1)} {net_match.group(2)}"
                return ExtractionResult(found=True, value=value, confidence=0.95)

            # Use first match
            value = f"{matches[0][0]} {matches[0][1]}"
            return ExtractionResult(found=True, value=value, confidence=0.75)

        return ExtractionResult(found=False, confidence=0.0)

    # ── 4. Date of Manufacture / Packing ────────────────────────────

    def extract_date(self, text: str) -> ExtractionResult:
        """
        Extract month and year of manufacture, packing, or import.
        Strategy: Regex for date patterns near MFG/MFD/PKD keywords.
        """
        # Date formats to detect
        date_patterns = [
            # Near MFG/PKD keyword (including "Mfg Date:", "PKD Date:", "Date of Mfg:")
            (
                r"(?:(?:MFG|MFD|Mfg|Mfd|PKD|Pkd|Packed|Manufactured)(?:\s*(?:Date|Dt\.?))?|Date\s*of\s*(?:Mfg|Manufacture|Manufacturing|Packing|Import))"
                r"[\s:.\/\-]*"
                r"(\d{1,2}[\s]*[\/\-\.]\s*\d{1,2}[\s]*[\/\-\.]\s*\d{2,4}|\w{3,9}[\s,]*\d{2,4}|\d{1,2}[\s]*[\/\-\.]\s*\d{2,4})",
                0.95,
            ),
            # Standalone date pattern MM/YYYY or MM-YYYY
            (
                r"(?:MFG|MFD|PKD)(?:\s*(?:Date|Dt\.?))?[\s:.]*(\d{1,2}\s*[\/\-]\s*\d{4})",
                0.9,
            ),
            # Month name + Year
            (
                r"(?:MFG|MFD|PKD|Manufactured|Packed)(?:\s*(?:Date|Dt\.?))?[\s:.]*"
                r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*[\s,.\-]*\d{4})",
                0.9,
            ),
        ]

        for pattern, confidence in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                value = re.sub(r"[,.\s]+$", "", value)
                if len(value) >= 4:
                    return ExtractionResult(found=True, value=value, confidence=confidence)

        # Fallback: use spaCy DATE entities if available
        if self._nlp:
            doc = self._nlp(text)
            dates = [ent.text for ent in doc.ents if ent.label_ == "DATE"]
            if dates:
                return ExtractionResult(found=True, value=dates[0], confidence=0.5)

        return ExtractionResult(found=False, confidence=0.0)

    # ── 5. MRP (Maximum Retail Price) ───────────────────────────────

    def extract_mrp(self, text: str) -> ExtractionResult:
        """
        Extract retail sale price (MRP inclusive of all taxes).
        Strategy: Regex for MRP/M.R.P followed by currency symbol and digits.
        """
        mrp_patterns = [
            # MRP Rs. 150 or MRP ₹150 or MRP: Rs 150.00
            (
                r"(?:MRP|M\.?\s*R\.?\s*P\.?|Max(?:imum)?\s*Retail\s*Price)"
                r"[\s:.\-]*(?:Rs\.?|₹|INR)?\s*(\d+[\d,]*\.?\d*)",
                0.95,
            ),
            # Rs. 150 (MRP) or ₹150 (incl. all taxes)
            (
                r"(?:Rs\.?|₹|INR)\s*(\d+[\d,]*\.?\d*)\s*(?:\(?\s*(?:incl|inclusive|MRP))",
                0.85,
            ),
            # Price: 150 or Cost: Rs 150
            (
                r"(?:Price|Cost|SP)[\s:.\-]*(?:Rs\.?|₹|INR)?\s*(\d+[\d,]*\.?\d*)",
                0.7,
            ),
        ]

        for pattern, confidence in mrp_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(",", "")
                try:
                    price = float(price_str)
                    if price > 0:
                        return ExtractionResult(
                            found=True,
                            value=f"₹{price_str}",
                            confidence=confidence,
                        )
                except ValueError:
                    continue

        return ExtractionResult(found=False, confidence=0.0)

    # ── 6. Consumer Care Details ────────────────────────────────────

    def extract_consumer_care(self, text: str) -> ExtractionResult:
        """
        Extract consumer care details (name, address, phone, email).
        Strategy: Find phone numbers, emails, and text near
        'Consumer Care' / 'Customer Care' / 'Helpline' keywords.
        """
        details: List[str] = []
        confidence = 0.0

        # Look for consumer care section
        care_section = re.search(
            r"(?:Consumer\s*Care|Customer\s*Care|Helpline|Toll\s*Free|"
            r"For\s*(?:Complaints|Queries|Feedback)|Contact\s*Us)"
            r"[\s:.\-]*(.+?)(?:\n\n|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )

        if care_section:
            section_text = care_section.group(0)
            confidence = 0.7
        else:
            section_text = text
            confidence = 0.4

        # Extract phone numbers (Indian format: 10-11 digits, with optional prefix)
        phone_patterns = [
            r"\b(?:\+91[\s\-]?)?[6-9]\d{9}\b",  # Indian mobile
            r"\b1800[\s\-]?\d{3}[\s\-]?\d{3,4}\b",  # Toll-free
            r"\b0\d{2,4}[\s\-]?\d{6,8}\b",  # Landline with STD code
        ]

        phones = []
        for pattern in phone_patterns:
            found_phones = re.findall(pattern, section_text)
            phones.extend(found_phones)

        if phones:
            details.append(f"Phone: {', '.join(phones[:2])}")
            confidence = max(confidence, 0.8)

        # Extract email addresses
        emails = re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", section_text, re.IGNORECASE)
        if emails:
            details.append(f"Email: {', '.join(emails[:2])}")
            confidence = max(confidence, 0.85)

        # Extract website URLs
        urls = re.findall(r"(?:www\.[\w.-]+\.\w+|https?://[\w./-]+)", section_text, re.IGNORECASE)
        if urls:
            details.append(f"Website: {', '.join(urls[:1])}")

        if details:
            return ExtractionResult(
                found=True,
                value="; ".join(details),
                confidence=confidence,
            )

        return ExtractionResult(found=False, confidence=0.0)
