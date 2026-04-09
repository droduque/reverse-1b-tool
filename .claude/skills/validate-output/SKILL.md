---
name: validate-output
description: Verify a generated Reverse 1B output file is correct. Use after running run-reverse-1b.
last_validated: 2026-04-08
allowed-tools: Read, Bash, Grep, Glob
---

# Validate Reverse 1B Output

## What it does
Checks that a generated Reverse 1B file has correct data
and intact formulas.

## Steps

1. **Open output file** with openpyxl (data_only=False to see formulas).

2. **Verify Sheet 1** — Compare populated values against the
   source 1A input. Check title, address, unit mix, rents,
   expenses, NOI, valuations.

3. **Verify Sheet 5 (Key Assumptions)** — Confirm:
   - E12-E16 have project-specific values (not template defaults)
   - All other cells still contain formulas (not hardcoded values)

4. **Spot-check downstream sheets** — Open 2-3 sheets that
   reference Sheet 1. Verify formula references are intact
   (should show formulas, not #REF! errors).

5. **Report pass/fail per check:**

| Check | Status | Notes |
|-------|--------|-------|
| Sheet 1 values match input | PASS/FAIL | details |
| Sheet 5 assumptions updated | PASS/FAIL | details |
| Formula cells preserved | PASS/FAIL | details |
| Downstream references intact | PASS/FAIL | details |
| File opens without errors | PASS/FAIL | details |

## Key files
- `output/` — generated files
- `reference/REVERSE_1B_Template.xlsx` — compare against template
