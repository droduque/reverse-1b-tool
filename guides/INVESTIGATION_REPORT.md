# Deep Investigation Report: Reverse 1B Automation

Date: 2026-03-04

---

## Step 1: 1A Proforma Files

### 1A Birchmount (reference/1A_Birchmount_2240.xlsx)

**Sheet:** `1A Proforma` (1 sheet)

**Unit Mix (rows 6-9):**
| Row | Type | SF | Count | Rent |
|-----|------|----|-------|------|
| 6 | 1 Bed | 624 | 84 | $2,490 |
| 7 | 2 Bed | 855.4 | 68 | $3,155 |
| 8 | 3 Bed | 1,015 | 18 | $3,675 |
| 9 | TOTAL | 757.96 avg | 170 | $2,881 avg |

**Key values confirmed:**
- Total units: 170 (F9 standalone / F12 standalone)
- Net rentable SF: 128,853 (J12 standalone)
- Parking: 162 spaces @ $200/mo
- Storage: 100 @ $40/mo
- Commercial: 4,370 SF @ $40/SF
- Vacancy: 3% residential, 4% commercial
- Property tax rate: 0.754087%, assessed value: $450,000
- Management fee: 4.25%
- Reserve: 2%
- Cap rates: 4.25% / 4.50% / 4.75%

**Layout matches CLAUDE.md:** YES. All cell positions confirmed.

**Internal calculation section (rows 58-142):** Contains detailed workups for utilities, R&M, staffing, insurance, marketing, G&A, property tax, and reserves. Many formulas reference an EXTERNAL workbook `[2]Typical Conv.Operating Expenses` (which won't be available). Key hardcoded values used by the proforma:
- `F80`: 11 (utilities $/PSF common area) → feeds H80 → feeds H31
- `I93`: 1,050 (R&M per unit) → feeds H32
- `I109`: 1,200 (staffing per unit) → feeds H33
- `F117`: 450 (insurance per unit) → feeds H34
- `F122`: 300 (marketing per unit) → feeds H35
- `F127`: 250 (G&A per unit) → feeds H36
- `I137`: 0.02 (reserve %) → feeds G39

### 1A 490 St Clair (reference/1A_490_St_Clair.xls)

**Sheets:** `Proforma w Affordable`, `Utilities`, `CMHC`, `Compatibility Report`, `Geo Assessments`

**Unit Mix (rows 6-15):**
| Row | Type | SF | Count | Rent |
|-----|------|----|-------|------|
| 6 | Studio | 420.25 | 15 | $2,675 |
| 7 | 1 Bed | 599.3 | 88 | $3,350 |
| 8 | 1 Bed Affordable | 450 | 11 | $1,715 |
| 9 | 1 Bed + Den | 675 | 88 | $3,650 |
| 10 | 2 Bed | 800 | 65 | $4,150 |
| 11 | 2 Bed Affordable | 625 | 12 | $1,985 |
| 12 | 2 Bed + Den | 875 | 43 | $4,450 |
| 13 | 3 Bed | 1,000 | 47 | $5,200 |
| 14 | 3 Bed Affordable | 925 | 3 | $2,268 |
| 15 | TOTAL | 726.6 avg | 372 | $3,793 avg |

**Key values confirmed:**
- Total units: 372 (F18)
- Net rentable SF: 270,294 (J18)
- Parking: 158 underground @ $250/mo
- Storage: 186 @ $100/mo
- Commercial: NOT present (no F25/G25 values)
- Vacancy: 3.5% residential
- Property tax rate: 0.754087%, assessed value: $620,000
- Cap rates: 4.25% / 4.50% / 4.75%

**Layout discrepancy from CLAUDE.md:**
- CLAUDE.md says "rows 16-28 standalone" for operating revenues → Actually rows 21-29 for 490 St Clair
- The 490 St Clair 1A has 9 unit types (rows 6-14) vs 3 (rows 6-8) for Birchmount
- The TOTAL row shifts down: row 9 (Birchmount) vs row 15 (490 St Clair)
- Summary rows also shift: F12/J12 (Birchmount) vs F18/J18 (490 St Clair)
- **The entire proforma layout shifts down by 6 rows** because of the additional unit type rows

**CRITICAL FINDING:** The "standardized layout" described in CLAUDE.md is only standard for the Birchmount file. The 490 St Clair file has a different row structure because it has more unit types. The operating revenue section starts at row 21 instead of row 15.

---

## Step 2: Reverse 1B Template Analysis

### All 15 Sheets Overview

| # | Sheet Name | Formulas | Values | Purpose |
|---|-----------|----------|--------|---------|
| 1 | 1. 1A Proforma | 241 | 283 | Input: The 1A proforma data + internal calcs |
| 2 | 2. Rev 1B Exec Summary | 122 | 59 | Output: Summary dashboard |
| 3 | 3. Headline #s | 20 | 34 | Output: Cover page + headline metrics |
| 4 | 4. Area Schedule | 31 | 177 | Input: Building area breakdown |
| 5 | 5. Key Assumptions | 138 | 174 | Mixed: Some inputs, many formula references |
| 6 | 6. Debt Stack & Financing | 23 | 33 | Calc: Debt structure |
| 7 | 7. Op Rev and Exp | 179 | 81 | Calc: Detailed revenue/expense |
| 8 | 8. Schedule | 469 | 12 | Calc: Monthly timeline |
| 9 | 9. Development Costs | 184 | 99 | Calc: Full cost breakdown |
| 10 | 10. Development Cash Flow | 8,055 | 164 | Calc: Monthly cash flow model |
| 11 | 11. 10-Yr Cash Flow IRR | 1,088 | 200 | Calc: Hold scenario analysis |
| 12 | 12. Sensitivity | 20 | 27 | Input: Scenario selector |
| 13 | 13. Altus Cost Guide 25 | 0 | 299 | Reference: Construction costs (all static) |
| 14 | 14. Sensitivity 2 | 0 | 10 | Input: Rent/cost sensitivity multipliers |
| 15 | 15. Headline #s | 34 | 51 | Output: Sensitivity comparison |

### Sheet 1 ("1. 1A Proforma") — Cell-by-Cell Comparison

**Row offset confirmed: Exactly +1 row consistently.**

| Content | Standalone Row | Template Row |
|---------|---------------|-------------|
| Header (title) | E2 | F2 |
| Address | — | F3 |
| Column headers | Row 5 | Row 6 |
| Unit type 1 | Row 6 | Row 7 |
| Unit type 2 | Row 7 | Row 8 |
| Unit type 3 | Row 8 | Row 9 |
| TOTAL/AVG | Row 9 | Row 10 |
| Total units | F12 | F13 |
| Operating revenues | Rows 15-27 | Rows 16-28 |
| Operating expenses | Rows 29-39 | Rows 30-40 |
| NOI | K41 (standalone) | K42 |
| Valuation | Rows 44-47 | Rows 45-48 |
| Internal calcs | Rows 57+ | Rows 58+ |

**Columns also shift:** In the standalone file, the title is in E2. In the template, it's in F2. The address is in F3 (template only — standalone has address embedded in the title).

**INPUT (non-formula) cells in Sheet 1 — the ONLY cells we can safely write to:**

Unit Mix (rows 7-9):
- D7:D9 — Unit type labels
- E7:E9 — Unit size (SF)
- F7:F9 — Unit count
- I7:I9 — Monthly rent per unit

Operating Revenues:
- F18, G18 — Underground parking (spaces, monthly fee)
- F19, G19 — Visitor parking
- F20, G20 — Retail parking
- F21, G21 — Storage lockers
- F24 — Vacancy rate
- G25 — "Rate" label (don't touch)
- F26, G26 — Commercial (SF, $/SF rate)
- F27 — Commercial vacancy rate

Operating Expenses:
- G37 — Management fee %
- F38 — Property tax rate
- G38 — Assessed value per unit

Valuation:
- H46, H47, H48 — Cap rates

Internal Section:
- F62 — Building GFA
- F64 — Amenity space
- F80 — Utilities $/PSF
- F87:G89 — R&M line items
- F100:I105 — Staffing line items
- F117 — Insurance per unit
- F122 — Marketing per unit
- F127 — G&A per unit
- I93 — R&M per unit (rounded, used by H32)
- I109 — Staffing per unit (used by H33)
- I137 — Reserve % (used by G39)
- H75 — Peter Wyse utility estimate
- H130 — Property tax % of value

**Formula cells in Sheet 1 — DO NOT TOUCH:**
- G7:G9 (unit mix %)
- H7:H9 (total SF)
- J7:J9 ($/SF)
- K7:K9 (monthly total)
- L7:L9 (annual total)
- All TOTAL/AVG row (E10:L10)
- F13, J13, J14 (summary)
- All Operating Revenue calculated columns
- H31:H36 (expense per unit — these are formulas pulling from internal section)
- F31:F36 (these are =F13 formulas)
- All NOI and valuation calculated fields
- G22 — References EXTERNAL workbook `[2]Typical Conv.Operating Expenses`
- G39 — References I137

### Sheet 4 ("4. Area Schedule") — CRITICAL

This sheet is a **detailed building area breakdown** with hardcoded values:
- Unit counts and sizes for each bedroom type (C7:E9)
- Amenity spaces (individual rooms with SF)
- Common areas (corridors, elevators, etc.)
- Commercial areas
- Parking spaces and area
- Back of house areas

**These are the cells that feed Sheet 5's Building Area Summary (F20:F25).**

Key input cells:
- C7:D9 — Unit counts and sizes (must match Sheet 1)
- C14:E18 — Amenity rooms
- C22:E31 — Common area items
- E35 — Commercial SF
- C39:D41 — Parking (counts and SF per space)
- E45:E49 — Back of house areas
- E64 — Target GFA (reference value)

### Sheet 5 ("5. Key Assumptions") — MOSTLY FORMULAS

**CRITICAL FINDING:** Most cells in Sheet 5 that CLAUDE.md says to "update per project" are actually FORMULAS, not inputs. They pull from other sheets.

| Cell | CLAUDE.md says | Actually contains |
|------|---------------|-------------------|
| B4 | "Project address" | FORMULA: `='3. Headline #s'!A12` |
| G10 | "Project start date" | FORMULA: `=TODAY()` |
| F20 | "Net residential area" | FORMULA: `='4. Area Schedule'!E54` |
| F21 | "Total amenity space" | FORMULA: `='4. Area Schedule'!E55` |
| F23 | "Commercial/retail area" | FORMULA: `='4. Area Schedule'!E57` |
| F24 | "Parking area" | FORMULA: `='4. Area Schedule'!E58` |
| F28 | "Number of units" | FORMULA: `='7. Op Rev and Exp'!E20` |
| F29 | "Building floor range" | FORMULA: `='13. Altus Cost Guide 25'!A7` |
| D36 | "Running cap rate" | FORMULA: `='7. Op Rev and Exp'!D56` |

**Actual INPUT cells in Sheet 5 (theme=8, blue):**
- E12:E16 — Schedule durations (0, 12, 18, formula, 0)
- F15 — Lease-up offset (-3)
- E37 — Profit percentage (0.08)
- E69 — Mezzanine debt % (0.15)
- E70 — Regular debt % (0.75)
- I69, J69 — Mezz interest components (0.0445, 0.035)
- I70, J70 — Regular debt interest components (0.0445, 0.01)

**Actual INPUT cells (theme=1, black/dark — default assumptions):**
- D45 — Land closing contingency (0.05)
- D49 — Construction contingency (0.02)
- D51 — Professional fees % (0.03)
- D52 — Prof fees contingency (0.05)
- D54 — Development management % (0.025)
- D57 — Permits contingency (0.05)
- D58 — Submeter credit ($600)
- D61 — Commission months (1.5)
- D62 — Marketing months (1.5)
- D74 — Financing fees % (0.01)
- D75 — Financing contingency (0.005)
- R57 — 1-Bed DC rate ($34,849)
- R58 — 2-Bed DC rate ($50,248)
- R59 — 3-Bed DC rate ($47,107)

**Note:** E15 (Lease-up duration) is a FORMULA: `='7. Op Rev and Exp'!E20/15` (units divided by 15 = months to lease up at ~15 units/month).

### Sheet 7 ("7. Op Rev and Exp") — THE KEY INTERMEDIARY

This sheet pulls **directly** from Sheet 1 for:
- Unit types: B16:B18 ← D7:D9
- Unit SF: C16:C18 ← E7:E9
- Unit counts: E16:E18 ← F7:F9
- Monthly rents: G16:G18 ← I7:I9
- Parking: C24:D26 ← F18:G20
- Storage: C27:D27 ← F21:G21
- Submetering: C28:D28 ← F22:G22
- Commercial: C29:D29 ← F26:G26
- Vacancy: C33 ← F24
- All expenses: C39:E47 ← F31:H39

**Row 19 is empty** — it's a blank 4th unit type row. The Exec Summary references it as "Res 2B part" but it's currently unused.

### Cross-Sheet References to Sheet 1

Only **two** sheets reference Sheet 1 directly:
1. **Sheet 7 (Op Rev and Exp)** — 30+ references (unit mix, revenues, expenses)
2. **Sheet 12 (Sensitivity)** — 3 references (cap rates: H46, H47, H48)
3. **Sheet 3 (Headline #s)** — 1 reference (address: F3)

All other sheets get their data through Sheet 7 → Sheet 5 → downstream.

### Cross-Sheet References to Sheet 5

- Sheet 6 (Debt) — 4 references
- Sheet 8 (Schedule) — 8 references (durations, offsets)
- Sheet 9 (Dev Costs) — 14 references (all cost assumptions)
- Sheet 10 (Cash Flow) — 1 reference (equity)
- Sheet 12 (Sensitivity) — 2 references (construction period, lease-up)

---

## Step 3: Example & Inputs File (Reverse 1B - Example & Inputs.xlsx)

Categorized all ~100 input parameters:

### Must Change Per Project (from the 1A)
- Unit mix (types, counts, SF, rents) — comes from 1A
- Project address — comes from 1A
- Total units — comes from 1A
- Cap rates — comes from 1A (can use defaults)
- Parking spaces/fees — comes from 1A
- Storage count/fees — comes from 1A
- Commercial SF/rate — comes from 1A
- Vacancy rates — comes from 1A
- Property tax rate/assessed value — comes from 1A
- Operating expense per-unit rates — comes from 1A

### Might Change Per Project
- Development charges (R57:R59) — city-specific, current values are Toronto
- Building floor range — affects Altus cost lookup
- Altus construction cost $/SF — reference data, changes by building type
- Schedule durations (E12:E16) — project-specific estimates
- Profit percentage (E37) — might be 8%, 10%, or 20%
- Sensitivity rent/cost multipliers (D6, D8 on Sheet 14)
- Scenario selector (E8 on Sheet 12)

### Leave as Default
- Land closing contingency (5%)
- Construction contingency (2%)
- Professional fees (3% of hard cost)
- Prof fees contingency (5%)
- Development management (2.5%)
- Marketing (1.5 months commission + 1.5 months marketing)
- Financing structure (10% equity / 15% mezz / 75% regular)
- Interest rates (4.45% prime + margins)
- Financing fees (1%) and contingency (0.5%)
- Submeter credit ($600/unit)
- Selling cost percentage (1%)
- Revenue/cost inflation (2%)
- NOI coverage (1.1x)
- Max LTV (75%)
- Permanent loan rate (3%)
- Loan term (25 years)
- All tax calculation parameters

---

## Step 4: Hard Problems Identified

### 1. Row Offset: Standalone 1A → Template Sheet 1

**Answer: Exactly +1 row, consistent across ALL sections.**

- Unit mix: rows 6-8 → 7-9
- Total: row 9 → 10
- Summary: row 12 → 13
- Operating revenues: rows 15-27 → 16-28
- Operating expenses: rows 29-39 → 30-40
- NOI: row 41 → 42
- Valuation: rows 44-47 → 45-48

**Column offset:** Title moves from E2 to F2. Address appears in F3 (template only).

**HOWEVER** — this offset is only valid for the Birchmount format (3 unit types). The 490 St Clair file has a completely different row structure because of its 9 unit types.

### 2. Unit Mix: 9 Types → 3 Rows

**Rows available:** Template has exactly 3 unit type rows (7, 8, 9) between the header (row 6) and TOTAL (row 10). There are NO hidden rows.

**Formulas that reference rows 7-9 SPECIFICALLY:**

In Sheet 1 (internal):
- E10: `=SUMPRODUCT(E7:E9,F7:F9)/F10`
- F10: `=SUM(F7:F9)`
- G10: `=SUM(G7:G9)`
- H10: `=SUM(H7:H9)`
- K10: `=SUM(K7:K9)`
- L10: `=SUM(L7:L9)`

In Sheet 7:
- B16: `='1. 1A Proforma'!D7`  E16: `='1. 1A Proforma'!F7`  G16: `='1. 1A Proforma'!I7`
- B17: `='1. 1A Proforma'!D8`  E17: `='1. 1A Proforma'!F8`  G17: `='1. 1A Proforma'!I8`
- B18: `='1. 1A Proforma'!D9`  E18: `='1. 1A Proforma'!F9`  G18: `='1. 1A Proforma'!I9`

**If we INSERT rows, these SUM ranges (F7:F9) would NOT auto-expand** because openpyxl doesn't adjust formula references when inserting rows. This would break the model.

**Recommended approach: Consolidate 9 unit types into 3 rows.**

Proposed grouping for 490 St Clair:
| Template Row | Consolidates | Units | Weighted Avg SF | Weighted Avg Rent |
|-------------|-------------|-------|----------------|-------------------|
| Row 7 "1 Bed" | Studio + 1 Bed + 1 Bed Affordable + 1 Bed + Den | 15+88+11+88 = 202 | weighted avg | weighted avg |
| Row 8 "2 Bed" | 2 Bed + 2 Bed Affordable + 2 Bed + Den | 65+12+43 = 120 | weighted avg | weighted avg |
| Row 9 "3 Bed" | 3 Bed + 3 Bed Affordable | 47+3 = 50 | weighted avg | weighted avg |

Total: 202 + 120 + 50 = 372 ✓

### 3. Circular References

**No true circular references detected.** The flow is one-directional:

```
Sheet 1 (1A Proforma)
  → Sheet 7 (Op Rev and Exp)
    → Sheet 5 (Key Assumptions)
      → Sheet 9 (Development Costs)
        → Sheet 10 (Development Cash Flow)
          → Sheet 11 (10-Yr Cash Flow IRR)
```

Sheet 5 pulls from Sheet 7 (cap rate, units), and Sheet 9 pulls from Sheet 5. There's no loop back.

**However:** Sheet 5 F73 references `'9. Development Costs'!H78` (interest cost) and Sheet 9 references Sheet 5 cost assumptions. In Excel, this would be resolved by iterative calculation. In openpyxl (which doesn't evaluate), this isn't our problem — we're preserving formulas, not computing values.

### 4. Named Ranges and Data Validations

**Named ranges found:**
- `AltusCC`: #REF! (broken reference)
- `AltusParking`: #REF! (broken reference)
- `Proforma`: #REF! (broken reference)
- Several CMHC and PRIZM references pointing to external workbook `[1]`

**These broken named ranges are pre-existing** — they existed in the template before we touched it. They reference external workbooks that aren't included. They should not affect our automation.

**Data validations:** None found.

**Merged cells:** Present in several sheets but mostly headers/titles. Not in the data entry areas we need to modify.

**Hidden rows:**
- Sheet 1: Row 50 (hidden)
- Sheet 2: Rows 31-33 (hidden)
- Sheet 9: Rows 49-50, 56-57, 71-74, 76 (hidden)
- Sheet 10: Row 9 (hidden)

These hidden rows don't affect our automation.

### 5. Sheet 5 Formula vs Input Analysis

**Formulas pulling from Sheet 1 (via Sheet 7):**
- F20 ← Area Schedule ← Sheet 1 unit mix areas
- F21 ← Area Schedule ← manual
- F28 ← Sheet 7 E20 ← Sheet 1 F10
- F29 ← Sheet 13 A7 (building type)
- D36 ← Sheet 7 D56 ← Sheet 12 ← Sheet 1 H47

**Hardcoded inputs we DO need to update:**
- E12-E16: Schedule durations (default or manual)
- F15: Lease-up offset (-3)
- E37: Profit % (default 8%)
- R57-R59: Development charges per unit type (city-specific)

**Cells we DON'T touch — they cascade automatically:**
- B3, B4 (project name/address — flows from Sheet 3 ← Sheet 1)
- G10 (start date — uses =TODAY())
- F20-F25 (building areas — flow from Sheet 4)
- F28 (units — flows from Sheet 7 ← Sheet 1)
- Everything else in the cost section (formulas)

### 6. Things That Worry Me

1. **External workbook references in Sheet 1:** Cells G22 (submetering), and rows 70-77, 92-97, 107-113, 115-116, 120, 125-126, 132 all reference `[2]Typical Conv.Operating Expenses`. When our output file is opened without that workbook, these cells will show stale values. This is pre-existing (same issue in the template) but worth noting.

2. **The Altus Cost Guide values are STRINGS, not numbers.** Sheet 13 stores costs as "$295", "$385" etc. Sheet 5 cell O48 reads `='13. Altus Cost Guide 25'!H7` — this pulls the string "$295". Excel may auto-convert, but openpyxl won't. If we change the building type row reference (A7 = "13-39 Storeys"), the hard cost lookup changes. Currently A7 is "13-39 Storeys" and F7/G7 are "$295"/"$385". If the building is shorter, we'd need to point to A6/F6/G6.

3. **Sheet 4 (Area Schedule) needs manual/estimated data.** The amenity spaces, common areas, parking SF per space, back of house — these aren't in the 1A. For Phase 1, we'll need sensible defaults or estimates. The template currently has Birchmount-specific values (corridor 25 SF/unit, 162 parking stalls at 350 SF each, etc.)

4. **The 490 St Clair file has NO commercial retail.** The template's commercial section (F26, G26) has values for Birchmount. For 490 St Clair, we'd need to write 0 to these cells, which changes the revenue mix.

5. **The submetering formula references an external workbook.** G22 = `='[2]Typical Conv.Operating Expenses'!BU96`. This pulls a monthly fee. For a new project, this cell's value will be stale. We may need to overwrite it with a hardcoded value.

6. **Sheet 12 (Sensitivity) scenario selector E8 = 1** means "Base Case" runs. The CHOOSE functions throughout the model use this. If we change nothing here, base case runs — which is correct for initial output.

7. **Sheet 14 (Sensitivity 2) multipliers D6=1, D8=1, D10=1.** These are rent, operating cost, and construction cost multipliers applied throughout Sheet 7 and the cash flow. If someone changes these to test sensitivity, the output changes. They should stay at 1 for our automation.

---

## What We Actually Need to Write To

Based on this analysis, the automation needs to update these cells:

### Sheet 1 — Primary Data Entry
| Cells | Content | Source |
|-------|---------|--------|
| F2 | Title line | 1A title |
| F3 | Address | Extracted from 1A title |
| D7:D9 | Unit type labels | 1A (consolidated if >3 types) |
| E7:E9 | Unit sizes | 1A (weighted avg if consolidated) |
| F7:F9 | Unit counts | 1A (summed if consolidated) |
| I7:I9 | Monthly rents | 1A (weighted avg if consolidated) |
| F18, G18 | Parking underground | 1A |
| F19, G19 | Visitor parking | 1A |
| F20, G20 | Retail parking | 1A |
| F21, G21 | Storage lockers | 1A |
| F24 | Vacancy rate | 1A |
| F26, G26 | Commercial retail | 1A (or 0 if none) |
| F27 | Commercial vacancy | 1A (or 0) |
| G37 | Management fee % | 1A |
| F38 | Property tax rate | 1A |
| G38 | Assessed value | 1A |
| H46:H48 | Cap rates | 1A |

### Sheet 1 — Internal Section (Operating Assumptions)
| Cells | Content | Source |
|-------|---------|--------|
| F62 | Building GFA | Estimated or from 1A |
| F64 | Amenity space SF | Estimated (2-3% of GFA) |
| F80 | Utilities $/PSF common | Default: 11 |
| I93 | R&M per unit | From 1A or default: 1,050 |
| I109 | Staffing per unit | From 1A or default: 1,200 |
| F117 | Insurance per unit | From 1A or default: 450 |
| F122 | Marketing per unit | From 1A or default: 300 |
| F127 | G&A per unit | From 1A or default: 250 |
| I137 | Reserve % | From 1A or default: 0.02 |

### Sheet 4 — Area Schedule
| Cells | Content | Source |
|-------|---------|--------|
| C7:D9 | Unit counts and sizes | Must match Sheet 1 |
| C14:E18 | Amenity rooms | Estimated |
| C39:D41 | Parking counts/SF | From 1A + estimated SF/space |
| E35 | Commercial SF | From 1A |
| E64 | Target GFA | Estimated |

### Sheet 5 — Key Assumptions (only the true inputs)
| Cells | Content | Source |
|-------|---------|--------|
| E12-E14, E16 | Schedule durations | Defaults: 0, 12, 18, 0 |
| F15 | Lease-up offset | Default: -3 |
| E37 | Profit % | Default: 0.08 |
| R57:R59 | Dev charges per unit type | City-specific (Toronto defaults) |

### Sheet 13 — Altus Cost Guide (reference only)
F29 on Sheet 5 is a formula pointing to Sheet 13 A7. Currently A7 = "13-39 Storeys". If the building is a different type, we'd need to update the F29 formula or modify which row the lookup references. **For Phase 1, leave as-is.**
