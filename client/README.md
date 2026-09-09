# 🏷️ Label Compliance Checker — Python Client Suite

A cross-platform Python client for scanning product packaging labels and validating compliance under the **Legal Metrology (Packaged Commodities) Rules, 2011**.

Replaces native Java, Kotlin, and Swift dependencies with a lightweight, 100% Python suite that runs on **Desktop (macOS, Windows, Linux)** and **Mobile (Android & iOS)**.

---

## 📦 Features

- **Desktop GUI**: Dark-themed graphical interface with image preview, live scanning progress, compliance card checklist, and report export.
- **Command Line Interface (CLI)**: Fast terminal tool with ANSI color badges and formatted inspection tables.
- **Python SDK / Library**: Import `LabelCheckerClient` in any Python script with zero external dependencies (uses standard library `urllib`).
- **Audit Reports**: One-click certificate export to text or markdown.

---

## 🚀 Quick Start

### 1. Requirements
The client works with standard Python 3.9+ and requires **no external dependencies**!
Optional: Install `Pillow` for high-resolution image preview thumbnails:
```bash
pip install Pillow
```

### 2. Launch the Graphical User Interface (GUI)
```bash
python client/scanner_gui.py
```
- Click **Select Image** or **Load Sample**.
- Click **⚡ Run Compliance Scan**.
- Inspect the 6 mandatory Legal Metrology fields:
  1. 🏭 Manufacturer / Packer / Importer Name & Address
  2. 📦 Common or Generic Name
  3. ⚖️ Net Quantity (Weight, Volume, or Count)
  4. 📅 Month & Year of Manufacture / Packing
  5. 💰 Maximum Retail Price (MRP incl. of all taxes)
  6. 📞 Consumer Care Details (Phone, Email, Address)
- Click **📄 Export Certificate Report** to save the verification certificate.

### 3. Use the Command Line Interface (CLI)

Check backend connection:
```bash
python client/scanner_cli.py health
```

Scan a label image:
```bash
python client/scanner_cli.py scan sample_label.png
```

List recent scan history:
```bash
python client/scanner_cli.py history --page 1
```

Filter history by compliance status:
```bash
python client/scanner_cli.py history --status COMPLIANT
```

Connect to a remote or cloud backend:
```bash
python client/scanner_cli.py --server https://your-deployed-backend.com scan label.jpg
```

---

## 📱 Running on Mobile Devices

### 🤖 Android
You can run this client on any Android phone without needing an APK build or Android Studio!

#### Option A: Pydroid 3 (Recommended)
1. Install **Pydroid 3** from Google Play Store or F-Droid.
2. Clone or copy this repository to your device.
3. Open `client/scanner_gui.py` inside Pydroid 3 and tap **Play ▶**.
4. The native GUI will open on your phone with full camera and file access.

#### Option B: Termux
1. Install **Termux** from F-Droid.
2. Run:
   ```bash
   pkg update && pkg install python
   python client/scanner_cli.py scan /sdcard/DCIM/Camera/label.jpg
   ```

---

### 🍎 iOS (iPhone & iPad)
You can run this client on iPhone/iPad without needing an Xcode build or Mac!

#### Option A: Pythonista 3
1. Open **Pythonista 3** from the App Store.
2. Import `client/scanner_cli.py` and `client/api_client.py`.
3. Select an image from Photos and run the scanner directly.

#### Option B: Carnets / Juno
1. Run the Python client interactively using Jupyter notebook or terminal commands.

---

## 💻 Programmatic Python SDK Usage

```python
from client.api_client import LabelCheckerClient

# Initialize client
client = LabelCheckerClient(base_url="http://127.0.0.1:8000")

# 1. Health check
print(client.health_check())

# 2. Scan an image file
result = client.scan_label("sample_label.png")
print(f"Overall Status: {result['overall_status']}")
print(f"Fields Compliant: {result['compliant_count']}/{result['total_fields']}")

# 3. Inspect individual fields
for field in result["fields"]:
    print(f"- {field['display_name']}: {field['status']} (Value: {field['value']})")
```
