# SVN Rock — Sensitivity Tool Suite: Build Plan

## What We're Building

Two React single-page apps sharing the same design system:

1. **Tool 2: Client Presentation Tool** (build first — the showstopper)
2. **Tool 1: Internal Upload Tool** (build second — uses same design system)

Both are .jsx files rendered as self-contained HTML pages. Tool 2 is purely client-side. Tool 1 wraps our existing Flask backend with a new React frontend.

---

## Existing Prototype

`branding/SVN_Rock_Reverse_1B_Presentation.jsx` — working prototype with:
- Design system (colors, fonts, card patterns) — **keep and refine**
- AnimatedNumber component — **keep**
- Slider component — **keep and improve** (needs visible custom thumb)
- MetricCard component — **keep and improve** (add tooltips)
- Basic sections: Hero, Overview, Revenue, Costs, Metrics, Sensitivity, Financing, Data Sources
- Hardcoded Birchmount data — **replace with dynamic JSON input**
- Simplified formulas — **expand to match Excel model more closely**

---

## Phase 1: Upgrade Presentation Tool (Tool 2)

Starting from the existing prototype. Four sub-phases:

### Phase 1A: Foundation & Data Layer
Replace hardcoded data with a proper JSON project structure. Expand financial formulas.

**Data structure:**
- Unit mix breakdown per type (not just averages): label, count, SF, monthly rent
- Parking: underground spaces/fee, visitor spaces/fee, retail spaces/fee
- Storage: count, fee
- Commercial: SF, $/SF rate
- Vacancy rates: residential, commercial
- OpEx breakdown: mgmt fee %, property tax rate, assessed value, insurance, R&M, staffing, marketing, G&A, utilities, reserve %
- Cap rates: best, base, worst
- Development costs: construction $/SF, soft cost %, land cost
- Financing: construction loan rate, permanent loan LTV/rate/term, equity split
- Schedule: construction months, pre-dev months, lease-up months
- Municipality, building type, DC rates per unit type

**Expanded formulas (mirror Excel chain):**
- Revenue per unit type: count × rent × 12, plus parking/storage/commercial
- OpEx per category (not a single lump sum)
- NOI = EGI - total OpEx
- Valuation at 3 cap rates
- Dev cost breakdown: land + hard costs + professional fees + dev mgmt + permits/DC + marketing + financing
- IRR approximation (merchant build)
- Permanent loan amortization, DSCR, cash-on-cash

### Phase 1B: All 7 Sections + Navigation
Build each section per the spec, upgrading the prototype:

1. **Header** — Sticky, logo left, section pills right, backdrop blur
2. **Section 1: Hero** — Gold label, Instrument Serif 56px title, building value hero, 5 overview cards
3. **Section 2: Revenue** — 2-column data rows with per-category breakdown
4. **Section 3: Dev Cost** — Animated stacked bar (6-7 cost categories, not just hard/soft), cards per category, gold total card
5. **Section 4: Key Metrics** — 4 cards with highlight states + hover tooltips
6. **Section 5: Sensitivity** — (detailed in Phase 1C)
7. **Section 6: Financing** — Permanent loan, debt service, DSCR, equity, cash-on-cash
8. **Section 7: Data Sources** — Source badges with valid-through dates

Navigation upgrades:
- Section pills track scroll position automatically
- Dot navigation or thin progress bar on right edge
- Scroll-snap between sections (optional — test if it feels natural)

### Phase 1C: Sensitivity Section (The Money Maker)
The interactive section that sells lease-up services.

**Left column — 4 sliders:**
- Rent per SF (±$1.00 from base, step $0.05)
- Cap Rate (3.00%–7.00%, step 0.25%)
- Construction Cost per SF (range around base, step $5)
- Vacancy Rate (0%–10%, step 0.5%)

**Right column — live results:**
- Building Value hero number (animates)
- **THE KILLER CALLOUT** — "A $0.10/sf rent increase = +$X.XM in building value"
  - Green tint if positive, red if negative
  - Large monospace number, impossible to miss
  - This is what Carolyn and Dave use to pitch lease-up
- Dev Yield and Equity Multiple cards, updating live
- NOI and Dev Profit compact display

**Slider improvements:**
- Visible custom thumb (gold circle, scales slightly on grab)
- Gold gradient on filled track portion
- Current value in gold JetBrains Mono next to label

### Phase 1D: Polish & Micro-interactions
- Hover tooltips on every metric (plain English)
- Card hover: elevated shadow + subtle border glow
- Section entrance animations (fade-in on scroll via IntersectionObserver)
- Test on 1440px laptop + iPad
- Performance: ensure slider drag is smooth (no animation lag)

---

## Phase 2: Internal Upload Tool (Tool 1)

### Phase 2A: React Frontend for Upload
New React UI using the same design system, replacing current Flask HTML template.

**Four screens:**
1. **Upload** — Drag-and-drop, gold dashed border on hover, .xlsx/.xls
2. **Processing** — Step indicators with checkmark animations (reading 1A, detecting municipality, pulling DC rates, generating Reverse 1B)
3. **Review** — Project summary, unit mix table, assumptions applied, warnings in gold, download button (gold CTA)
4. **Data Freshness** — Always visible panel with dataset cards and status badges (reads from data_registry.json via Flask endpoint)

Backend: existing Flask app, called via fetch to `/preview` and `/generate`.

### Phase 2B: Connect the Two Tools
- "Open in Presentation Mode" button on review screen
- Tool 1 outputs JSON matching Tool 2's input format
- Tool 2 accepts data via URL params or localStorage

---

## Phase 3: Integration & Testing

- Birchmount (3 unit types) — verify numbers match Excel
- 490 St Clair (9→3 consolidated) — verify consolidation works
- Multiple screen sizes
- Slider performance (must be buttery smooth)

---

## Build Order

```
Phase 1A  →  Phase 1B  →  Phase 1C  →  Phase 1D
[data]       [sections]   [sensitivity] [polish]

Then:
Phase 2A  →  Phase 2B  →  Phase 3
[upload UI]  [connect]    [test]
```

**Starting with Phase 1A** — data layer and expanded formulas. This is the foundation everything builds on.

---

## Files

**New:**
- `static/presentation.html` — Tool 2 (self-contained React + Babel standalone)
- `static/upload.html` — Tool 1 (React frontend for Flask)

**Modified:**
- `branding/SVN_Rock_Reverse_1B_Presentation.jsx` — Updated to match new version
- `app.py` — Add routes to serve new HTML files + JSON data endpoint

**Unchanged:**
- `populate_reverse_1b.py`, `xml_writer.py`, `data_registry.json`, `data_freshness.py`
