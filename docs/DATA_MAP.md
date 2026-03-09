# Data Map: 1A Proforma → Reverse 1B Model

## How the 1A Feeds the Reverse 1B

The reverse 1B model's **Sheet 1 ("1. 1A Proforma")** is literally a copy of the standalone 1A proforma file, pasted into the model with a 1-row offset. The rest of the 15-sheet model pulls from this sheet via cell references.

## 1A Proforma Cell Layout (inside Reverse 1B)

### Header
- `F2`: Project title line 1 ("Estimated Stabilized Value - Today")
- `F3`: Project address ("2240 Birchmount Road, Scarborough, ON")

### Unit Mix (Rows 7-10)
| Cell | Content | Example Value |
|------|---------|---------------|
| D7:D9 | Unit type labels | "1 Bed", "2 Bed", "3 Bed" |
| E7:E9 | Unit size (SF) | 624, 855.4, 1015 |
| F7:F9 | Unit count | 84, 68, 18 |
| G7:G9 | Unit mix % | 0.494, 0.4, 0.106 |
| H7:H9 | Total SF per type | 52416, 58167, 18270 |
| I7:I9 | Monthly rent per unit | 2490, 3155, 3675 |
| J7:J9 | $/SF | 3.99, 3.69, 3.62 |
| K7:K9 | Monthly total | 209160, 214540, 66150 |
| L7:L9 | Annual total | 2509920, 2574480, 793800 |
| D10 | "TOTAL/AVG.:" row | Totals/averages |
| F10 | Total units | 170 |
| H10 | Total rentable SF | 128,853 |
| I10 | Avg monthly rent | 2,881 |
| K10 | Total monthly rent | 489,850 |
| L10 | Total annual rent | 5,878,200 |

### Summary Fields (Rows 12-14)
| Cell | Content |
|------|---------|
| F13 | Total Residential Units |
| J13 | Net Rentable SF |
| J14 | Total Monthly Rent Revenue |

### Operating Revenues (Rows 16-28)
| Cell | Content |
|------|---------|
| K17 | Annual rent revenue |
| F18, G18 | Underground parking (spaces, monthly fee) |
| K18 | Annual parking revenue |
| F21, G21 | Storage lockers (count, monthly fee) |
| K21 | Annual storage revenue |
| F22, G22 | Submetering (units, monthly fee) |
| K22 | Annual submetering |
| F24 | Vacancy rate (rent & parking) |
| F26, G26 | Commercial retail (SF, rate $/SF) |
| K26 | Annual commercial revenue |
| F27 | Commercial vacancy rate |
| K28 | **TOTAL annual operating revenue** |

### Operating Expenses (Rows 30-40)
| Cell | Content |
|------|---------|
| H31 | Utilities (annual per unit) |
| H32 | Repairs & Maintenance (annual per unit) |
| H33 | Staffing (annual per unit) |
| H34 | Insurance (annual per unit) |
| H35 | Marketing (annual per unit) |
| H36 | General & Admin (annual per unit) |
| G37 | Management fee (% of gross) |
| F38 | Property tax rate |
| G38 | Assessed value |
| G39 | Reserve for replacement (% of gross) |
| K40 | **TOTAL annual operating expenses** |

### NOI (Row 42)
| Cell | Content |
|------|---------|
| K42 | **Net Operating Income** |

### Valuation (Rows 45-48)
| Cell | Content |
|------|---------|
| H46 | Cap rate - best case (4.25%) |
| K46 | Market value - best case |
| H47 | Cap rate - base case (4.50%) |
| K47 | Market value - base case |
| H48 | Cap rate - worst case (4.75%) |
| K48 | Market value - worst case |

## Key Assumptions Sheet (Sheet 5) — What Gets Set Per Project

| Cell | Content | Source |
|------|---------|--------|
| B4 | Project address | Manual |
| G10 | Project start date | Manual |
| E12-E16 | Schedule durations (months) | Defaults: 0, 12, 18, 11, 0 |
| F15 | Lease-up offset | Default: -3 |
| F20 | Net residential area | From 1A (H10) |
| F21 | Total amenity space | From 1A or estimated |
| F23 | Commercial/retail area | From 1A (F26) |
| F24 | Parking area below grade | Estimated (AI or manual) |
| F28 | Number of units | From 1A (F10/F13) |
| F29 | Building number of floors | Estimated ("13-39 Storeys") |
| D36 | Running cap rate | From 1A (H47 — base case) |
| E37 | Profit percentage | Default: 8% |

## What Changes Per Project (from Noor)

**Always changes:**
1. Unit mix (types, counts, sizes, rents) — rows 7-9 in 1A
2. Project address/name
3. Development charges (by municipality — Toronto uses per-unit-type rates)
4. Building area schedule (GFA, parking area)

**Sometimes changes:**
5. Cap rates (if market differs)
6. Building height range (affects Altus cost guide lookup)
7. Operating expense rates (if market differs)
8. Financing rates (if Joanna provides updated rates)

**Rarely changes (use defaults):**
9. Profit margin (8%)
10. Schedule durations
11. Professional fees (3% of hard cost)
12. Development management (2.5%)
13. Marketing (1.5 months commission + 1.5 months marketing)
14. Construction contingency (2%)
15. Financing structure (10% equity / 15% mezz / 75% regular)

## Color Convention (from User Manual)

- **BLUE cells** = user inputs/assumptions → SAFE to overwrite
- **BLACK cells** = formulas/template → DO NOT overwrite
- **GREEN cells** = formula but overridable → overwrite with caution

## Key Difference: 490 St Clair vs Birchmount

The 490 St Clair 1A has:
- 9 unit types (vs 3) including studios, dens, and affordable units
- The reverse 1B template rows 7-9 only have 3 rows for unit types
- This is the "unit mix composition" manual work Noor described
- The 1A proforma inside the reverse 1B may need additional rows inserted, or the unit types need to be consolidated into the template's structure