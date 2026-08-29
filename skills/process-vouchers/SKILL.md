---
name: process-vouchers
description: Process a folder of West Run travel vouchers end to end - parse every voucher, reconcile the receipts against what was claimed, file the receipts by category, build the Invoice Tracker workbook, and write a QuickBooks Online bill import file. Use when the user says "process the vouchers", "run the vouchers", "do the voucher folder", "check the receipts", names a project folder holding an Inbox, or opens a session in one and asks to process it.
---

# Process a voucher project

One command in, a finished folder out. The person running this puts vouchers and
receipts into `Inbox/`, points you at the project folder, and gets back filed
receipts, an audit workbook, and a file QuickBooks can import.

```
Inbox/  ->  [ parse  ->  reconcile  ->  file  ->  export ]  ->  Output/
```

**You judge; the scripts execute.** Which receipt backs which expense, what a
vendor is called, what is missing — yours. Arithmetic, filing 26 files, and
writing a workbook — the scripts', because those have to be exact and identical
every run. **Never do the money math yourself.** If a number is wrong, fix the
input and re-run; do not correct it in your head and report the corrected one.

## 0. Orient — quietly, before anything else

**The project folder** is whichever hits first:

1. A path the user gave you.
2. The current directory, if it contains an `Inbox` folder (or an `01-*` folder,
   which is the older layout).
3. If the current directory contains folders that each hold an `Inbox`, list
   them and ask which one.
4. Otherwise say what you looked for and stop. **Do not guess.**

**The scripts and the interpreter ship inside this skill's own folder:**

```
<skill>/
  SKILL.md      this file
  scripts/      parse_vouchers.py, extract_receipts.py, finalize_receipts.py,
                quickbooks_export.py, tracker_sheet.py
  references/   voucher-layout.md — the cell map, read it only when needed
  python/       a self-contained interpreter, python.exe inside (may be absent;
                see Python below)
```

**No Excel template is needed and none is shipped.** The Invoice Tracker is
written from scratch by `tracker_sheet.py` — headers, formulas, brand colours
and all. The only workbooks ever opened are the vouchers in `Inbox/` and the
tracker the pipeline itself just wrote.

`<skill>` is the directory holding this `SKILL.md`. This skill ships in the
`lsg` plugin, so use `${CLAUDE_SKILL_DIR}` — Claude Code substitutes it with this
skill's own folder, wherever the client installed the plugin. Expand `<skill>`
to a real path in every command below.

If you cannot find `<skill>/scripts/parse_vouchers.py`, say so and stop — do
not go hunting for a copy elsewhere on the machine, because a stale copy that
runs is worse than an honest failure.

**Python.** Use `<skill>/python/python.exe` — bundled, needs no install, and the
one this was tested against. Only if that folder is missing, fall back to
`py -3`, then `python`, then `python3`.

Then check the one library that is actually required:

```bash
"<skill>/python/python.exe" -c "import openpyxl; print('ok')"
```

`openpyxl` is **required** — nothing can read or write a workbook without it. If
it is missing, offer to install it and **ask first**:

```bash
"<skill>/python/python.exe" -m pip install openpyxl
```

`pymupdf` is **optional**. It reads the text layer out of PDF receipts so they do
not have to be looked at. Without it every receipt comes back `needs_vision` and
you read them all yourself — same answers, more work. Do not install it without
being asked, and never treat it as missing-and-therefore-broken.

**Never install silently.** If the user declines `openpyxl`, stop — there is no
working around it.

Say the project folder and Python in one line, then stop narrating setup.

## 1. Ask for the mileage rate — before you run anything

Ask exactly one question, and offer the default:

> **Mileage rate?** Press enter for **0.725**, or give a different rate.

That number does two jobs: contractors are audited against it, and the tracker
bills at it. It changes when the GSA rate changes. Use whatever they answer for
every step below — the same rate goes to all three scripts. **Do not skip this
question and assume the default.**

If they also say the exercise or project name, note it; otherwise the scripts
take it off the vouchers themselves.

## 2. Parse the vouchers

```bash
"<skill>/python/python.exe" "<skill>/scripts/parse_vouchers.py" --project "<project>" --rate <rate>
```

Writes the Invoice Tracker workbook into `_work/`. Every run writes a new
version and never overwrites an earlier one.

Read what it prints. Anything `ERROR` could not be read at all and will not
reach QuickBooks — say so now, not at the end.

**If a voucher will not parse, or a figure looks wrong**, read
`<skill>/references/voucher-layout.md` before guessing. It is the cell-by-cell
map of the form and lists the template's known quirks — `'$'` strings sitting in
numeric cells, flattened formulas, mileage billed on a zero-mile row, a date
typo in the client's own sample. Several things that look like bugs are
documented and deliberate. **Do not open the voucher and start correcting
numbers.**

## 3. Extract the receipts

```bash
"<skill>/python/python.exe" "<skill>/scripts/extract_receipts.py" --project "<project>" --rate <rate>
```

Writes `_work/_extract.json`: per person their name, `initial_surname`, the trip
window, what they claimed per category (`total` and the individual `lines`), and
one record per receipt.

PDFs with a text layer arrive already parsed — `vendor_guess`, `amounts`
(largest first), `dates`. **Anything with `needs_vision: true` is an image: open
it with the Read tool and read the vendor, date and total yourself.** Never skip
one, and never infer a receipt's contents from its filename — contractors name
files `IMG_4471.jpg`.

## 4. Match every receipt to an expense

For each receipt find the line on that person's row that it backs:

1. **Amount is the strong signal.** Check against both the category `total` and
   each entry in `lines` — a hotel folio usually matches the category total, a
   single taxi receipt matches one line.
2. **Date narrows it.** The receipt date should sit inside `trip.first_day` …
   `trip.last_day`. Outside that window, say so.
3. **Vendor decides the category** when the amount is ambiguous: an airline is
   `Airfare`, a hotel is `Lodging`, Hertz/Avis/Enterprise is `Rental Vehicle`, a
   fuel brand is `Rental Fuel`, a toll authority or taxi is
   `Parking, Tolls & Taxis`. Anything else is `MISC`.

Every receipt ends up **matched**, **mismatched** (found the expense, the amount
differs) or **orphan** (backs nothing). Every expense with no receipt is
**unbacked**.

> **Never adjust an amount to make a match.** A two-cent gap is a finding. This
> whole project exists because the sheet that came before it was hand-patched by
> pennies to force agreement.

## 5. Write your judgement to `_work/_matches.json`

`source` must be the path copied straight from `_extract.json`, and
`initial_surname` likewise — do not re-derive either.

```json
{
  "receipts": [
    {"source": "<path from _extract.json>",
     "person": "Baptiste, Yvonne",
     "initial_surname": "Y. Baptiste",
     "vendor": "Comfort Inn",
     "date": "2026-07-06",
     "category": "Lodging",
     "amount": 528.40,
     "status": "matched",
     "voucher_amount": 528.40,
     "note": ""}
  ],
  "unbacked": [
    {"person": "Baptiste, Yvonne", "category": "Parking, Tolls & Taxis",
     "amount": 22.10, "note": "no receipt found"}
  ]
}
```

- **`date`** — the transaction date printed on the receipt. Not the email date,
  not today.
- **`vendor`** — as printed, short, no `Inc`/`LLC`/`Ltd`. Cannot read it? Leave
  it `null`; it files as `UNKNOWN VENDOR` and gets listed for a human. **A
  confidently wrong vendor on a financial record is worse than an obviously
  incomplete one.**
- **`category`** — exactly one of `Airfare`, `Baggage`, `Lodging`,
  `Rental Vehicle`, `Rental Fuel`, `Parking, Tolls & Taxis`, `MISC`. These are
  QuickBooks' own category names. **Never invent one.**

## 6. File everything

```bash
"<skill>/python/python.exe" "<skill>/scripts/finalize_receipts.py" --project "<project>"
```

Renames each receipt `YYYY.MM.DD - Vendor - Category - F. Lastname.ext`,
**copies** it into `Output/Receipts/<Category>/` — creating a category folder
only as a file lands in it — copies the tracker into `Output/` with
`Receipt Check` and `Receipts Missing` columns appended, and writes the run log.

If it reports anything under **could not be filed**, say so plainly. Do not
present the run as complete.

## 7. Write the QuickBooks import file

```bash
"<skill>/python/python.exe" "<skill>/scripts/quickbooks_export.py" --project "<project>" --rate <rate>
```

Writes `Output/YYYY.MM.DD - QuickBooks Bills - <Project>.csv` — one bill per
contractor, lines split by expense account, the cash advance as a negative line.

**A bill is only written when its lines add up to the voucher's Due, to the
penny.** Anything that does not tie is held back and named. Read the script's
output and repeat every held voucher to the user — that list is the work that is
left, and it must never be summarised away.

It also prints the vendor names. **Every one has to already exist in QuickBooks
under that exact name** or the bill fails at import. Pass that list on.

## 8. Report

Lead with findings, not counts:

- Every **unbacked expense** — person, category, amount. **This is the point.**
  It is what gets asked about before West Run invoices Coastal Defense.
- Every **mismatch**, every **orphan**, anything filed `UNKNOWN VENDOR`.
- Every voucher **held back from QuickBooks**, and why.
- The vendor list to check against QuickBooks.
- Then the counts: vouchers parsed, receipts filed, bills written, total.

Then tell them what to do next, in this order:

1. Open the workbook in `Output/` and work anything flagged.
2. Check the vendor names exist in QuickBooks.
3. Import the CSV — **QuickBooks shows every bill before it creates anything.
   Approve there.**

## Rules

- **Never edit a receipt, a voucher, or a number in the tracker.** This pipeline
  files and reports; it does not correct.
- **Never move an original out of `Inbox/`.** It is the only proof of what a
  contractor actually sent. Everything downstream is a copy.
- **Never round to make something agree.**
- **These vouchers carry social security numbers** in a field the scripts are
  built never to read. Do not read it either, do not put it in a filename, a
  memo, a report or a chat message. Receipts carry names, addresses and partial
  card numbers — nothing beyond the vendor, date and amount needed to state a
  finding goes into chat, and none of it leaves the project folder.
- **If a step fails, stop and say so.** A final output that looks complete but
  is not is the worst thing this can produce.
