# Plan: SVN Rock Reverse 1B Screening Tool

## Goal
Build a single HTML file (`reverse-1b-tool.html`) that works backwards from a building's stabilized value to show how development costs break down. It's a sales tool for developer clients.

## What It Does (Plain English)
1. User enters NOI and cap rate → tool calculates what the building is worth
2. Subtracts selling costs and profit margin → shows how much is "available" for development
3. Splits that budget into categories (land, construction, etc.) by percentage
4. Shows key financial metrics (yield, IRR, equity multiple)
5. Includes a rent sensitivity slider to see how rent changes affect everything
6. Sensitivity table showing best/base/worst case scenarios

## Approach
- **Single file**: All HTML, CSS, and JavaScript inline — no frameworks, no dependencies
- **Styling**: Navy (#1e3a5f) + Orange (#e87722), Inter font from system stack, Tailwind-inspired utility approach but all hand-written CSS
- **Calculations**: All live — every input change recalculates everything instantly
- **Layout**: Header → Inputs card → Advanced Settings (collapsed) → Rent Slider → Metrics Dashboard (3 cards) → Sensitivity Table → Cost Breakdown Table → Footer

## Sections to Build
1. **Header** — Logo placeholder + title
2. **Section 1: Inputs** — Project name, units, SF, NOI, cap rate, profit margin + auto-calculated summary
3. **Section 2: Advanced Settings** — Collapsible. Timeline, cost allocation %, financing assumptions
4. **Section 3: Rent Sensitivity** — Slider with live impact display
5. **Output: Metrics Dashboard** — 3 cards: Dev Yield, IRR, Equity Multiple
6. **Output: Sensitivity Table** — Best/Base/Worst case at different cap rates
7. **Output: Cost Breakdown Table** — Category, %, Total $, Per Unit, Per SF
8. **Footer** — Disclaimer + branding + auto date

## Key Decisions
- Cap rate input: dropdown with 0.25% increments (4.0% to 7.0%) — simpler than a slider for precise values
- Profit margin: range slider (10%–30%) — visual and intuitive
- Rent slider: range input with ±$0.50 range in $0.05 steps
- IRR: simplified approximation as specified (not full DCF)
- All currency formatted with Intl.NumberFormat

## Risk / Notes
- IRR is an approximation, not a true DCF-based IRR — fine for a screening tool
- The tool is static HTML, no data is saved anywhere
- Works offline once opened in browser
