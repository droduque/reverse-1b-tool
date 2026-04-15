---
name: validate-output
description: Verify a generated Reverse 1B output file is correct. Use after running run-reverse-1b.
last_validated: 2026-04-15
allowed-tools: Read, Bash, Grep, Glob
---

# Validate Reverse 1B Output

## What it does
Checks that a generated Reverse 1B file has correct data and intact formulas.
The XML-level checks (cell types, formula integrity, stale cache, cross-sheet
consistency, template bleed-through) are done by the repo engine at
`validate_output.py`. This skill is the Claude-facing wrapper.

## How to run

```bash
python3 .claude/skills/validate-output/scripts/validate.py <output_xlsx> --json
```

Options:
- `--source <1A_path>` — explicit 1A source; without it, the engine looks up
  the source by matching keywords in the output filename
- `--json` — emit machine-readable JSON; default is a human-readable table

`validate.py` handles the deterministic work. It imports `validate_output()`
and `parse_1a()` from the root engine, so the check list is the single source
of truth. Checks run:

- Workbook has `fullCalcOnLoad='1'` so Excel recalculates
- `calcChain.xml` absent (otherwise Excel shows a repair warning)
- No stale cached `<v>` values in formula cells
- `sharedStrings.xml` well-formed with matching uniqueCount
- Sheet 1 numeric cells stored as numbers, not shared strings
- Sheet 1 formula columns (F, G, I, J, K rows 7-9, plus row-10 TOTAL) still
  contain formulas (not overwritten)
- Unit sums, vacancy rate, cap rates match the parsed 1A source
- No division-by-zero setups (unit count > 0 with SF = 0)
- No Birchmount fingerprints (170 units, 128853 SF, 489850, 5878200) unless
  this IS Birchmount
- Sheet 4 C/D columns numeric and cross-matched against Sheet 1
- Sheet 1 E62 (Building GFA) > 0

## What Claude does

1. Run `validate.py --json` on the output xlsx.
2. Read the `passed` flag. If `false`, surface the `errors` list exactly.
3. If there are `warnings`, summarize them in one line (they're non-blocking
   but worth noting, especially template-bleed warnings).
4. If all checks pass, report: file name, checks passed count, source 1A
   used for cross-check.
5. For judgment calls (e.g., an unexpected warning that only appears on a
   specific project), flag to Alejandro rather than dismissing.

## Rules

- The engine is the source of truth for what "correct" means. Do not write
  a one-off Python snippet that duplicates a check.
- If validation fails, the fix goes in `populate_reverse_1b.py` (the thing
  that produced the bad output). Never edit the xlsx by hand to make
  validation pass.
- If no 1A source matches the output filename, pass `--source` explicitly.
  Don't skip validation because the lookup missed.

## Key files
- `../../../validate_output.py` — the engine (check list lives here)
- `../../../output/` — generated files
- `../../../populate_reverse_1b.py` — imported for `parse_1a()` cross-check
