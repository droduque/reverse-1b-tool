---
description: Current project status and decisions (updated 2026-04-02)
---

## Status

- **Phase 1 (Automation):** COMPLETE. 1A → Reverse 1B in ~1 minute.
- **Phase 2 (Presentation Tool):** COMPLETE. 4 sensitivity sliders, IRR calculations. Deployed to Railway.
- **Phase 2B (Expansion):** ON HOLD. No row expansion for now — keeping weighted average consolidation (3 unit types).
- **Phase 2C (Construction Financing + Overrides):** IN PROGRESS. GFA/parking display, construction debt stack inputs, prime rate auto-fetch — code done, deploying.

## Deployment

- Live at Railway: https://earnest-celebration-production.up.railway.app
- Fran V2 template adopted 2026-03-31 (gold/slate colors, Open Sans font)
- Railway timeout/speed issues reported by Noor — needs investigation

## Current Decisions

- **No row expansion** — keeping 3-row weighted average consolidation instead of 14 rows.
- **Construction financing = construction debt** — not permanent loan. Developers care about construction phase first (Derek confirmed).
- **Financing preview removed** from presentation mode (Noor: "creates discredit"). Kept in upload form for Sheet 6.
- **Prime rate** auto-fetched from Bank of Canada Valet API (policy + 2.20%).

## Blocking Items

- ~~**Noor:** Fix template O48/P48~~ — DONE 2026-04-02, V3 template swapped in
- **Noor:** Set template default view to Normal (minor — not blocking)
- **Railway:** Speed/timeout — Procfile updated (300s timeout, 2 workers). Upgrade to Pro ($20/mo) is SVN's call.

## Next Meetings

- Tuesday April 7, 11:30 AM — Noor/Alejandro call
- Thursday (likely April 10) 1 PM — full team presentation (Derek, Joanna, Dave, research)

## 5 Test Projects (all passing)

1. Birchmount (170 units, 3 types) — the original source
2. 490 St Clair (372 units, 9 types) — largest consolidation test
3. Bayview (12 types, luxury rents $8K-$20K/mo)
4. Old Weston (445 units, 3 types) — largest unit count
5. Glenavy (9 types with walk-out townhouses)
