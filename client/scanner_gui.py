#!/usr/bin/env python3
"""
Label Compliance Checker — Python GUI Application
Cross-platform native GUI for Legal Metrology (Packaged Commodities) Rules, 2011 compliance scanning.
Runs on desktop (macOS, Windows, Linux) and mobile (Pydroid 3, Termux with X11/VNC).
"""
import sys
import os
import threading
import json
from datetime import datetime

# Path resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from client.api_client import LabelCheckerClient
except ImportError:
    from api_client import LabelCheckerClient

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Colors
BG_DARK = "#090d16"
CARD_BG = "#121826"
CARD_HOVER = "#182235"
TEXT_LIGHT = "#f8fafc"
TEXT_MUTED = "#94a3b8"
ACCENT_BLUE = "#3b82f6"
COLOR_GREEN = "#10b981"
COLOR_AMBER = "#f59e0b"
COLOR_RED = "#ef4444"
BORDER_COLOR = "#232d42"


class LabelScannerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Label Compliance Checker — Legal Metrology (PCR 2011)")
        self.geometry("960x680")
        self.minsize(800, 600)
        self.configure(bg=BG_DARK)

        self.client = LabelCheckerClient()
        self.selected_file_path = None
        self.last_scan_result = None

        self._create_styles()
        self._build_ui()
        self._check_backend_async()

    def _create_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=BG_DARK)
        style.configure("Card.TFrame", background=CARD_BG, relief="flat")
        style.configure("TLabel", background=CARD_BG, foreground=TEXT_LIGHT, font=("Helvetica", 10))
        style.configure("Muted.TLabel", foreground=TEXT_MUTED, font=("Helvetica", 9))
        style.configure("Title.TLabel", font=("Helvetica", 14, "bold"), foreground=TEXT_LIGHT)
        style.configure("Header.TLabel", background=BG_DARK, font=("Helvetica", 16, "bold"), foreground=TEXT_LIGHT)

    def _build_ui(self):
        # Header Frame
        header = tk.Frame(self, bg=CARD_BG, height=54, highlightbackground=BORDER_COLOR, highlightthickness=1)
        header.pack(fill=tk.X, side=tk.TOP)

        brand_lbl = tk.Label(
            header,
            text="🏷️  Label Compliance Checker (PCR 2011)",
            font=("Helvetica", 13, "bold"),
            bg=CARD_BG,
            fg=TEXT_LIGHT
        )
        brand_lbl.pack(side=tk.LEFT, padx=18, pady=12)

        self.status_badge = tk.Label(
            header,
            text="Checking backend...",
            font=("Helvetica", 9),
            bg="#262f45",
            fg=TEXT_MUTED,
            padx=10,
            pady=4
        )
        self.status_badge.pack(side=tk.RIGHT, padx=18, pady=12)

        # Main Container (2 Columns)
        container = tk.Frame(self, bg=BG_DARK)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Left Column: Image Upload & Preview
        left_col = tk.Frame(container, bg=CARD_BG, width=380, highlightbackground=BORDER_COLOR, highlightthickness=1)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        left_col.pack_propagate(False)

        left_title = tk.Label(left_col, text="Package Label Image", font=("Helvetica", 11, "bold"), bg=CARD_BG, fg=TEXT_LIGHT)
        left_title.pack(anchor="w", padx=16, pady=(16, 8))

        # Preview box
        self.preview_canvas = tk.Canvas(left_col, bg="#0d1320", highlightthickness=1, highlightbackground=BORDER_COLOR, width=340, height=280)
        self.preview_canvas.pack(padx=16, pady=8)
        self.preview_text = self.preview_canvas.create_text(
            170, 140,
            text="No image selected\nClick 'Select Image' below",
            fill=TEXT_MUTED,
            font=("Helvetica", 10),
            justify=tk.CENTER
        )

        self.file_lbl = tk.Label(left_col, text="No file chosen", font=("Helvetica", 8), bg=CARD_BG, fg=TEXT_MUTED)
        self.file_lbl.pack(anchor="w", padx=16, pady=4)

        btn_row = tk.Frame(left_col, bg=CARD_BG)
        btn_row.pack(fill=tk.X, padx=16, pady=6)

        btn_select = tk.Button(
            btn_row,
            text="Select Image",
            command=self._select_image,
            bg="#232d42",
            fg=TEXT_LIGHT,
            activebackground=CARD_HOVER,
            activeforeground=TEXT_LIGHT,
            relief="flat",
            font=("Helvetica", 9, "bold"),
            padx=12,
            pady=6,
            cursor="hand2"
        )
        btn_select.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))

        btn_sample = tk.Button(
            btn_row,
            text="Load Sample",
            command=self._load_sample,
            bg="#232d42",
            fg=TEXT_LIGHT,
            activebackground=CARD_HOVER,
            activeforeground=TEXT_LIGHT,
            relief="flat",
            font=("Helvetica", 9),
            padx=10,
            pady=6,
            cursor="hand2"
        )
        btn_sample.pack(side=tk.RIGHT, padx=(4, 0))

        self.btn_scan = tk.Button(
            left_col,
            text="⚡ Run Compliance Scan",
            command=self._run_scan_thread,
            bg=ACCENT_BLUE,
            fg="white",
            activebackground="#2563eb",
            activeforeground="white",
            relief="flat",
            font=("Helvetica", 11, "bold"),
            pady=10,
            cursor="hand2",
            state=tk.DISABLED
        )
        self.btn_scan.pack(fill=tk.X, padx=16, pady=(12, 16))

        # Right Column: Results & Checklist
        right_col = tk.Frame(container, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        right_top = tk.Frame(right_col, bg=CARD_BG)
        right_top.pack(fill=tk.X, padx=16, pady=16)

        right_title = tk.Label(right_top, text="Compliance Evaluation", font=("Helvetica", 12, "bold"), bg=CARD_BG, fg=TEXT_LIGHT)
        right_title.pack(side=tk.LEFT)

        self.overall_label = tk.Label(
            right_top,
            text="STANDBY",
            font=("Helvetica", 10, "bold"),
            bg="#1c2538",
            fg=TEXT_MUTED,
            padx=12,
            pady=4
        )
        self.overall_label.pack(side=tk.RIGHT)

        # Fields List Container (Scrollable or Clean Frame)
        self.fields_container = tk.Frame(right_col, bg=CARD_BG)
        self.fields_container.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 10))

        # Initial placeholder in fields list
        self.placeholder_lbl = tk.Label(
            self.fields_container,
            text="Ready to scan.\nUpload a label image and click 'Run Compliance Scan'.",
            font=("Helvetica", 10),
            bg=CARD_BG,
            fg=TEXT_MUTED,
            justify=tk.CENTER
        )
        self.placeholder_lbl.pack(expand=True, pady=40)

        # Bottom actions
        bottom_bar = tk.Frame(right_col, bg=CARD_BG)
        bottom_bar.pack(fill=tk.X, padx=16, pady=12)

        self.btn_export = tk.Button(
            bottom_bar,
            text="📄 Export Certificate Report",
            command=self._export_report,
            bg="#232d42",
            fg=TEXT_LIGHT,
            relief="flat",
            font=("Helvetica", 9),
            padx=12,
            pady=6,
            cursor="hand2",
            state=tk.DISABLED
        )
        self.btn_export.pack(side=tk.RIGHT)

    def _check_backend_async(self):
        def task():
            try:
                res = self.client.health_check()
                self.after(0, lambda: self.status_badge.config(
                    text="● Backend Live (PaddleOCR)",
                    bg="#064e3b",
                    fg=COLOR_GREEN
                ))
            except Exception:
                self.after(0, lambda: self.status_badge.config(
                    text="○ Backend Offline",
                    bg="#451a1a",
                    fg=COLOR_RED
                ))
        threading.Thread(target=task, daemon=True).start()

    def _select_image(self):
        filetypes = [("Image files", "*.png;*.jpg;*.jpeg;*.webp"), ("All files", "*.*")]
        path = filedialog.askopenfilename(title="Select Package Label Image", filetypes=filetypes)
        if path:
            self._load_image_file(path)

    def _load_sample(self):
        sample_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sample_label.png"))
        if os.path.exists(sample_path):
            self._load_image_file(sample_path)
        else:
            messagebox.showinfo("Sample", "Sample image not found on disk.")

    def _load_image_file(self, path):
        self.selected_file_path = path
        self.file_lbl.config(text=os.path.basename(path))
        self.btn_scan.config(state=tk.NORMAL)

        # Update preview canvas
        if HAS_PIL:
            try:
                im = Image.open(path)
                im.thumbnail((340, 280))
                self.preview_image = ImageTk.PhotoImage(im)
                self.preview_canvas.delete("all")
                self.preview_canvas.create_image(170, 140, image=self.preview_image)
                return
            except Exception:
                pass

        self.preview_canvas.delete("all")
        self.preview_canvas.create_text(
            170, 140,
            text=f"Loaded:\n{os.path.basename(path)}\n(Ready to scan)",
            fill=COLOR_GREEN,
            font=("Helvetica", 10, "bold"),
            justify=tk.CENTER
        )

    def _run_scan_thread(self):
        if not self.selected_file_path:
            return
        self.btn_scan.config(state=tk.DISABLED, text="Scanning label...")
        self.overall_label.config(text="ANALYZING...", bg="#1c2538", fg=ACCENT_BLUE)

        def worker():
            try:
                res = self.client.scan_label(self.selected_file_path)
                self.after(0, lambda: self._display_results(res))
            except Exception as e:
                self.after(0, lambda: self._display_error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _display_error(self, err_msg):
        self.btn_scan.config(state=tk.NORMAL, text="⚡ Run Compliance Scan")
        self.overall_label.config(text="SCAN ERROR", bg="#451a1a", fg=COLOR_RED)
        messagebox.showerror("Scan Error", f"Failed to scan image:\n{err_msg}")

    def _display_results(self, res):
        self.last_scan_result = res
        self.btn_scan.config(state=tk.NORMAL, text="⚡ Run Compliance Scan")
        self.btn_export.config(state=tk.NORMAL)

        overall = res.get("overall_status", "UNKNOWN")
        comp_count = res.get("compliant_count", 0)
        total_fields = res.get("total_fields", 6)
        pct = int((comp_count / total_fields) * 100) if total_fields else 0

        if overall == "COMPLIANT":
            self.overall_label.config(text=f"✔ COMPLIANT ({pct}%)", bg="#064e3b", fg=COLOR_GREEN)
        elif overall == "PARTIALLY_COMPLIANT":
            self.overall_label.config(text=f"⚠ PARTIALLY COMPLIANT ({pct}%)", bg="#453106", fg=COLOR_AMBER)
        else:
            self.overall_label.config(text=f"✘ NON COMPLIANT ({pct}%)", bg="#451a1a", fg=COLOR_RED)

        # Clear container
        for widget in self.fields_container.winfo_children():
            widget.destroy()

        fields = res.get("fields", [])
        field_list = [{"key": k, **v} for k, v in fields.items()] if isinstance(fields, dict) else fields

        icons = {
            "manufacturer_name_address": "🏭",
            "generic_name": "📦",
            "net_quantity": "⚖️",
            "date_of_manufacture": "📅",
            "mrp": "💰",
            "consumer_care_details": "📞"
        }

        for idx, f_info in enumerate(field_list):
            f_key = f_info.get("field_name", "")
            icon = icons.get(f_key, "📋")
            name = f_info.get("display_name", f_key)
            status = (f_info.get("status") or "MISSING").upper()
            val = f_info.get("value") or "Not found on label"
            conf = int(f_info.get("confidence", 0) * 100)

            row = tk.Frame(self.fields_container, bg=CARD_HOVER if idx % 2 == 0 else CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
            row.pack(fill=tk.X, pady=3, padx=2)

            icon_lbl = tk.Label(row, text=icon, font=("Helvetica", 12), bg=row["bg"], width=3)
            icon_lbl.pack(side=tk.LEFT, padx=(6, 2))

            text_frame = tk.Frame(row, bg=row["bg"])
            text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=6)

            title_lbl = tk.Label(text_frame, text=name, font=("Helvetica", 9, "bold"), bg=row["bg"], fg=TEXT_LIGHT)
            title_lbl.pack(anchor="w")

            val_lbl = tk.Label(text_frame, text=val[:60], font=("Helvetica", 8), bg=row["bg"], fg=TEXT_MUTED)
            val_lbl.pack(anchor="w")

            if status == "FOUND":
                badge_text = f"✔ {conf}%"
                badge_bg = "#064e3b"
                badge_fg = COLOR_GREEN
            else:
                badge_text = "✘ Missing"
                badge_bg = "#451a1a"
                badge_fg = COLOR_RED

            badge = tk.Label(row, text=badge_text, font=("Helvetica", 8, "bold"), bg=badge_bg, fg=badge_fg, padx=8, pady=3)
            badge.pack(side=tk.RIGHT, padx=10)

    def _export_report(self):
        if not self.last_scan_result:
            return

        out_path = filedialog.asksaveasfilename(
            title="Save Compliance Report",
            defaultextension=".txt",
            filetypes=[("Text file", "*.txt"), ("Markdown file", "*.md")]
        )
        if not out_path:
            return

        res = self.last_scan_result
        lines = [
            "================================================================",
            "   LEGAL METROLOGY (PACKAGED COMMODITIES) RULES, 2011",
            "            LABEL COMPLIANCE AUDIT REPORT",
            "================================================================",
            f"Audit Date:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Scan ID:          {res.get('scan_id', 'N/A')}",
            f"Overall Status:   {res.get('overall_status')}",
            f"Compliance Score: {res.get('compliant_count')}/{res.get('total_fields')} fields compliant",
            "----------------------------------------------------------------",
            "CHECKLIST DETAILS:",
            "----------------------------------------------------------------",
        ]

        fields = res.get("fields", [])
        field_list = [{"key": k, **v} for k, v in fields.items()] if isinstance(fields, dict) else fields
        for f in field_list:
            lines.append(f"* {f.get('display_name')}: [{f.get('status')}] (Confidence: {int(f.get('confidence', 0)*100)}%)")
            lines.append(f"  Extracted: {f.get('value') or 'None'}")
            if f.get("recommendation"):
                lines.append(f"  Requirement: {f.get('recommendation')}")
            lines.append("")

        lines.append("================================================================")
        lines.append("Verified by Label Compliance Checker v1.0.0")

        with open(out_path, "w", encoding="utf-8") as out_f:
            out_f.write("\n".join(lines))

        messagebox.showinfo("Exported", f"Audit report successfully saved to:\n{out_path}")


def main():
    app = LabelScannerGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
