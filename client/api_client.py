"""
Label Compliance Checker — API Client
Cross-platform client for interacting with the FastAPI backend.
Works with standard Python (zero external dependencies required).
"""
import os
import json
import uuid
import mimetypes
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, Union

DEFAULT_SERVER_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


class LabelCheckerClient:
    """
    Python client for the Legal Metrology Label Compliance Scanner API.
    """
    def __init__(self, base_url: Optional[str] = None, timeout: float = 60.0):
        self.base_url = (base_url or DEFAULT_SERVER_URL).rstrip("/")
        self.timeout = timeout

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def health_check(self) -> Dict[str, Any]:
        """Check backend service health and readiness."""
        url = self._url("/health")
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            raise ConnectionError(f"Cannot connect to backend at {self.base_url}: {e}")

    def scan_label(self, image: Union[str, bytes], filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload and scan a product label image for Legal Metrology PCR 2011 compliance.
        :param image: File path (str) or raw image bytes
        :param filename: Optional filename if bytes are provided
        """
        if isinstance(image, str):
            if not os.path.exists(image):
                raise FileNotFoundError(f"Image file not found: {image}")
            with open(image, "rb") as f:
                image_bytes = f.read()
            filename = os.path.basename(image)
        elif isinstance(image, (bytes, bytearray)):
            image_bytes = bytes(image)
            filename = filename or "label_image.jpg"
        else:
            raise TypeError("image must be either a file path (str) or raw bytes")

        # Build multipart/form-data payload using standard library
        boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
        mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        crlf = bytes([13, 10])
        body = bytearray()
        body.extend(b"--" + boundary.encode("utf-8") + crlf)
        body.extend(f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode("utf-8") + crlf)
        body.extend(f'Content-Type: {mime_type}'.encode("utf-8") + crlf + crlf)
        body.extend(image_bytes)
        body.extend(crlf + b"--" + boundary.encode("utf-8") + b"--" + crlf)

        url = self._url("/api/v1/scan")
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Content-Length": str(len(body)),
                "Accept": "application/json",
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            try:
                err_json = json.loads(err_body)
                msg = err_json.get("detail", err_body)
            except Exception:
                msg = err_body
            raise RuntimeError(f"Server returned error {e.code}: {msg}")
        except urllib.error.URLError as e:
            raise ConnectionError(f"Failed to connect to backend at {self.base_url}: {e}")

    def get_history(self, page: int = 1, page_size: int = 20, status: Optional[str] = None) -> Dict[str, Any]:
        """Get paginated scan history."""
        query_parts = [f"page={page}", f"page_size={page_size}"]
        if status:
            query_parts.append(f"status={urllib.request.quote(status.upper())}")
        query = "&".join(query_parts)
        url = self._url(f"/api/v1/scans?{query}")
        req = urllib.request.Request(url, headers={"Accept": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Server error {e.code}: {err_body}")
        except urllib.error.URLError as e:
            raise ConnectionError(f"Failed to connect to backend: {e}")

    def get_scan(self, scan_id: str) -> Dict[str, Any]:
        """Get detailed scan result by ID."""
        url = self._url(f"/api/v1/scans/{scan_id}")
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Server error {e.code}: {err_body}")
        except urllib.error.URLError as e:
            raise ConnectionError(f"Failed to connect to backend: {e}")
