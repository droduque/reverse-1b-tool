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

- Sheet 5: Only cells E12-E16, F15, E37, R57-R59 are inputs. Everything else is formulas.
- Rows 7-10 on Sheet 1: formula cells in columns after the unit mix data. Only write to the data columns.
- External workbook references (e.g., G22 submetering) — pre-existing, leave as-is.

Learned from INVESTIGATION_REPORT.md analysis of all 15 sheets.
