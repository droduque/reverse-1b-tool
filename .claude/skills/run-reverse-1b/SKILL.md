---
name: run-reverse-1b
description: Execute the Reverse 1B populator with a new 1A proforma file. Use when Alejandro provides a new 1A Excel file to process.
allowed-tools: Read, Write, Bash, Grep, Glob
---

# Run Reverse 1B

## What it does
Takes a 1A proforma Excel file and populates a copy of the
Reverse 1B template with the extracted data.

## Steps

1. **Validate input file** — Confirm it's .xlsx or .xls.
   If .xls, convert to .xlsx first (LibreOffice CLI).

2. **Scan the 1A** — Read the proforma to extract:
   - Title and address (E2/F2)
   - Unit mix (types, SF, counts, rents) starting at row 7
   - Operating revenues, expenses, NOI
   - Valuation at three cap rates
   Use docs/DATA_MAP.md for exact cell locations.

3. **Copy the template** — Copy reference/REVERSE_1B_Template.xlsx
   to output/ with data_only=False (preserve ALL formulas).

4. **Populate Sheet 1** — Write 1A data to the correct cells.
   CRITICAL: Only write to BLUE cells. NEVER overwrite BLACK
   (formula) or GREEN (overridable) cells.

5. **Update Key Assumptions (Sheet 5)** — Only cells E12-E16,
   F15, E37, R57-R59. Everything else is formulas.

6. **Handle unit mix consolidation** — If the 1A has more than
   3 unit types, consolidate into 3 (smallest, mid, largest)
   using weighted averages for rent and SF.

7. **Save and verify** — Save output file. Open it to confirm:
   - Sheet 1 shows the new 1A data
   - Formula cells are intact (not overwritten)
   - Downstream sheets reference correctly

## Key files
- `reference/REVERSE_1B_Template.xlsx` — template (never modify)
- `reference/1A_*.xlsx` — sample 1A files
- `docs/DATA_MAP.md` — cell-by-cell mapping
- `docs/1B_User_Manual.pdf` — color conventions (BLUE/BLACK/GREEN)
