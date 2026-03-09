# Build Plan: Phase 1 — 1A to Reverse 1B Populator

## What We're Building

A Python script (`populate_reverse_1b.py`) that:
1. Reads any 1A proforma file (.xlsx or .xls)
2. Copies the Reverse 1B template (preserving all formulas)
3. Writes 1A data into the correct cells across 3 sheets
4. Outputs a ready-to-review .xlsx file

---

## Architecture (One File, Three Steps)

```
populate_reverse_1b.py
│
├── Step 1: PARSE the 1A proforma
│   ├── Dynamic row scanning (no hardcoded row numbers)
│   ├── Extract unit mix (any number of unit types)
│   ├── Extract operating revenues, expenses, NOI, valuation
│   └── Consolidate unit types into 3 groups if >3 types
│
├── Step 2: WRITE to the template copy
│   ├── Sheet 1: 1A data + internal operating assumptions
│   ├── Sheet 4: Area schedule (derived + estimated)
│   └── Sheet 5: True inputs only (durations, profit %, dev charges)
│
└── Step 3: SAVE output
    └── output/Reverse_1B_{project_name}_{date}.xlsx
```

---

## Step 1: Dynamic 1A Parser

### How It Finds Each Section

The parser scans column D and E looking for landmark text, not row numbers:

| Section | Landmark String | What We Extract |
|---------|----------------|-----------------|
| Title | "Estimated Stabilized Value" in E2 or F2 | Project name, address |
| Unit Mix | Rows between header row and "TOTAL/AVG" in D col | Type, SF, count, rent for each |
| Summary | "Total Residential Units:" in E col | Total units, total rentable SF |
| Operating Revenues | "ESTIMATED OPERATING REVENUES" in E col | Parking, storage, submetering, commercial, vacancy |
| Operating Expenses | "ESTIMATED OPERATING EXPENSES" in E col | Per-unit costs, mgmt fee, tax rate, reserve |
| NOI | "ESTIMATED NET OPERATING INCOME" in E col | NOI value |
| Valuation | "ESTIMATED VALUATION" in G col | 3 cap rates |

### Unit Mix Consolidation (when >3 types)

Groups by keyword matching on the unit type label:

| Group | Matches labels containing | Template Row |
|-------|--------------------------|-------------|
| 1-Bed | "studio", "1 bed", "bachelor" | Row 7 (D7) |
| 2-Bed | "2 bed" | Row 8 (D8) |
| 3-Bed | "3 bed", "4 bed" | Row 9 (D9) |

For each group:
- **Count** = sum of all units in group
- **SF** = weighted average (sum of count×SF / sum of count)
- **Rent** = weighted average (sum of count×rent / sum of count)

If only 1-2 types exist (no 3-bed), remaining rows get label only, count=0.

### .xls File Handling

If input is .xls, use `xlrd` to read. Same parsing logic, different library calls. No conversion needed.

---

## Step 2: Write Targets (Exact Cells)

### Sheet 1 — 1A Proforma Data

**Unit mix (rows 7-9):**
- D7, E7, F7, I7 — 1-Bed group (label, SF, count, rent)
- D8, E8, F8, I8 — 2-Bed group
- D9, E9, F9, I9 — 3-Bed group

**Operating revenues:**
- F18, G18 — Underground parking (spaces, monthly fee)
- F19, G19 — Visitor parking (spaces, fee — 0 if not in 1A)
- F20, G20 — Retail parking (spaces, fee — 0 if not in 1A)
- F21, G21 — Storage lockers (count, monthly fee)
- F24 — Vacancy rate (residential)
- F26, G26 — Commercial retail (SF, $/SF rate) — write 0, 0 if no commercial
- F27 — Commercial vacancy rate — write 0 if no commercial

**Operating expenses:**
- G37 — Management fee %
- F38 — Property tax rate
- G38 — Assessed value per unit

**Valuation:**
- H46 — Best case cap rate
- H47 — Base case cap rate
- H48 — Worst case cap rate

**Title/address:**
- F2 — "Estimated Stabilized Value - Today" (or similar)
- F3 — Project address

**Internal operating assumptions (rows 58+):**
- F62 — Building GFA (from 1A if available, else estimate: total rentable SF / 0.88)
- F64 — Amenity space (estimate: 2.5% of GFA, rounded to nearest 100)
- I93 — R&M per unit (from 1A H32 equivalent, or default 1,050)
- I109 — Staffing per unit (from 1A H33 equivalent, or default 1,200)
- F117 — Insurance per unit (from 1A H34 equivalent, or default 450)
- F122 — Marketing per unit (from 1A H35 equivalent, or default 300)
- F127 — G&A per unit (from 1A H36 equivalent, or default 250)
- I137 — Reserve % (from 1A, or default 0.02)
- F80 — Utilities $/PSF common area (default 11)

### Sheet 4 — Area Schedule

Every value cell, what Birchmount has, and our approach:

| Cell(s) | Description | Birchmount Value | Derivable from 1A? | Our Approach |
|---------|-------------|-----------------|--------------------|-|
| A2 | Address | "2240 Birchmount..." | Yes | From 1A title |
| **Section 1: Residential** |
| C7, D7 | 1-Bed (count, SF) | 84, 624 | Yes | From Sheet 1 rows 7-9 |
| C8, D8 | 2-Bed (count, SF) | 68, 855 | Yes | From Sheet 1 rows 7-9 |
| C9, D9 | 3-Bed (count, SF) | 18, 1015 | Yes | From Sheet 1 rows 7-9 |
| F7:F9 | Notes (% text) | "49% of total..." | Yes | Calculate from count/total |
| **Section 2.1: Amenities** |
| C14, D14, E14 | Fitness Centre | 1, 1200, 1200 | No | Default: 1200 SF |
| C15, D15, E15 | Party Room | 1, 1000, 1000 | No | Default: 1000 SF |
| C16, D16, E16 | Co-Working | 1, 600, 600 | No | Default: 600 SF |
| C17, D17, E17 | Games/Lounge | 1, 500, 500 | No | Default: 500 SF |
| C18, D18, E18 | Terrace/BBQ | 1, 403, 403 | No | Scale: total amenity / 5 for remainder |
| **Section 2.2: Common Areas** |
| C22, D22, E22 | Main Lobby | 1, 600, 800 | No | Default: 800 SF |
| C23, D23 | Corridors | 170, 25 | Partially | Count = total units, SF/unit = 25 |
| C24, D24 | Elevator Lobbies | 6, 60 | No | Count = estimated floors, SF = 60 |
| C25, D25 | Stairwells | 2, 600 | No | Default: 2, 600 SF each |
| C26, D26 | Elevators | 3, 60 | No | Default: 3 (or 4 if >250 units), 60 SF |
| C27, D27, E27 | Mail/Parcel | 3, 150, 300 | No | Default: 300 SF |
| C28, D28 | Garbage Rooms | 4, 200 | No | Count = est floors / 4, SF = 200 |
| C29, D29 | Mech/Elec Rooms | 2, 200 | No | Default: 2, 200 SF each |
| C30, D30 | Storage Lockers | 85, 25 | Partially | Count = from 1A storage count, SF = 25 |
| C31, D31 | Janitor Closets | 3, 40 | No | Count = est floors / 5, SF = 40 |
| **Section 3: Commercial** |
| C35, D35, E35 | Retail | 1, 4370, 4370 | Yes | SF from 1A F26. If no commercial: 0 |
| **Section 4.1: Parking** |
| C39, D39 | Underground | 162, 350 | Partially | Count from 1A F18, SF = 350/space |
| C40, D40 | Visitor | 15, 350 | Partially | Count from 1A F19, SF = 350/space |
| C41, D41 | Retail Parking | 15, 350 | Partially | Count from 1A F20, SF = 350/space |
| **Section 4.2: Back of House** |
| C45, D45, E45 | Loading Dock | 1, 300, 500 | No | Default: 500 SF |
| C46, D46, E46 | Mgmt Office | 1, 150, 200 | No | Default: 200 SF |
| C47, D47, E47 | Security | 1, 100, 150 | No | Default: 150 SF |
| C48, D48, E48 | Maintenance | 1, 200, 300 | No | Default: 300 SF |
| C49, D49, E49 | Mech Penthouse | 1, 400, 2000 | No | Scale: ~12 SF/unit |
| **Verification** |
| E64 | Target GFA | 146,346 | Yes (if in 1A) | From 1A F62 (Building GFA), or estimate: net rentable / 0.88 |

**Estimation rules for items NOT in the 1A:**

1. **Total amenity space:** ~22 SF/unit (Birchmount: 3,703 / 170 = 21.8). Use `total_units * 22`, distributed across 5 rooms.
2. **Estimated floors:** `ceil(total_units / 12)` for typical apartment (Birchmount: 170/12 ≈ 15 floors)
3. **Elevator count:** 2 if <100 units, 3 if 100-250, 4 if >250
4. **Mechanical penthouse:** ~12 SF/unit (Birchmount: 2000/170 ≈ 11.8)
5. **Parking SF/space:** Always 350 SF (industry standard for underground)
6. **Back of house total:** ~3,150 SF for typical building, scales slightly with size

### Sheet 5 — Key Assumptions (True Inputs Only)

| Cell | Value | Notes |
|------|-------|-------|
| E12 | 0 | Land purchase duration |
| E13 | 12 | Pre-development |
| E14 | 18 | Construction |
| E16 | 0 | Stabilized |
| F15 | -3 | Lease-up offset |
| E37 | 0.08 | Profit % |
| R57 | 34849 | Toronto 1-Bed DC rate |
| R58 | 50248 | Toronto 2-Bed DC rate |
| R59 | 47107 | Toronto 3-Bed DC rate |

---

## Step 3: Safety Checks

Before writing to any cell, verify it does NOT contain a formula (starts with `=`). If it does, log a warning and skip it. This protects against accidentally overwriting formula cells.

---

## Build Order

1. **Parser module** — Read 1A, extract all data, consolidate unit types
2. **Writer module** — Copy template, write to Sheet 1, Sheet 4, Sheet 5
3. **CLI wrapper** — `python populate_reverse_1b.py reference/1A_Birchmount_2240.xlsx`
4. **Test with Birchmount** — Output should reproduce the existing template values
5. **Test with 490 St Clair** — Verify consolidation works, commercial=0 handled

---

## Open Questions for Alejandro

1. **Amenity sizing:** I proposed ~22 SF/unit as a rule of thumb (based on Birchmount). Does Noor have a preferred ratio, or is this close enough for the "80% automated" goal?

2. **Floor count estimation:** I proposed `ceil(units / 12)` (12 units per floor). Is this reasonable for the projects SVN typically sees, or do they have a different assumption?

3. **Operating expense per-unit rates:** The 1A files already contain these (utilities, R&M, staffing, etc.). Should I pull them from the 1A directly, or should the tool always use the template defaults (1,050 R&M, 1,200 staffing, etc.)?

4. **Building GFA:** Birchmount's 1A has this in the internal section (F62 = 146,346). If the 1A doesn't have it, I'll estimate as `net rentable SF / 0.88`. Is that ratio reasonable?

5. **Dev charges:** Current template has Toronto rates. For Phase 1, should the tool always default to Toronto, or should we prompt the user for the city?
