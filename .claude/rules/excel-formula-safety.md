---
description: Critical rules for Excel formula preservation in Reverse 1B generation
---

## Color Conventions (from 1B_User_Manual.pdf)

- **BLUE cells** — Safe to write. These are input cells.
- **BLACK cells** — NEVER overwrite. These contain formulas.
- **GREEN cells** — Overridable, but check with Noor first.

## Formula Preservation Rules

1. Always copy template with `data_only=False` to preserve formulas.
2. Use `xml_writer.py` for complex workbooks — openpyxl corrupts drawings/images/charts.
3. After generation, verify formula cells still contain formulas (not hardcoded values).
4. Remove `calcChain.xml` from the ZIP to force Excel to recalculate on open.
5. Set `fullCalcOnLoad="1"` in workbook settings.

## Sheet Cascade

Sheet 1 (1A data) → Sheet 7 (intermediary calculations) → Sheet 5 (Key Assumptions) → downstream sheets.

Changing a value in Sheet 1 cascades through the entire workbook. This is by design.

## What NOT to Touch

- Sheet 5: pure input cells are E12-E16, F15, E37, R57-R59. Everything else is a formula.
- Rows 7-10 on Sheet 1: formula cells in columns after the unit mix data. Only write to the data columns.
- External workbook references (e.g., G22 submetering) — pre-existing, leave as-is.

## Formula-to-formula rewrite (documented exception)

Sheet 5 F29 / O48 / P48 / O49 / P49 are formulas in the template that the populator rewrites via `queue_write(..., is_formula=True)`. Each rewrite swaps the *target* of the cross-sheet reference (storey row, region columns, parking row), never the cell type. Allowed paths:

- **Surface parking override** (parking_type='surface'): O49/P49 repointed to Altus row 40 (was 36 in V4 / Altus 25).
- **Storey-tier selector** (storey_tier in form): F29/O48/P48 repointed to Altus row 6/7/8/9.
- **Wood-frame option** (construction_type='wood_frame' + storey_tier='up_to_6'): F29/O48/P48 repointed to Altus row 15.
- **Region selector** (region='ottawa' or 'other_ontario'): O48/P48 + O49/P49 column letters swap to Ottawa cols (L/M) or wrap in =AVERAGE(GTA, Ottawa).

If you need to add another formula-to-formula rewrite, follow the same pattern: helper builder → `queue_write(..., is_formula=True)` → log line. Never replace the formula with a static value.

Learned from INVESTIGATION_REPORT.md analysis of all 15 sheets, extended 2026-04-29 for the V5/Altus 26 epic.
