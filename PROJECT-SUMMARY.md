# SVN Rock — Project Summary

Last Updated: 2026-03-09

## Phase 1: 1A to Reverse 1B Populator

### Completed
- [x] Deep investigation of all Excel files (1A proformas, template, inputs spec)
- [x] Cell-by-cell mapping documented in `docs/INVESTIGATION_REPORT.md`
- [x] CLAUDE.md updated with corrected write targets (Sheet 5 is mostly formulas)
- [x] Dynamic 1A parser — finds sections by landmark text, not hardcoded rows
- [x] Unit mix consolidation — groups N unit types into 3 rows with weighted averages
- [x] Template populator — writes to Sheet 1, Sheet 4, Sheet 5
- [x] Formula preservation verified (all formula cells untouched)
- [x] Birchmount test: 524 matches, 0 mismatches on Sheet 1
- [x] 490 St Clair test: 9 types consolidated to 3, commercial=0 handled, .xls format works
- [x] Estimation logging — every assumed value documented in output log
- [x] Flags for Noor (Altus Ottawa vs GTA columns, height category, external refs)
- [x] ZIP/XML writer — preserves drawings/images/charts byte-for-byte (fixes openpyxl corruption)
- [x] DC rate lookup — 51 municipalities from Kanen's spreadsheet
- [x] Property tax rates — 46 municipalities, NT rates preferred, MT fallback
- [x] Municipality auto-detection from project address
- [x] Building type auto-detection from floor count (7+ = high-rise)
- [x] Web app (Flask) with Rock Advisors branding
- [x] Property tax override fields in web form (auto-fill from 1A + municipality)
- [x] Burlington DC formatting bug fixed (commas → decimal points)
- [x] Excel opens without drawing repair warnings

### Not Yet Done
- [ ] Edge case: 1A with only 1-2 unit types
- [ ] Edge case: 1A with no parking at all
- [ ] Edge case: different expense label formats across clients
- [ ] Test with additional 1A files (Glenavy, Bayview, Old Weston Rd in reference/)
- [ ] Host web app online

### Key Files
```
populate_reverse_1b.py          # Main script — parses 1A, populates template
xml_writer.py                   # ZIP/XML writer — surgical cell modification
app.py                          # Flask web app
templates/index.html            # Web UI (Rock Advisors design)
static/logo-white.png           # Logo
reference/                      # Input files, template, DC/tax data
output/                         # Generated files + logs
docs/INVESTIGATION_REPORT.md    # Detailed investigation findings
docs/DATA_MAP.md                # Cell mapping reference
compare_outputs.py              # Compares auto output vs template
```

### How to Run
```bash
# Command line
python3 populate_reverse_1b.py reference/1A_Birchmount_2240.xlsx

# Web app
python3 app.py
# Then open http://localhost:5001
```

### Known Issues
1. Sheet 5 O48/P48 reference Ottawa Altus costs instead of GTA (pre-existing template issue)
2. Sheet 13 Altus values are text strings ("$295") — works in Excel via auto-coercion
3. External workbook references in Sheet 1 rows 70+ show stale values
4. Sheet 5 F29 always points to "13-39 Storeys" regardless of building height

### Waiting On
- **Kanen:** Toronto DC rate confirmation ($33,497 vs $34,849 for 1-bed)
- **Kanen:** Mississauga DC waiver status (2B/3B at $5,376 — is waiver active?)
- **Kanen:** Richmond Hill & Aurora NT tax rates (only MT available)
- **Noor:** Expanded template (3 → 14 unit rows) — away until ~2026-03-20
- **Fran/Joana:** Financing proposal sheet

### Future Phases
- Phase 2: Template row expansion 3 → 14 (waiting on Noor)
- Phase 3: HTML sensitivity/presentation tool (per Derek's vision)
- Phase 4: Financing proposal integration (pending Fran/Joana)
- Phase 5: Host web app online
