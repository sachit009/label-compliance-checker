#!/usr/bin/env python3
"""
Label Compliance Checker — Python CLI Tool
Scan packaging labels and verify compliance with the Legal Metrology (Packaged Commodities) Rules, 2011.
"""
import sys
import os
# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import argparse
try:
    from client.api_client import LabelCheckerClient
except ImportError:
    from api_client import LabelCheckerClient

# ANSI Color codes for terminals
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BLUE = "\033[94m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def color_status(status: str) -> str:
    s = status.upper()
    if "COMPLIANT" in s and "NON" not in s and "PARTIAL" not in s:
        return f"{GREEN}{BOLD}PASS ({s}){RESET}"
    elif "PARTIAL" in s:
        return f"{YELLOW}{BOLD}WARN ({s}){RESET}"
    else:
        return f"{RED}{BOLD}FAIL ({s}){RESET}"


def cmd_health(client: LabelCheckerClient):
    print(f"{DIM}Connecting to {client.base_url}...{RESET}")
    try:
        res = client.health_check()
        print(f"\n{GREEN}{BOLD}Backend Status: HEALTHY{RESET}")
        print(f"  Service:    {res.get('service')}")
        print(f"  Version:    {res.get('version')}")
        print(f"  OCR Engine: {res.get('ocr_engine')}")
        print(f"  Endpoint:   {client.base_url}\n")
    except Exception as e:
        print(f"\n{RED}{BOLD}Backend Unreachable:{RESET} {e}\n")
        sys.exit(1)


def cmd_scan(client: LabelCheckerClient, image_path: str):
    if not os.path.exists(image_path):
        print(f"{RED}Error: File not found: {image_path}{RESET}")
        sys.exit(1)

    print(f"{DIM}Scanning label image: {image_path}...{RESET}")
    try:
        res = client.scan_label(image_path)
    except Exception as e:
        print(f"{RED}Scan request failed:{RESET} {e}")
        print(f"{YELLOW}Hint: Ensure backend is running or pass --server http://<ip>:8000{RESET}")
        sys.exit(1)

    overall = res.get("overall_status", "UNKNOWN")
    comp_count = res.get("compliant_count", 0)
    total_fields = res.get("total_fields", 6)
    score_pct = int((comp_count / total_fields) * 100) if total_fields else 0

    print("\n" + "=" * 68)
    print(f"  SCAN RESULT: {color_status(overall)}")
    print(f"  Compliance Score: {score_pct}% ({comp_count}/{total_fields} Mandatory Fields Present)")
    print(f"  Scan ID: {res.get('scan_id', 'N/A')}")
    print("=" * 68 + "\n")

    fields = res.get("fields", [])
    field_list = [{"key": k, **v} for k, v in fields.items()] if isinstance(fields, dict) else fields
    header = f"{'MANDATORY FIELD':<44} | {'STATUS':<12} | {'CONFIDENCE':<10} | {'EXTRACTED VALUE'}"
    print(f"{BOLD}{header}{RESET}")
    print("-" * 94)

    for field_info in field_list:
        name = field_info.get("display_name") or field_info.get("field_name", "Field")
        status = (field_info.get("status") or "MISSING").upper()
        conf = f"{int(field_info.get('confidence', 0) * 100)}%"
        val = field_info.get("value") or "-"
        if len(val) > 28:
            val = val[:25] + "..."

        if status == "FOUND":
            st_colored = f"{GREEN}PRESENT{RESET}"
        elif status == "ILLEGIBLE":
            st_colored = f"{YELLOW}ILLEGIBLE{RESET}"
        else:
            st_colored = f"{RED}MISSING{RESET}"

        print(f"{name:<44} | {st_colored:<21} | {conf:<10} | {val}")
        rec = field_info.get("recommendation")
        if rec and status != "FOUND":
            print(f"  {DIM}↳ Required: {rec}{RESET}")

    print("-" * 76 + "\n")


def cmd_history(client: LabelCheckerClient, page: int = 1, status: str = None):
    try:
        res = client.get_history(page=page, status=status)
    except Exception as e:
        print(f"{RED}Failed to fetch history:{RESET} {e}")
        sys.exit(1)

    items = res.get("items", [])
    total = res.get("total", 0)
    print(f"\n{BOLD}Scan History (Total: {total}, Page: {page}){RESET}\n")
    if not items:
        print(f"{DIM}No scan records found.{RESET}\n")
        return

    print(f"{'SCAN ID':<38} | {'STATUS':<20} | {'COMPLIANT'}")
    print("-" * 70)
    for item in items:
        sid = item.get("scan_id", "")
        st = color_status(item.get("overall_status", ""))
        cnt = f"{item.get('compliant_count')}/{item.get('total_fields')}"
        print(f"{sid:<38} | {st:<29} | {cnt}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Legal Metrology (Packaged Commodities) Rules, 2011 — Python Label Scanner"
    )
    parser.add_argument("--server", default=os.getenv("API_BASE_URL", "http://127.0.0.1:8000"), help="Backend URL")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    subparsers.add_parser("health", help="Check server health")

    scan_parser = subparsers.add_parser("scan", help="Scan a label image file")
    scan_parser.add_argument("image", help="Path to image file")

    hist_parser = subparsers.add_parser("history", help="List scan history")
    hist_parser.add_argument("--page", type=int, default=1, help="Page number")
    hist_parser.add_argument("--status", choices=["COMPLIANT", "PARTIALLY_COMPLIANT", "NON_COMPLIANT"], help="Filter by status")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    client = LabelCheckerClient(base_url=args.server)

    if args.command == "health":
        cmd_health(client)
    elif args.command == "scan":
        cmd_scan(client, args.image)
    elif args.command == "history":
        cmd_history(client, page=args.page, status=args.status)


if __name__ == "__main__":
    main()
