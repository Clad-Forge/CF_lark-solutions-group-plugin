#!/usr/bin/env python3
# ---------------------------------------------------------------------
# COPY - do not edit here. The original is 02-Tool/extract_receipts.py in the LSG-005
# project folder; this file is overwritten by 05-Plugin/build_plugin.py.
# ---------------------------------------------------------------------
"""
LSG-005 Step 4, part one: pull everything readable out of the receipts offline.

Deliberately does NOT decide anything. It extracts, and the Skill judges. The
split matters because matching money is deterministic and should be cheap and
repeatable, while reading a crumpled photo is not.

  PDFs    read straight off the text layer with PyMuPDF. Emailed receipts -
          airline itineraries, hotel folios, rental invoices - are nearly always
          digital PDFs with real text, so this is exact and free.
  Images  NOT OCR'd. They are flagged `needs_vision` and handed to the Skill,
          which can look at them directly. That removes any Tesseract install
          and is better on angled phone photos than local OCR would be.

Expense totals come from the VOUCHERS, not from the summary workbook: openpyxl
writes formulas without cached values, so a freshly generated tracker reads back
as blank until Excel has opened it once. Parsing the voucher again is exact and
has no such trap.

Usage:
    python extract_receipts.py --project "04-Projects/NSW 2607-A"
Writes:
    <project>/04-Receipt Check/_extract.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

# PyMuPDF is OPTIONAL, and deliberately so.
#
# It is the only compiled dependency in the whole pipeline - a wheel built
# against one Python version and architecture. openpyxl, the other one, is pure
# Python and can simply be carried along in the plugin. Making this one a hard
# requirement would mean either an install on the client's machine or shipping
# binaries that have to match their interpreter exactly.
#
# All it buys is SPEED and DETERMINISM on PDFs that already carry a text layer -
# 17 of the 26 receipts in the test set. Without it every receipt is marked
# needs_vision and Claude reads it directly, which it can already do for the 9
# images either way. Same answers, more slowly.
#
# So: use it if it is there, say so plainly if it is not, never fail over it.
# `pymupdf` is the current module name; `fitz` is the old one and now prints a
# deprecation warning on import. Try the new name, fall back to the old so an
# older install still works, and end up with None if neither is there.
try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_vouchers import collect_submissions, parse_voucher, split_name
from tracker_sheet import RECEIPT_CATEGORIES, stage_dir

# voucher computed key -> the category folder a receipt for it belongs in
CATEGORY_OF = {key: label for label, key in RECEIPT_CATEGORIES if key}

# 1,234.56 / 1234.56 / $99.00 - two decimals required, so "2 days" and a date
# cannot be mistaken for money.
AMOUNT = re.compile(r"\$?\s*(\d{1,3}(?:,\d{3})*\.\d{2})\b")

DATE_PATTERNS = [
    (re.compile(r"\b(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\b"), "ymd"),
    (re.compile(r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})\b"), "mdy"),
    (re.compile(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+"
                r"(\d{1,2}),?\s+(\d{4})\b", re.I), "mon"),
]
MONTHS = {m: n for n, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun",
     "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}


def find_amounts(text):
    """Every two-decimal figure in the text, biggest first.

    Biggest first because a receipt's largest number is almost always its
    total - but they are ALL returned, since a folio's nightly rate may be what
    matches a single voucher line rather than the category total."""
    seen = []
    for raw in AMOUNT.findall(text):
        value = float(raw.replace(",", ""))
        if value not in seen:
            seen.append(value)
    return sorted(seen, reverse=True)


def find_dates(text):
    """Any date in the text, ISO, deduped, in order of appearance."""
    found = []
    for pattern, kind in DATE_PATTERNS:
        for match in pattern.finditer(text):
            try:
                if kind == "ymd":
                    year, month, day = (int(g) for g in match.groups())
                elif kind == "mdy":
                    month, day, year = (int(g) for g in match.groups())
                else:
                    month = MONTHS[match.group(1)[:3].lower()]
                    day, year = int(match.group(2)), int(match.group(3))
                iso = dt.date(year, month, day).isoformat()
            except (ValueError, KeyError):
                continue
            if iso not in found:
                found.append(iso)
    return found


def guess_vendor(text):
    """First substantial line. Receipts lead with the merchant name.

    A guess, and named one - the Skill confirms it against the file itself.
    Never write this straight into a filename."""
    for line in text.splitlines():
        line = line.strip()
        if len(line) < 2:
            continue
        if AMOUNT.fullmatch(line) or re.fullmatch(r"[\d\s.,/-]+", line):
            continue
        return line[:60]
    return ""


def read_receipt(path):
    """One receipt. PDFs give text; images are handed on for vision."""
    record = {"file": path.name, "path": str(path),
              "suffix": path.suffix.lower(), "bytes": path.stat().st_size}
    if path.suffix.lower() != ".pdf":
        record.update(kind="image", needs_vision=True,
                      note="image - open it and read the vendor, date and total")
        return record

    if fitz is None:
        record.update(kind="pdf", needs_vision=True,
                      note="PDF - no text extractor installed, open it and read "
                           "the vendor, date and total")
        return record

    try:
        with fitz.open(str(path)) as doc:
            text = "\n".join(page.get_text() for page in doc)
            record["pages"] = doc.page_count
    except Exception as exc:                       # noqa: BLE001 - report, never crash the run
        record.update(kind="unreadable", needs_vision=True, error=str(exc))
        return record

    if len(text.strip()) < 20:
        # A scan saved as PDF: real pages, no text layer.
        record.update(kind="scanned-pdf", needs_vision=True, text="",
                      note="PDF with no text layer - render or view it to read")
        return record

    record.update(kind="pdf", needs_vision=False, text=text.strip(),
                  amounts=find_amounts(text), dates=find_dates(text),
                  vendor_guess=guess_vendor(text))
    return record


def expenses_for(result):
    """What this person claimed, per category: the total and the lines.

    Both, because a hotel folio usually matches the category total while a
    single taxi receipt matches one line."""
    out = {}
    for key, label in CATEGORY_OF.items():
        total = round((result.get("computed") or {}).get(key) or 0, 2)
        lines = sorted({round(ln[key], 2) for ln in result["lines"]
                        if ln.get(key)}, reverse=True)
        if total or lines:
            out[label] = {"total": total, "lines": lines}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Extract receipt text for the Step 4 check.")
    ap.add_argument("--project", required=True, help="a 04-Projects/<Project> folder")
    ap.add_argument("--rate", type=float, default=0.725)
    args = ap.parse_args(argv)

    # resolve() so that --project "." from inside the folder still knows its own
    # name; Path(".").name is an empty string.
    project = Path(args.project).resolve()
    inbox = stage_dir(project, "01", "01-Inbox")
    if not inbox.is_dir():
        print(f"inbox not found: {inbox}", file=sys.stderr)
        return 2

    people = []
    for voucher, receipts, folder in collect_submissions(inbox):
        if folder is None:
            continue                                # loose voucher, no person folder
        entry = {"person": folder, "voucher": voucher.name if voucher else None,
                 "employee": "", "initial_surname": "", "trip": {},
                 "expenses": {}, "receipts": []}
        if voucher:
            result = parse_voucher(voucher, args.rate)
            last, first, _mid = split_name(result["employee"])
            entry["employee"] = result["employee"]
            # 'SANDS JR, NEAL F' -> 'N. Sands Jr', the filename convention
            entry["initial_surname"] = (
                f"{first[:1].upper()}. {last.title()}" if last and first else last.title())
            dates = [ln["date"] for ln in result["lines"] if ln.get("date")]
            entry["trip"] = {"first_day": min(dates).isoformat() if dates else None,
                             "last_day": max(dates).isoformat() if dates else None}
            entry["expenses"] = expenses_for(result)
        entry["receipts"] = [read_receipt(p) for p in receipts]
        people.append(entry)

    out_dir = stage_dir(project, "04", "04-Receipt Check")
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {"project": project.name, "generated": dt.date.today().isoformat(),
               "categories": [label for label, _k in RECEIPT_CATEGORIES],
               "people": people}
    out = out_dir / "_extract.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    total = sum(len(p["receipts"]) for p in people)
    vision = sum(1 for p in people for r in p["receipts"] if r.get("needs_vision"))
    print(f"{len(people)} person folder(s), {total} receipt(s)")
    if fitz is None:
        print("  PyMuPDF is not installed - every receipt goes to vision.")
        print("  Same answers, just slower. Install it to read text-layer PDFs offline.")
    print(f"  {total - vision} read offline from the PDF text layer")
    print(f"  {vision} need looking at (image or no text layer)")
    for person in people:
        got = len(person["receipts"])
        print(f"  {person['person']:<20} {got:>2} receipt(s)"
              f"{'  <- no voucher' if not person['voucher'] else ''}")
    print(f"written: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
