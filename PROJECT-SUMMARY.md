# SVN Rock — Project Summary

Last Updated: 2026-03-31

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
- [x] Bayview test: 12 unit types → 3, luxury rents ($8K-$20K/mo), no 1-beds handled cleanly
- [x] Old Weston test: 445 units, 3 types, largest unit count
- [x] Glenavy test: 9 types incl. walk-out townhouses + bachelor, 0 parking
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
- [x] Data freshness tracking system (registry + alerts + status badges)
- [x] JSON project data export for presentation tool
- [x] Alphabetical municipality dropdown
- [x] All 5 test projects pass full pipeline (zero crashes)
- [x] **Post-generation validator** — 67 automated checks per file (cell types, formulas, data accuracy)
- [x] **fullCalcOnLoad** — forces Excel to recalculate all formulas on open (no stale cached values)
- [x] **Empty unit group handling** — numeric zeros for projects missing a unit type (e.g., Bayview has no 1-beds)
- [x] **Validator integrated into web app** — bad files blocked before download on both /generate and /export-scenario
- [x] **Presentation link fix** — "Open in Presentation Mode" now shows most recent project (by time, not alpha sort)
- [x] **Parser section tracking** — reports which sections were found vs defaulted (8/10, missing: Commercial, Submetering)
- [x] **Financial sanity checks** — validate_output.py warns on out-of-range cap rates, expenses, IRRs

### Not Yet Done
- [ ] Edge case: 1A with only 1-2 unit types
- [ ] Edge case: different expense label formats across clients

## Phase 2: Presentation & Sensitivity Tool

### Completed
- [x] Client presentation tool (React/Babel standalone, dark premium theme)
- [x] 7 sections: Hero, Revenue, Costs, Metrics, Sensitivity, Financing, Data Sources
- [x] 5 sensitivity sliders: rent ($/sf), cap rate, construction cost, vacancy, interest rate
- [x] Rent slider shows actual $/sf with $0.05 steps (not percentage)
- [x] Baseline indicators on all sliders (shows starting value when adjusted)
- [x] "Killer callout" — per $0.10/sf rent impact on building value (permanent headline)
- [x] Dynamic impact callout when rent slider moves (green/red with dollar amount)
- [x] Merchant IRR (develop and sell at stabilization)
- [x] 10-Year Hold IRR (Newton's method, 2% NOI growth, exit at base cap rate)
- [x] Interest rate slider affects DSCR, cash-on-cash, and both IRRs
- [x] Animated numbers with quadratic ease-in-out
- [x] Save Scenario & Export button (re-generates Excel with adjusted values)
- [x] Reset to Baseline button
- [x] Multi-project support via URL routing (/present/<filename>)
- [x] Scroll-based section tracking (IntersectionObserver highlights active nav pill)
- [x] Fade-in entrance animations on scroll
- [x] Card hover effects (elevated shadow + gold border glow)
- [x] Scroll progress bar (gold, fixed top)
- [x] Upload tool redesigned — dark premium theme matching presentation tool
- [x] Drag-and-drop upload with gold dashed border
- [x] "Open in Presentation Mode" link after generation (auto-updates to latest project)
- [x] "(est.)" labels on screening-level metrics (dev costs, IRR, financing)
- [x] Legibility improvements (font sizes, spacing, dim text brightened)
- [x] **CMHC MLI Select financing** — permanent loan matches Exec Summary to 0.007%
- [x] Loan sizing: annual PV for amount, monthly PMT for debt service (matches Sheet 11 exactly)
- [x] CMHC program badges in financing section (dynamic per program selection)
- [x] Interest rate slider relabeled "CMHC Loan Rate" (3.7% baseline, 2.5-6.5% range)
- [x] CMHC Premium shown as cost line item in financing cards
- [x] Implied LTV shown (e.g., "84.7% LTV (DSCR-constrained)") instead of max LTV
- [x] Backwards compatibility for old JSON files (auto-upgrades to CMHC defaults)
- [x] **Reimport flow** — Noor uploads reviewed Excel, tool extracts verified metrics
- [x] **Results pages** — generation results + reimport results with warning banners
- [x] **Verified metrics at baseline** — exact Excel values shown when sliders at default
- [x] **Financing program selection** — dropdown in upload form (CMHC MLI Select, CMHC Standard, Conventional)
- [x] **Sheet 6 D31-D35 written during generation** — financing parameters now flow into template (was never written before)
- [x] **Interest rate slider exports to Excel** — slider value now flows through to exported Excel on /export-scenario (was silently discarded before)
- [x] **All 5 projects tested across all 3 financing programs** — passes validation
- [x] **Backward compatible with older JSON files** — auto-upgrades to CMHC MLI Select defaults
- [x] **Financing programs updated to Joanna's v3.12 proformas** (2026-03-19):
  - CMHC MLI Select (100pts): 95% LTV, 1.1x DSCR, 50yr amort, 3.70%, 5.00% premium
  - CMHC MLI Select Energy (50pts): 95% LTV, 1.1x DSCR, 40yr amort, 3.70%, 5.175% premium
  - Conventional: 75% LTV, 1.2x DSCR, 25yr amort, 5.50%, 0% premium
  - Old keys (cmhc_mli_select, cmhc_standard) aliased for backwards compatibility
- [x] **Stale cached value clearing** — formula cells stripped of template cached values across all 15 sheets
- [x] **calcChain.xml removal** — prevents Excel repair warnings from stale formula chain
- [x] **All 5 projects regenerated 2026-03-23** — all now use CMHC MLI Select 100pts (50yr amort, 3.7%, 5.00% premium). Old March 13/19 files cleaned out. All 5 pass validation (65-68 checks each). Sent to SVN team.
- [x] **Start date fix (2026-03-31)** — `=TODAY()` on month-end dates broke EDATE chain in Sheet 10 (units never "completed" → NOI=0). Fixed by forcing 1st of current month.
- [x] **Fran V2 template adopted (2026-03-31)** — Rock Advisors branding, Open Sans font, gold/slate colors, bold-blue consultant-input markers, print setup. Sheet 1 and 6 columns shifted left by 1. All cell mappings updated in populate_reverse_1b.py, validate_output.py, and import functions.
- [x] **Financing preview removed from presentation mode (2026-03-31)** — per Noor's feedback, takeout financing not shown to clients. Financing program selector kept in upload form (drives Sheet 6 calculations).
- [x] **Deployed to Railway (2026-03-31)** — live at https://earnest-celebration-production.up.railway.app

### IRR Accuracy (verified 2026-03-12 vs Excel Sheets 10 & 11)
- **Merchant IRR: 27.96% vs 27.90% (0.06pt gap)** — was 0.82pt before fix
- **Hold IRR: 20.66% vs 20.62% (0.04pt gap)** — was 0.36pt before fix
- Merchant IRR = simple CAGR (Sheet 10 collapses to two cash flows: equity in, sale out)
- Hold IRR = 10-year annual model with CMHC refi, 2% NOI growth, proper loan amortization
- Remaining ~0.05pt gap from $42K construction interest during lease-up (negligible)
- All dollar amounts feeding IRR are exact from Excel formula evaluation

### Revenue & Financing Accuracy (verified 2026-03-11 vs Exec Summary Sheet 2)
- Revenue: **0.00%** gap (exact match, all 8 line items)
- OpEx: **0.02%** gap ($323 utilities rounding on $1.7M)
- NOI @ Stabilization: **0.007%** gap ($343 on $4.9M)
- Building Value: **0.007%** gap ($7.6K on $108.9M)
- Permanent Loan: **0.007%** gap ($6.4K on $92.2M)
- Annual Debt Service: **0.007%** gap ($309 on $4.4M)
- LTV: **84.71%** exact match (4 decimal places)
- DSCR: **1.1081** exact match
- Dev costs: **0.4%** total gap (screening estimates, labeled "(est.)")

### Not Yet Done
- [ ] Test on 1440px laptop + iPad (responsive)
- [x] ~~Deploy to Railway~~ (done 2026-03-31)

## Output Validation (added 2026-03-11)

The system now validates every generated file before delivering it. This was added after discovering that:
1. Empty strings in numeric cells cause `#VALUE!` errors in Excel formulas
2. Without `fullCalcOnLoad`, Excel shows stale cached values from the Birchmount template
3. The presentation mode link was showing the wrong project (alphabetical sort, not chronological)

### What the Validator Checks (67 checks per file)
- **Cell types**: All numeric write targets (unit SF, counts, rents, parking, cap rates, GFA, etc.) are stored as numeric, not shared strings
- **Formula integrity**: Formula cells in rows 7-10 (unit mix area) still have formulas, not overwritten with values
- **Division-by-zero**: Flags when unit SF=0 could cause `#DIV/0!` in $/SF formulas
- **Data accuracy**: Unit count totals match parsed data, vacancy/cap rates match
- **Template bleed-through**: Warns if cached formula values still show Birchmount fingerprints (170 units, 128853 SF)
- **Workbook settings**: `fullCalcOnLoad="1"` present in workbook.xml
- **Cross-sheet consistency**: Sheet 4 unit counts/SF match Sheet 1

### How It Runs
- **Automatic**: Integrated into `app.py` — runs after every generation, before download
- **Blocking**: If any check fails, the file is deleted and an error is shown (bad files never delivered)
- **Both routes**: Covers `/generate` (upload) and `/export-scenario` (sensitivity export)
- **CLI**: `python3 validate_output.py` to validate all output files manually

## Key Files
```
populate_reverse_1b.py          # Main script — parses 1A, populates template
xml_writer.py                   # ZIP/XML writer — surgical cell modification
validate_output.py              # Post-generation validator (67 checks)
app.py                          # Flask web app + presentation routes
templates/index.html            # Upload UI (dark premium theme)
templates/presentation.html     # Client presentation tool (React/Babel)
templates/results.html          # Generation results page
templates/reimport.html         # Noor's reimport upload page
templates/results_reimport.html # Reimport results with diff
data_registry.json              # Dataset freshness tracking config
data_freshness.py               # Freshness calculator and alerts
reference/                      # Input files, template, DC/tax data
output/                         # Generated files (Excel + JSON) + logs
```

## How to Run
```bash
# Web app
python3 app.py
# Then open http://localhost:5001
# Upload tool: http://localhost:5001/
# Presentation: http://localhost:5001/present

# Validate all output files
python3 validate_output.py
```

## Known Issues
1. Sheet 5 O48/P48 reference Ottawa Altus costs instead of GTA (pre-existing template issue)
2. Sheet 13 Altus values are text strings ("$295") — works in Excel via auto-coercion
3. External workbook references in Sheet 1 rows 70+ show stale values
4. Sheet 5 F29 always points to "13-39 Storeys" regardless of building height
5. Empty unit type row (e.g., no 1-beds) shows `#DIV/0!` in $/SF column — template formula issue, needs IFERROR() from Noor

## Waiting On
- **Noor:** Expanded template (3 → 14 unit rows) — should be back (was away until ~2026-03-20)
- **Noor:** Affordable vacancy handling, financing sheet connection
- **Joanna:** 5 financing programs incoming (confirmed 2026-03-19 call) — Jeffrey (underwriter) preparing details
- **Joanna:** Decide if Debt Advisory section should show max capacity or her actual deal numbers

## Resolved
- **Kanen:** Toronto DC rates confirmed ($33,497 / $48,299 / $45,280) — using these
- **Kanen:** Mississauga waiver confirmed active (1B+D/2B/3B full waiver, 1B/Bachelor 50%)

## Future Phases
- Phase 2B: Template row expansion 3 → 14 (waiting on Noor)
- Phase 3: Deploy to Railway
- Phase 4: Joanna's proforma auto-population (revenue side — pending her approval)
- Phase 5: Pull Joanna's final deal numbers back into presentation tool
