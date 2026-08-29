#!/usr/bin/env python3
# ---------------------------------------------------------------------
# COPY - do not edit here. The original is 02-Tool/quickbooks_export.py in the LSG-005
# project folder; this file is overwritten by 05-Plugin/build_plugin.py.
# ---------------------------------------------------------------------
"""
LSG-005 - the QuickBooks Online bill import file.

The last mile. Every other script in this folder exists to work out what each
contractor is actually owed; this one turns that into something QuickBooks can
swallow, so nobody keys a reimbursement by hand.

WHY A FILE AND NOT AN API. There is no QuickBooks connector, and building one
means an Intuit developer app plus OAuth2 tokens that would have to live
somewhere. A CSV needs no credentials, no network, and no permission to touch
Lark's books. They import it, QuickBooks shows them every bill it is about to
create, and a human approves. The approval gate is the point, not a limitation.

WHAT IT WILL NOT DO
-------------------
* It will not emit a bill whose lines do not add up to the voucher's Due, to
  the penny. Not rounded, not balanced with a plug line. A voucher that does
  not reconcile is HELD and named. This whole project exists because a previous
  sheet was hand-patched by pennies to force agreement; a bill that quietly
  disagrees with the document behind it would be the same mistake with an
  invoice number on it.
* It will not emit a bill for a voucher the parser could not read (status
  ERROR). Those are held.
* It will not invent a vendor. QuickBooks matches on the name in the Vendor
  column; anyone not already set up there fails at import, visibly. Creating
  vendors would mean tax IDs, and the SSN field on these vouchers is one the
  tools are forbidden to read.
* It will not silently drop a negative Due. A contractor whose cash advance
  exceeded their trip owes money back - that is a vendor credit, not a bill,
  and the two must not be mixed in one import. Held and named.

WARN vouchers DO export. An unbacked toll receipt or a mileage-rate
disagreement is a finding for a human to chase, not a reason to hold up
somebody's whole reimbursement. The findings ride along in the bill Memo so
they are visible in QuickBooks at approval time.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from parse_vouchers import collect_submissions, parse_voucher  # noqa: E402
from tracker_sheet import (initial_surname, long_path, safe_field,  # noqa: E402
                           split_name, stage_dir)

# --------------------------------------------------------------------- accounts
#
# Voucher figure -> the QuickBooks expense account the line posts to.
#
# The first five are Lark's own QuickBooks category names - that is why the
# tracker and the receipt folders use exactly these words and not, say,
# "Car Rental". They line up on purpose so a receipt, a tracker column and a
# bill line all read the same.
#
# The last four are NOT confirmed against their chart of accounts. They are the
# money a voucher owes that no receipt backs - mileage and per diem are computed
# from a rate, labor is Section B, and the advance is a deduction. Change the
# right-hand side to whatever their COA actually calls these; nothing else in
# the file needs touching.
ACCOUNTS = [
    ("airfare",    "Airfare",                 "Airfare"),
    ("hotel",      "Lodging",                 "Lodging"),
    ("car_rental", "Rental Vehicle",          "Rental Vehicle"),
    ("fuel",       "Rental Fuel",             "Rental Fuel"),
    ("taxi",       "Parking, Tolls & Taxis",  "Parking, Tolls & Taxis"),
    ("mileage",    "POV Mileage",             "POV Mileage"),          # confirm
    ("per_diem",   "Per Diem / M&I",          "Per Diem / M&I"),       # confirm
    ("labor",      "Contract Labor",          "Contract Labor"),       # confirm
    ("advance",    "Cash Advance Recovery",   "Cash Advance Recovery"),  # confirm
]

# QuickBooks Online's bill importer asks you to map columns on the way in, so
# these headers do not have to match its template exactly - but they are named
# after its fields to make that mapping a formality.
HEADERS = ["Bill No", "Vendor", "Bill Date", "Due Date", "Terms", "Memo",
           "Account", "Line Description", "Line Amount"]

PENNY = 0.011


def bill_no(exercise, employee, taken):
    """A short, stable, unique bill number: 'NSW2607A-SANDSJR'.

    Stable matters more than pretty. Re-running the pipeline as late vouchers
    trickle in regenerates this file, and the same voucher must produce the same
    bill number every time - that is what makes QuickBooks reject it as a
    duplicate instead of paying somebody twice.

    QuickBooks caps this field, so it is trimmed to 20 characters. A collision
    after trimming gets a numeric suffix rather than being allowed to merge two
    people's lines into one bill."""
    last, _first, _mid = split_name(employee)
    code = safe_field(exercise, "JOB").replace(" ", "").replace("-", "").upper()
    who = safe_field(last, "UNKNOWN").replace(" ", "").upper()
    base = f"{code[:10]}-{who}"[:20].strip("-")
    candidate, count = base, 2
    while candidate in taken:
        suffix = f"~{count}"
        candidate = f"{base[:20 - len(suffix)]}{suffix}"
        count += 1
    taken.add(candidate)
    return candidate


def vendor_name(employee, style="display"):
    """The name QuickBooks has to match against.

    A voucher writes 'SANDS JR, NEAL F' - shouting, surname first, initial with
    no period. No accounting system has a vendor called that. 'display' turns it
    into 'Neal Sands Jr', which is the shape a QuickBooks vendor is normally set
    up in; 'voucher' passes the raw field through for a book that happens to be
    keyed the other way.

    Either way this is a MATCH, never a create. A name QuickBooks does not
    recognise fails at import, loudly, and somebody sets that vendor up by hand.
    That is the correct outcome: creating vendors from these files would mean
    handling the SSN field, which is the one field this pipeline will not read."""
    if style == "voucher":
        return employee
    last, first, _middle = split_name(employee)
    if not last:
        return employee
    # The middle initial is dropped on purpose. 'Ana Ferreira' is far more likely
    # to be how a vendor is actually set up than 'Ana L. Ferreira', and this name
    # only has to do one job: match a record that already exists.
    return f"{first.title()} {last.title()}".strip() if first else last.title()


def bill_lines(result):
    """The lines of one bill, and what they add up to.

    Amounts come from `computed` - our own sum of the voucher's expense lines -
    never from the voucher's own totals row. The two are checked against each
    other by the parser and any gap is already a warning on that voucher; using
    the reported figure here would hide it again.

    The advance is a NEGATIVE line, because the voucher's Due is net of it while
    the categories are gross. Without it no bill could ever tie."""
    computed = result.get("computed") or {}
    lines = []
    for key, label, account in ACCOUNTS:
        if key == "labor":
            amount = result.get("labor") or 0.0
        elif key == "advance":
            amount = -(result.get("advance") or 0.0)
        else:
            amount = computed.get(key) or 0.0
        amount = round(amount, 2)
        if abs(amount) < 0.005:
            continue                    # a category nobody spent in is not a line
        lines.append({"account": account, "description": label, "amount": amount})
    return lines, round(sum(ln["amount"] for ln in lines), 2)


def findings_for(person, matches):
    """The receipt-check findings for one person, condensed for the Memo.

    Whoever approves this bill in QuickBooks should be able to see that
    something was flagged without going back to the workbook. Amounts and
    categories only - no vendor names, no receipt detail, nothing that would put
    more of somebody's trip into an accounting system than the approval needs."""
    if not matches:
        return []
    notes = []
    unbacked = [u for u in matches.get("unbacked", []) if u.get("person") == person]
    if unbacked:
        total = sum(u.get("amount") or 0 for u in unbacked)
        notes.append(f"{len(unbacked)} expense(s) with no receipt, {total:.2f}")
    mine = [r for r in matches.get("receipts", []) if r.get("person") == person]
    bad = [r for r in mine if r.get("status") == "mismatched"]
    if bad:
        notes.append(f"{len(bad)} receipt(s) do not match the voucher amount")
    orphans = [r for r in mine if r.get("status") == "orphan"]
    if orphans:
        notes.append(f"{len(orphans)} receipt(s) match no expense")
    return notes


def memo_for(result, project, matches):
    """Exercise, voucher date, then anything a human should know before paying."""
    bits = [result.get("exercise") or project]
    date = result.get("voucher_date")
    if date:
        bits.append(f"voucher {date.strftime('%Y-%m-%d')}")
    bits.extend(findings_for(result.get("folder") or "", matches))
    if result.get("rate_issues"):
        bits.append(f"{result['rate_issues']} mileage line(s) fail the rate check")
    return " | ".join(b for b in bits if b)


def build(project, rate, matches, vendor_style="display"):
    """Every voucher in the inbox, sorted into bills and holds.

    Returns (rows, bills, held). `held` is the important half - it is what a
    human has to deal with, and it is never allowed to be silently short."""
    inbox = stage_dir(project, "01", "Inbox")
    if not inbox.is_dir():
        raise SystemExit(f"inbox not found: {inbox}")

    rows, bills, held, taken, vendors = [], [], [], set(), []
    for voucher, _receipts, folder in collect_submissions(inbox):
        who = folder or (voucher.name if voucher else "?")
        if voucher is None:
            held.append((who, "receipts but no voucher - nothing to bill"))
            continue

        result = parse_voucher(voucher, rate)
        result["folder"] = folder or ""
        employee = result.get("employee") or ""
        name = initial_surname(employee) or who

        if result.get("status") == "ERROR":
            reason = result["notes"][0] if result.get("notes") else "could not be read"
            held.append((who, f"voucher could not be parsed - {reason}"))
            continue

        due = result.get("due_employee")
        if due is None:
            held.append((name, "no Due figure on the voucher"))
            continue

        lines, total = bill_lines(result)
        if not lines:
            held.append((name, "voucher has no expense lines"))
            continue

        if due < 0:
            held.append((name, f"Due is {due:.2f} - the advance exceeds the trip, so "
                               f"this is a vendor credit owed back to West Run, "
                               f"not a bill. Enter it by hand."))
            continue

        if abs(total - due) > PENNY:
            held.append((name, f"lines add to {total:.2f} but the voucher's Due is "
                               f"{due:.2f} - a {total - due:+.2f} gap. Not billed; "
                               f"the voucher needs looking at."))
            continue

        supplier = vendor_name(employee, vendor_style)
        if supplier not in vendors:
            vendors.append(supplier)
        number = bill_no(result.get("exercise") or project.name, employee, taken)
        date = result.get("voucher_date")
        stamp = date.strftime("%m/%d/%Y") if date else ""
        memo = memo_for(result, project.name, matches)
        for line in lines:
            rows.append({
                "Bill No": number,
                "Vendor": supplier,
                "Bill Date": stamp,
                # Left blank on purpose: QuickBooks applies the vendor's own
                # payment terms. Inventing a due date here would be this tool
                # deciding when somebody gets paid.
                "Due Date": "",
                "Terms": "",
                "Memo": memo,
                "Account": line["account"],
                "Line Description": line["description"],
                "Line Amount": f"{line['amount']:.2f}",
            })
        bills.append((number, name, total, len(lines)))
    return rows, bills, held, vendors


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(long_path(path), "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Write a QuickBooks Online bill import file from parsed vouchers.")
    ap.add_argument("--project", required=True, help="the project folder")
    ap.add_argument("--rate", type=float, default=0.725,
                    help="mileage rate the vouchers are audited against")
    ap.add_argument("--out", help="defaults to <project>/Output/<date> - QuickBooks Bills - <project>.csv")
    ap.add_argument("--vendor-format", choices=("display", "voucher"), default="display",
                    help="'display' writes 'Neal Sands Jr'; 'voucher' writes the raw "
                         "'SANDS JR, NEAL F' straight off the voucher")
    args = ap.parse_args(argv)

    project = Path(args.project).resolve()

    # The receipt check is optional here. Its findings enrich the Memo, but a
    # bill file must be producible from vouchers alone - the money is a property
    # of the voucher, not of whether anybody has looked at the receipts yet.
    matches = None
    check = stage_dir(project, "04", "_work") / "_matches.json"
    if check.is_file():
        try:
            matches = json.loads(check.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            print(f"note: could not read {check.name} ({exc}); "
                  f"memos will carry no receipt findings", file=sys.stderr)

    rows, bills, held, vendors = build(project, args.rate, matches, args.vendor_format)

    if args.out:
        out = Path(args.out)
    else:
        stamp = dt.date.today().strftime("%Y.%m.%d")
        name = f"{stamp} - QuickBooks Bills - {safe_field(project.name, 'Project')}.csv"
        out = stage_dir(project, "05", "Output") / name
    write_csv(out, rows)

    total = sum(b[2] for b in bills)
    print(f"{len(bills)} bill(s), {len(rows)} line(s), {total:,.2f} total")
    for number, name, amount, count in bills:
        print(f"  {number:<22} {name:<18} {amount:>10,.2f}  {count} line(s)")
    if vendors:
        print(f"\n{len(vendors)} vendor(s) - each must ALREADY EXIST in QuickBooks "
              f"under this exact name, or that bill fails at import:")
        for who in vendors:
            print(f"  {who}")

    if held:
        print(f"\n{len(held)} NOT billed - these need a human:")
        for who, why in held:
            print(f"  {who}: {why}")
    print(f"\nwritten: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
