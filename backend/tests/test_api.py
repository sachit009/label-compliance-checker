import pytest
import pytest_asyncio
import io
from PIL import Image
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.config import settings
from app.db import engine
from app.models.database import Base

@pytest_asyncio.fixture(autouse=True)
async def setup_db(monkeypatch):
    monkeypatch.setattr(settings, "OCR_ENGINE", "mock")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

@pytest.mark.asyncio
async def test_scan_and_history():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create a mock 100x100 PNG
        buf = io.BytesIO()
        img = Image.new("RGB", (100, 100), color=(255, 255, 255))
        img.save(buf, format="PNG")
        buf.seek(0)

        # POST /api/v1/scan
        files = {"file": ("label.png", buf, "image/png")}
        resp = await ac.post("/api/v1/scan", files=files)
        assert resp.status_code == 200
        scan_data = resp.json()
        assert "scan_id" in scan_data
        assert "overall_status" in scan_data
        assert len(scan_data["fields"]) == 6

        # GET /api/v1/scans with status query (verifying DBOverallStatus fix)
        resp_history = await ac.get(f"/api/v1/scans?status={scan_data['overall_status']}")
        assert resp_history.status_code == 200
        history_data = resp_history.json()
        assert "items" in history_data
        assert history_data["total"] >= 1

        # GET /api/v1/scans/{scan_id}
        resp_detail = await ac.get(f"/api/v1/scans/{scan_data['scan_id']}")
        assert resp_detail.status_code == 200
        assert resp_detail.json()["scan_id"] == scan_data["scan_id"]
