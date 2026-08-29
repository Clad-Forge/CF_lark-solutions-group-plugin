<!-- SOURCE OF TRUTH - edit here. This file lives in the lsg plugin repo
     (Clad-Forge/CF_lark-solutions-group-plugin); ship changes with
     ./scripts/release.sh. It began as a copy of 01-Reference/voucher-layout.md
     in the LSG-005 project folder: do not run 05-Skill/build_skill.py against
     this repo, and never copy an LSG-005 version over this file. -->

> Reference for `process-vouchers`. Read this when a voucher will not parse
> or a figure looks wrong: it is the cell-by-cell map of the West Run travel
> voucher and every template quirk the parser is built to survive.

# Voucher layout & field map

Source of truth: `01-Reference/Dummy Voucher (Actual).xlsx` — the real form,
supplied 2026-08-08. Everything below was read out of that file, not assumed.

> **2026-08-09 — the form changed.** The first sample
> (`01-Reference/Dummy Voucher.xlsx`) was a *Coastal Defense Inc.* mock-up with
> a Lark employee's name and e-mail on it. The genuine article is a **West Run,
> LLC** voucher. Same exercise, same TDY, different template. The header block
> and the expense grid are identical; **everything below row 39 moved.** Both
> forms still parse — see [Two forms](#two-forms).

**Document:** *West Run, LLC — Travel Voucher*
**Office:** 10153 Hounsdale Drive, Pickerington, OH 43147 · 254 681-5809
**Workbook:** three sheets — `Export Summary`, `Voucher` (all data), `Receipts`
(empty). It was **exported from Apple Numbers**, which matters (quirk 1).
**Used range:** `A1:J60`. 59 merged ranges.

## Header block

Values live in the **anchor** cell of each merged range. Read the anchor.

| Field | Cell | Merge | Sample value | Type seen |
|---|---|---|---|---|
| Employee name | `A9` | `A9:E9` | `SANDS JR, NEAL F` | text, `LAST, First M` |
| **SSN or EIN** | `F9` | `F9:H9` | `000-00-0000` | **text — see the warning below** |
| Voucher date | `I9` | `I9:J9` | `2026-07-25` | real date here, text on the old form |
| Street address | `A11` | `A11:D11` | `9686 PACIFIC PINES CT` | text |
| City | `E11` | `E11:G11` | `ORLANDO` | text |
| State | `H11` | — | `FL` | text |
| Zip | `I11` | `I11:J11` | `32832` | number, may be blank |
| E-mail | `C12` | `C12:F12` | `…@example.com` | text |
| Phone | `I12` | `I12:J12` | `(407) 461-7081` | text |
| Location (TDY) | `C13` | `C13:J13` | `WATERTOWN, NY` | text |
| **Exercise Name** | `C14` | `C14:J14` | `NSW 2607-A` | text — **this is the project key** |

Rows 5–7 are the payment-method block (`A6`/`B7` tick ACH or Check). Row 15 is
the static GSA instruction line. Neither is data.

> ### ⚠️ `F9` holds a social security number
>
> The dummy carries `000-00-0000`. **Real submissions will carry real SSNs.**
> The parser does not read `F9` and must never be changed to — that one field is
> the difference between a summary workbook and a PII liability. Worth raising
> with Levi separately: a folder of these vouchers sitting in OneDrive is a pile
> of contractor SSNs, and that is a storage-and-access question, not a parsing
> one.

## Expense grid — rows 17 to 38

Header labels sit in row 16. Twenty-two available rows; a voucher uses as many
as the trip needs and leaves the rest blank. **Unchanged from the old form.**

| Col | Header | Notes |
|---|---|---|
| `A` | Date | real date on this form |
| `B` | Travel From/To | free text. **Best row-occupancy test** |
| `C` | POV Miles | number, `0` when flying |
| `D` | Mileage $ Billed | number |
| `E` | Airfare | number |
| `F` | Car Rental | number |
| `G` | Rental Fuel | number |
| `H` | Hotel | number, per night |
| `I` | Per Diem/M&I | number, per day |
| `J` | Parking/Taxi/Tolls | number |

## Totals and the footer

| Field | Cell | Notes |
|---|---|---|
| Column totals | `D39:J39` | literals, except `J39` which is `=SUM(J17:J38)` |
| Section B — daily rate | `E41` | independent-contractor labor |
| Section B — number of days | `H41` | |
| Section B — labor total | `I41` | |
| Section A: TOTAL TRAVEL | `I42` | the grid's row 39 added up |
| TOTAL TRIP EXPENSES | `I43` | travel + labor |
| Cash Advance & Company Prepaid | `I44` | |
| **Total Reimbursement/labor Due** | **`I45`** | **what the employee gets paid** |

Rows 46–53 are certification, signature and office-use blocks. Not data.

**Section B is new.** The old form had no labor line at all. When a contractor
bills labor, `Due` is larger than the travel categories add up to, and that has
to be visible rather than look like a broken sum — see proj-lsg-005-tool.

## Two forms

The footer is the only part whose geometry differs, so the parser finds it by
**reading the labels** in rows 40–53 and taking the rightmost number on the
matching row. No second cell map, and it survives the row drift a Numbers
re-export would introduce.

| | West Run (current) | Old Coastal Defense mock |
|---|---|---|
| Total trip expenses | `I43` | `J40` |
| Cash advance | `I44` | `J41` |
| Due | `I45` | `J42` |
| Section B labor | `I41` | — |
| Section A total travel | `I42` | — |

## Known quirks — the parser must survive all of these

1. **It is a Numbers export, so the formulas are gone.** Every cell that was a
   formula has been flattened to a literal — only `J39` survived. Consequences:
   the "wrong cell reference" audit has nothing to read on this form, and a
   voucher opened and re-saved in Excel will not recompute anything.
2. **`'$'` appears where a number should be.** `D20` and `E24` are the literal
   string `$`, and `E26` is `' $                    -  '`. All three are Numbers'
   rendering of `$0.00`. They coerce to blank, which is correct — they are
   excluded from sums, and every column still reconciles against row 39.
3. **The sample has a date typo.** `A18` is `2026-04-11` sitting between
   `2026-07-10` and `2026-07-12`, and the signature date `B50` is `2026-04-18`.
   April for a July trip. The parser flags any line date more than 45 days from
   the voucher's median. **Ask Levi whether this is a known keying habit.**
4. **Rows 32–38 carry zeros with no date or route.** Occupancy is tested on
   column `A` **or** `B`, so they are correctly excluded — the same defence that
   handled the old form's stale formulas.
5. **Mileage can be billed with no POV miles.** On the old form this was always
   a stale copy-paste formula; flattened to a literal it becomes a bare number
   on a zero-mile row. Flagged explicitly, because the formula that used to
   explain it no longer exists.
6. **Filenames carry no identity.** Identity comes from `A9`, period.
7. **Name format differs from the old form** — `SANDS JR, NEAL F`: uppercase,
   generational suffix inside the surname field, no trailing period on the
   middle initial. `split_name` still splits on commas; `SANDS JR` is the
   surname.
8. **Blank ≠ zero.** An empty `I44` means "no advance", not `$0.00`.
9. **No penny bug on this form.** The old template's `=SUM(D17:D38)+0.01` was a
   property of that Excel mock-up. The West Run voucher reconciles **exactly** —
   all seven categories match row 39, and row 39 adds to `I42`/`I43`/`I45`.

## What survives the parser

**Unchanged from the first build** — the field set was settled 2026-08-03 and
Cort confirmed 2026-08-09 that it stays the same. Note that the West Run form
carries **no yellow highlighting**; the selection comes from that agreement, not
from the file.

**Kept**

| | |
|---|---|
| `A9` | employee name |
| `I9` | voucher date |
| rows 17–38, cols `A`,`C`,`D`,`E`,`F`,`G`,`H`,`I`,`J` | date, POV miles, mileage $, airfare, car rental, rental fuel, hotel, per diem, parking/taxi/tolls |
| `D39:J39` | column totals **as the voucher reports them** — to reconcile, not to report |
| `I45` (by label) | due employee |

**Dropped** — read but not carried: address, city, state, zip, e-mail, phone,
location, exercise name, **column `B`**, `I43` total trip expenses, `I44` cash
advance. **Never read at all:** `F9` (SSN/EIN).

`I42` and `I43` are read internally, only to derive Section B labor as the gap
between them. Column `B` is read internally for row occupancy.

## Reported vs computed

The parser reports **its own sum of the lines**, then checks that against
`D39:J39` and `I42`. Any gap becomes a warning on that voucher. `I45` passes
through untouched — it is the number the employee gets paid.

## Open questions for Levi

- **Is `Dummy Voucher.xlsx` (Coastal Defense) dead?** If contractors only ever
  submit the West Run form, the two-form support is insurance we can drop.
- Where does the master list live — and is the **WR Invoice Tracker** (added
  2026-08-08, not yet examined) it?
- Should Section B labor be carried as its own column on the master list? Today
  it is only flagged, because the agreed field set is travel-only.
- Is the April date in the sample a one-off or a habit?
- How do receipts arrive, and how are they tied back to a voucher?
- Who fixes a voucher that fails validation — Lark, or back to the contractor?
- **Where should vouchers carrying real SSNs be stored?**

## Related
- proj-lsg-005-tool — the parser
- proj-lsg-005-test-data — regression baseline
- LSG-005 — project anchor
