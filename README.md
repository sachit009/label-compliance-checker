# 🏷️ Label Compliance Checker

**Verify product labels against India's Legal Metrology (Packaged Commodities) Rules, 2011**

A full-stack application that scans product labels using OCR, extracts text with NLP, and validates compliance with all 6 mandatory fields required under Indian law.

---

## 🏗️ Architecture

```
┌──────────────┐      Multipart      ┌───────────────┐
│  Flutter App  │ ──── Upload ──────▶ │  FastAPI       │
│  (Mobile)     │                     │  Backend       │
│               │ ◀── JSON ───────── │                │
└──────────────┘                     └───────┬───────┘
                                             │
                            ┌────────────────┼────────────────┐
                            ▼                ▼                ▼
                     ┌────────────┐   ┌────────────┐   ┌────────────┐
                     │ PaddleOCR  │   │ spaCy+Regex│   │ PostgreSQL │
                     │ / Cloud    │   │ NLP Engine │   │ Database   │
                     │ Vision     │   │            │   │            │
                     └────────────┘   └────────────┘   └────────────┘
```

## ✅ The 6 Compliance Fields

| # | Field | Detection Method |
|---|-------|-----------------|
| 1 | **Manufacturer Name & Address** | spaCy NER (ORG/GPE) + keyword anchors |
| 2 | **Generic / Common Name** | Position-based + explicit anchors |
| 3 | **Net Quantity** | Regex: quantity + standard units |
| 4 | **Month & Year of Manufacture** | Regex near MFG/PKD keywords |
| 5 | **MRP (incl. all taxes)** | Regex: MRP + ₹/Rs + digits |
| 6 | **Consumer Care Details** | Phone/email regex + keyword context |

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Flutter SDK (for the mobile app)

### 1. Start the Backend

```bash
# Clone the project
cd label-compliance-checker

# Copy environment file
cp backend/.env.example backend/.env

# Start PostgreSQL + Backend with Docker Compose
docker-compose up --build
```

The API will be available at **http://localhost:8000**
- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### 2. Run the Flutter App

```bash
cd frontend/label_checker

# Install dependencies
flutter pub get

# Run on connected device/emulator
flutter run
```

> **Note:** If running on an Android emulator, the default API URL is
> `http://10.0.2.2:8000`. For a physical device, update the base URL
> in `lib/services/api_service.dart` to your machine's IP address.

---

## 🧪 Testing

### Backend Tests
```bash
cd backend

# Install test dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Run tests
python -m pytest tests/ -v
```

### API Testing (via Swagger)
1. Open http://localhost:8000/docs
2. Use the `POST /api/v1/scan` endpoint
3. Upload a product label image
4. View the compliance results

---

## 📁 Project Structure

```
label-compliance-checker/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Environment-driven settings
│   │   ├── db.py                # Async SQLAlchemy connection
│   │   ├── models/
│   │   │   ├── database.py      # SQLAlchemy models
│   │   │   └── schemas.py       # Pydantic schemas
│   │   ├── services/
│   │   │   ├── ocr_service.py   # PaddleOCR + Cloud Vision
│   │   │   ├── nlp_service.py   # spaCy + Regex extraction
│   │   │   └── compliance.py    # Compliance validation
│   │   └── routers/
│   │       └── scan.py          # API endpoints
│   ├── tests/
│   │   ├── test_nlp_service.py  # NLP extraction tests
│   │   └── test_compliance.py   # Compliance logic tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── label_checker/
│       ├── lib/
│       │   ├── main.dart
│       │   ├── theme/           # Premium dark theme
│       │   ├── screens/         # Home, Camera, Result, History
│       │   ├── models/          # Data models
│       │   ├── services/        # API client
│       │   └── widgets/         # Compliance card, status tile
│       └── pubspec.yaml
├── docker-compose.yml
└── README.md
```

---

## ⚙️ Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OCR_ENGINE` | `paddle` | OCR engine: `paddle` or `gcloud_vision` |
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection string |
| `MAX_IMAGE_SIZE_MB` | `10` | Maximum upload size |
| `GOOGLE_APPLICATION_CREDENTIALS` | — | Path to GCP service account JSON |

### Switching to Google Cloud Vision
```bash
# In .env or docker-compose.yml
OCR_ENGINE=gcloud_vision
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

---

## 📜 Legal Reference

This tool validates labels against the **Legal Metrology (Packaged Commodities) Rules, 2011**, specifically Rule 6(1) which mandates:

- (a) Name and address of manufacturer/packer/importer
- (b) Common or generic name of commodity
- (c) Net quantity in standard units
- (d) Month and year of manufacture/packing/import
- (e) Retail sale price (MRP inclusive of all taxes)
- (f) Consumer care details

---

## 📄 License

MIT License — Built for educational and compliance purposes.
