"""
Label Compliance Checker — OCR Service
Dual-engine OCR abstraction: PaddleOCR (default) + Google Cloud Vision (optional).
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class OCREngine(ABC):
    """Abstract base class for OCR engines."""

    @abstractmethod
    def extract_text(self, image_bytes: bytes) -> str:
        """
        Extract text from raw image bytes.

        Args:
            image_bytes: Raw bytes of the image (JPEG, PNG, etc.)

        Returns:
            Concatenated text string with spatial ordering preserved.
        """
        pass

    @abstractmethod
    def name(self) -> str:
        """Return the engine name identifier."""
        pass


class PaddleOCREngine(OCREngine):
    """
    PaddleOCR-based text extraction.
    Loaded once at startup and reused for all requests.
    """

    def __init__(self):
        try:
            from paddleocr import PaddleOCR

            logger.info("Initializing PaddleOCR engine (this may take a moment)...")
            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang="en",
                show_log=False,
                use_gpu=False,  # Set True if GPU is available
            )
            logger.info("PaddleOCR engine ready.")
        except (ImportError, Exception) as e:
            logger.warning(
                f"PaddleOCR not available or failed to load ({e}). "
                "OCR extraction will return empty text unless a cloud engine or mock is used."
            )
            self._ocr = None

    def name(self) -> str:
        return "paddle"

    def extract_text(self, image_bytes: bytes) -> str:
        # Decode image bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError("Failed to decode image. Ensure the file is a valid image.")

        if self._ocr is None:
            logger.warning("PaddleOCR engine is not loaded; returning empty extracted text.")
            return ""

        # Run OCR
        results = self._ocr.ocr(image, cls=True)

        if not results or not results[0]:
            logger.warning("PaddleOCR returned no results.")
            return ""

        # Sort results by vertical position (top to bottom), then horizontal
        lines = []
        for line in results[0]:
            bbox = line[0]
            text = line[1][0]
            confidence = line[1][1]
            # Use top-left y coordinate for sorting
            y_pos = bbox[0][1]
            x_pos = bbox[0][0]
            lines.append((y_pos, x_pos, text, confidence))

        # Sort by y (top→bottom), then x (left→right)
        lines.sort(key=lambda l: (l[0], l[1]))

        # Group lines by approximate y-position (within 15px = same line)
        grouped_lines = []
        current_group = []
        last_y = None

        for y, x, text, conf in lines:
            if last_y is not None and abs(y - last_y) > 15:
                # New line group
                current_group.sort(key=lambda t: t[0])  # Sort by x within line
                grouped_lines.append(" ".join(t[1] for t in current_group))
                current_group = []
            current_group.append((x, text))
            last_y = y

        if current_group:
            current_group.sort(key=lambda t: t[0])
            grouped_lines.append(" ".join(t[1] for t in current_group))

        return "\n".join(grouped_lines)


class CloudVisionEngine(OCREngine):
    """
    Google Cloud Vision API-based text extraction.
    Requires GOOGLE_APPLICATION_CREDENTIALS to be set.
    """

    def __init__(self):
        try:
            from google.cloud import vision
            logger.info("Initializing Google Cloud Vision engine...")
            self._client = vision.ImageAnnotatorClient()
            self._vision = vision
            logger.info("Google Cloud Vision engine ready.")
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize Google Cloud Vision: {e}. "
                "Ensure google-cloud-vision is installed and "
                "GOOGLE_APPLICATION_CREDENTIALS is set."
            )

    def name(self) -> str:
        return "gcloud_vision"

    def extract_text(self, image_bytes: bytes) -> str:
        image = self._vision.Image(content=image_bytes)

        # Use TEXT_DETECTION for product labels (sparse text)
        response = self._client.text_detection(image=image)

        if response.error.message:
            raise RuntimeError(
                f"Cloud Vision API error: {response.error.message}"
            )

        texts = response.text_annotations
        if not texts:
            logger.warning("Cloud Vision returned no text.")
            return ""

        # First annotation contains the full text
        return texts[0].description


class MockOCREngine(OCREngine):
    """
    Mock OCR engine for local testing, rapid CI, and developer preview.
    Extracts a representative Indian packaged commodity label text.
    """

    def name(self) -> str:
        return "mock"

    def extract_text(self, image_bytes: bytes) -> str:
        logger.info("MockOCREngine extracting simulated label text for testing.")
        return (
            "Himalaya Wellness Company\n"
            "Plot No. 19, Sector 7, IMT Manesar, Gurugram, Haryana - 122050\n"
            "Generic Name: Organic Green Tea (Premium Whole Leaf)\n"
            "Net Wt: 250 g\n"
            "Mfg Date: 03/2026\n"
            "Best Before: 24 months from Mfg Date\n"
            "MRP Rs. 350.00 (Inclusive of all taxes)\n"
            "For Consumer Care Complaints:\n"
            "Consumer Care Cell: care@himalaya.com, Toll Free: 1800-208-1930\n"
        )


# ---------- Factory ----------

_engine_cache: Optional[OCREngine] = None


def get_ocr_engine(engine_name: str = "paddle") -> OCREngine:
    """
    Factory function to get or create an OCR engine instance.
    Engines are cached as singletons for the application lifetime.

    Args:
        engine_name: "paddle", "gcloud_vision", or "mock"

    Returns:
        An OCREngine instance.
    """
    global _engine_cache

    if _engine_cache is not None and _engine_cache.name() == engine_name:
        return _engine_cache

    if engine_name == "mock":
        _engine_cache = MockOCREngine()
    elif engine_name == "paddle":
        engine = PaddleOCREngine()
        if engine._ocr is None:
            logger.info("PaddleOCR not installed locally. Using MockOCREngine fallback.")
            _engine_cache = MockOCREngine()
        else:
            _engine_cache = engine
    elif engine_name == "gcloud_vision":
        _engine_cache = CloudVisionEngine()
    else:
        raise ValueError(
            f"Unknown OCR engine: '{engine_name}'. Use 'paddle', 'gcloud_vision', or 'mock'."
        )

    return _engine_cache
