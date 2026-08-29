# Voucher pipeline

Turns a folder of West Run travel vouchers and receipts into filed receipts, an
audit workbook, and a QuickBooks Online import file.

You set up two folders and answer one question. Everything else runs.

---

## Install

It arrives with the **Lark Solutions Group plugin** — there is nothing to unzip
and no folder to place. If you have not added the plugin yet, follow
`docs/client-setup.md` in the plugin repository; it takes about a minute and you
only do it once.

Once the plugin is installed, this skill is simply there. Updates arrive the
same way, so you never reinstall it by hand.

### Python

This runs on Python, which the plugin does **not** bundle — install it once and
every tool we send you afterwards uses the same runtime:

1. Get Python **3.13** from **python.org/downloads** — the real installer.
2. On the first screen, tick **"Add python.exe to PATH"**.
3. Then, in a terminal:

   ```
   pip install openpyxl pymupdf
   ```

`openpyxl` is required — nothing can read or write a workbook without it.
`pymupdf` is optional: it reads the text out of PDF receipts so they do not have
to be looked at one by one. Without it everything still works, it just takes
longer.

> **Do not install Python from the Microsoft Store.** Windows ships a
> placeholder called `python3` that looks installed and then does nothing —
> it opens the Store instead of running. If `python --version` prints nothing
> useful, that placeholder is what you have.

## Set up a job

One folder per project. Name it whatever West Run calls the exercise — it is on
the voucher itself, in the `Exercise Name` box (`NSW 2607-A`).

```
NSW 2607-A/
  Inbox/
    Sands Jr, Neal/
      Sands Neal - Travel Voucher.xlsx
      Receipts/
        hotel-folio.pdf
        fuel-stop.jpg
    Ferreira, Ana/
      ...
```

**One folder per person, named `Lastname, Firstname`.** Their voucher can sit
anywhere inside it, and receipts can be loose or in a `Receipts/` subfolder — it
searches the whole folder. Receipts are recognised by extension: `.pdf`, `.png`,
`.jpg`, `.jpeg`, `.heic`, `.tif`, `.webp`, `.bmp`, `.gif`.

**Filenames do not matter.** Contractors name files `IMG_4471.jpg` and
`voucher (3).xlsx`. Everything is identified by what is inside it.

That is the whole job. Do not create anything else — `Output/` is made for you.

## Run it

Point Claude at the project folder and say **"process the vouchers"**.

It asks one question — **the mileage rate**, defaulting to `0.725`. Press enter
to accept it, or type a different rate when the GSA rate changes. That number
both audits what contractors billed and sets what the tracker bills at.

Then it runs. Nothing else is asked.

## What comes back

```
NSW 2607-A/
  Inbox/                                    untouched, exactly as received
  Output/
    Vouchers/                               every voucher, renamed
    Receipts/
      Airfare/                              renamed receipts, filed by category
      Lodging/
      Rental Vehicle/
      ...
    2026.08.28 - Invoice Tracker - NSW 2607-A.xlsx
    2026.08.28 - QuickBooks Bills - NSW 2607-A.csv
  _work/                                    working files, ignore
```

Receipts are renamed `YYYY.MM.DD - Vendor - Category - F. Lastname.ext` using
the date **printed on the receipt**. A category folder only appears once a
receipt has been filed into it, so a folder you can see always has something in
it.

**Originals in `Inbox/` are never moved or edited.** Everything in `Output/` is
a copy. `Inbox/` stays the record of what a contractor actually sent.

## Before you import to QuickBooks

Three things, in order:

**1. Open the workbook.** It carries a `Variance` column — the voucher's own Due
against what the tracker computes — plus `Receipt Check` and `Receipts Missing`.
Work anything flagged. Columns shaded for keying are West Run's own direct costs
and labor days; a voucher cannot know them.

**2. Check the vendor names.** The run prints every contractor it is about to
bill. **Each one must already exist in QuickBooks under that exact name.**
Anyone missing has to be set up by hand first — the pipeline will not create a
vendor, because creating one means handling tax IDs and these vouchers carry
social security numbers the tools are built never to read.

**3. Import the CSV.** QuickBooks asks you to map the columns, then shows every
bill before it creates anything. **That preview is the approval gate.** Nothing
is posted until you say so.

## What it will refuse to do

It holds a voucher back rather than guess. Held vouchers are always named, never
quietly dropped:

| Held when | Why |
|---|---|
| The voucher cannot be read | Nothing to bill |
| The lines do not add up to the voucher's Due, to the penny | The document disagrees with itself. Somebody looks at it |
| Due is negative | The cash advance exceeded the trip, so money is owed *back*. That is a vendor credit, not a bill — enter it by hand |
| Receipts arrived with no voucher | The case that otherwise goes missing |

A voucher with a **missing receipt or a mileage-rate disagreement still bills.**
Those are findings for somebody to chase, not a reason to hold up a
reimbursement — they ride along in the bill's Memo so they are visible in
QuickBooks when you approve.

## Two things it will never do

- **Round anything to make it agree.** A two-cent gap is reported as a two-cent
  gap.
- **Change a voucher, a receipt, or a number.** It reads, reconciles, files and
  reports. Corrections are a human's.

---

*Built by Clad Forge for Lark Solutions Group. Questions to
cort@cladforge.com.*
