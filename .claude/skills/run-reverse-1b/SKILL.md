---
name: run-reverse-1b
description: Execute the Reverse 1B populator with a new 1A proforma file. Use when Alejandro provides a new 1A Excel file to process.
last_validated: 2026-04-15
allowed-tools: Read, Write, Bash, Grep, Glob
---

# Run Reverse 1B

## What it does
Takes a 1A proforma Excel file and populates a copy of the Reverse 1B template
with the extracted data. The mechanical work (parse, consolidate, copy template,
write cells, preserve formulas) is done by the repo engine at
`populate_reverse_1b.py`. This skill is the Claude-facing wrapper.

## How to run

```bash
python3 .claude/skills/run-reverse-1b/scripts/populate.py <path_to_1A.xlsx> --json
```

Options:
- `--municipality "Toronto"` — look up DC rates non-interactively
- `--building-type high-rise|mid-rise` — override auto-selection
- `--output-dir <path>` — override the default `output/` directory

`populate.py` handles the deterministic work:
- Input validation (must be `.xlsx` or `.xls`)
- Imports `parse_1a()` and `populate_template()` from the root engine
  (single source of truth — no cell mapping is duplicated here)
- Consolidates unit mix (the engine does weighted-average grouping for >3 types)
- Copies the template via the ZIP/XML writer (formulas, drawings, images preserved)
- Writes only to known input cells (Sheet 1, Sheet 4, Sheet 5)
- Exports the companion project JSON
- Verifies the output file exists with non-zero size before returning `ok: true`

## What Claude does

1. Run `populate.py` with the 1A path. Use `--json` for machine-readable output.
2. Check the `ok` flag and the `consolidated` flag in the result.
3. If `consolidated: true`, read the log file at `output/Reverse_1B_*_log.txt`
   and confirm the consolidation looks right (smallest/mid/largest grouping).
4. Run the `validate-output` skill against the generated xlsx before telling
   Alejandro it's ready.
5. Report: output path, unit total, consolidation status, municipality, building
   type. If anything failed, relay the error message verbatim.

## Rules

- NEVER hand-edit cells after the engine writes them. If a cell is wrong,
  the fix goes in `populate_reverse_1b.py`, not here.
- NEVER overwrite a formula (BLACK) cell. The engine enforces this; don't
  work around it.
- If Alejandro passes an `.xls` file, the engine converts to `.xlsx` first
  via LibreOffice CLI. If that fails, the script surfaces the error.
- For new municipalities not in `data_registry.json`, the engine flags it;
  don't silently fall back to Toronto.

## Key files
- `../../../populate_reverse_1b.py` — the engine (cell maps live here)
- `../../../reference/REVERSE_1B_Template.xlsx` — template (never modify)
- `../../../data_registry.json` — municipality DC rates
- `../../../guides/DATA_MAP.md` — cell-by-cell mapping reference
