# Design System: SVN-Rock Reverse 1B

## 1. Visual Theme & Atmosphere

The Reverse 1B tool presents as a premium dark-mode financial SaaS application, closer to Linear or Bloomberg Terminal than a typical web form. The page opens on a deep dark canvas (`#0F1218`) with warm off-white text (`#E8E6E1`) and gold accents (`#C9993A`) that function as both brand anchor and interactive highlight. The gold-on-dark palette reads as luxury investment advisor: confident, data-driven, and deliberately opaque in a way that signals exclusivity rather than obscurity.

JetBrains Mono is the defining typographic element. Every number, badge, card title, and button uses monospace letterforms, giving the entire interface the precision of a terminal readout dressed in a luxury skin. Headings use serif faces (Playfair Display on the index page, Instrument Serif on results/presentation) for editorial contrast, while body text runs through Open Sans or DM Sans depending on the page. This serif/mono pairing creates a tension between traditional finance authority and modern data engineering.

The shadow system is built entirely around gold-tinted depth. Where most dark-mode applications use neutral black shadows (invisible against dark backgrounds), SVN-Rock uses `rgba(201,153,58,0.12)` as its ambient glow, creating a warm halo effect around elevated elements. On hover, this intensifies to `rgba(201,153,58,0.25)`, making interactions feel like gold light is emanating from within the UI. Focus rings use a 3px gold spread, turning keyboard navigation into a branded experience.

**Key Characteristics:**
- Deep dark backgrounds (`#0F1218`) with warm off-white text (`#E8E6E1`), never pure white or pure black
- Gold (`#C9993A`) as the singular accent color for all interactive and emphasis elements
- JetBrains Mono for all data values, buttons, badges, and card titles, creating monospace-as-brand
- Serif headings (Playfair Display / Instrument Serif) for editorial authority
- Gold-tinted shadows and glows instead of neutral elevation
- Conservative border-radius (8px standard, 12px cards) with no pill shapes
- Smooth 0.2-0.3s transitions on all interactive states
- Single-column centered layouts, no sidebar, no responsive mobile

**Brand Alignment Note:** Rock Advisors Inc. (rockadvisorsinc.com) uses a corporate palette of Primary Blue (`#335572`), Dark Navy (`#002868`), and Orange (`#f47c00`) with Open Sans + Gothic A1 at 7px border-radius. The current tool aesthetic deliberately diverges from the parent brand for a premium data-tool feel. Future iterations should evaluate aligning the gold accent toward the Rock Advisors orange (`#f47c00`) and incorporating the navy (`#002868`) as a secondary dark tone to bridge the gap between tool and brand.

## 2. Color Palette & Roles

### Primary
- **Gold** (`#C9993A`): Primary brand color. CTA backgrounds, accent borders, focus rings, active states, title underlines. The singular interactive color.
- **Gold Hover** (`#B8882F`): Darker gold for hover states on buttons and interactive elements.
- **Background** (`#0F1218`): Primary page background. A deep blue-black that reads as dark without the flatness of pure black.
- **Background Deep** (`#0A0D11`): Deeper variant for layered sections and page-level depth.

### Surface & Cards
- **Card Background** (`#161B24`): Elevated surface color for cards, panels, and containers.
- **Card Border** (`#1E2530`): Subtle border for card edges and dividers. Visible but not distracting.

### Text
- **Text Primary** (`#E8E6E1`): Warm off-white for headings and primary body text. Not pure white, which would feel harsh on dark backgrounds.
- **Text Dim** (`#8B8A87`): Muted warm gray for secondary text, labels, and descriptions.

### Status
- **Success** (`#3DB06B`): File upload confirmation, positive states, green indicators.
- **Error** (`#D94F4F`): Validation errors, failed states, destructive actions.
- **Blue** (`#6B8AE0`): Presentation mode accent for informational elements and secondary highlights.

### Gold Opacity Scale
Used for backgrounds, borders, and overlays at varying intensities:
- `rgba(201,153,58, 0.04)`: Barely visible tint for large surface areas
- `rgba(201,153,58, 0.05)`: Subtle background wash
- `rgba(201,153,58, 0.08)`: Light border or divider tint
- `rgba(201,153,58, 0.12)`: Standard ambient glow (shadow default)
- `rgba(201,153,58, 0.15)`: Hover background tint
- `rgba(201,153,58, 0.20)`: Button shadow, active backgrounds
- `rgba(201,153,58, 0.25)`: Strong glow (hover shadow)
- `rgba(201,153,58, 0.30)`: Maximum emphasis glow

### Rock Advisors Brand Reference (future alignment)
- **Primary Blue** (`#335572`): Main brand blue from rockadvisorsinc.com
- **Dark Navy** (`#002868`): Deep blue, could replace or complement `#0F1218` in branded contexts
- **Orange** (`#f47c00`): Accent color, natural bridge from current gold (`#C9993A`)
- **Body Text** (`#232323`): Corporate body text (light-mode only)

## 3. Typography Rules

### Font Families
- **Serif Headings**: Playfair Display 400-700 (index page), Instrument Serif (results/presentation)
- **Body**: Open Sans 300-700 (index page), DM Sans 300-700 (results/presentation)
- **Monospace**: JetBrains Mono 400-600 (data values, buttons, badges, card titles)

> **Known Inconsistency:** The index page uses Playfair Display + Open Sans while results and presentation pages use Instrument Serif + DM Sans. This should be unified. Recommendation: DM Sans for all body text, Instrument Serif for all headings. See Section 7 for details.

### Hierarchy

| Role | Font | Size | Weight | Line Height | Notes |
|------|------|------|--------|-------------|-------|
| Page Title | Playfair Display / Instrument Serif | 28-32px | 400-700 | 1.2 | Main page heading |
| Section Heading | Playfair Display / Instrument Serif | 22-26px | 400 | 1.3 | Feature section titles |
| Card Title | JetBrains Mono | 16-18px | 600 | 1.4 | Monospace for data-card headers |
| Body | Open Sans / DM Sans | 15-16px | 300-400 | 1.6 | Standard reading text |
| Body Small | Open Sans / DM Sans | 14px | 300 | 1.5 | Secondary descriptions |
| Button | JetBrains Mono | 14-15px | 500-600 | 1.0 | Uppercase, letter-spacing 0.5-1px |
| Data Value | JetBrains Mono | 16-20px | 500 | 1.2 | Financial figures, scores, metrics |
| Data Large | JetBrains Mono | 28-36px | 600 | 1.0 | Hero metric numbers in presentation |
| Badge | JetBrains Mono | 11-12px | 500 | 1.0 | Status labels, tier indicators |
| Label | Open Sans / DM Sans | 13-14px | 400 | 1.4 | Form labels, metadata |
| Caption | Open Sans / DM Sans | 12px | 300 | 1.4 | Fine print, disclaimers |

### Principles
- **Monospace as brand**: JetBrains Mono is used for all data, all buttons, all badges, and all card titles. If the element conveys a number or triggers an action, it gets monospace. This creates a "data terminal" feel across the entire interface.
- **Serif for authority**: Headings use serif typefaces to ground the tool in traditional finance. The serif/mono contrast is deliberate: editorial credibility meets engineering precision.
- **Uppercase buttons**: All button text is uppercase with subtle letter-spacing (0.5-1px), reinforcing the monospace-as-UI-chrome pattern.
- **Weight restraint**: Body text stays at 300-400. Bold (600-700) is reserved for card titles and hero data values. No weight above 700 anywhere.

## 4. Component Stylings

### Buttons

**Primary Gold**
- Background: `#C9993A`
- Text: `#0F1218` (dark on gold)
- Padding: 18px 24px
- Radius: 8px
- Font: JetBrains Mono 14-15px weight 500, uppercase, letter-spacing 0.5-1px
- Shadow: `0 4px 20px rgba(201,153,58,0.2)`
- Hover: background `#B8882F`, shadow intensifies
- Transition: 0.2s ease
- Use: Primary CTA ("Generate Report", "Upload File", "Run Analysis")

**Ghost / Outlined**
- Background: transparent
- Text: `#C9993A`
- Padding: 18px 24px
- Radius: 8px
- Border: `1px solid rgba(201,153,58,0.25)`
- Font: JetBrains Mono 14-15px weight 500, uppercase
- Hover: background `rgba(201,153,58,0.08)`, border brightens
- Use: Secondary actions ("Back", "Reset")

### Cards & Containers
- Background: `#161B24`
- Border: `1px solid #1E2530`
- Radius: 12px
- Padding: 28px
- Title accent: gold underline or left-border highlight
- Hover shadow: `0 8px 32px rgba(201,153,58,0.12)`
- Transition: 0.2-0.3s ease
- Use: Data panels, metric groups, form sections

### Inputs & Forms
- Background: `#161B24` or slightly darker
- Border: `1px solid #1E2530`
- Radius: 8px
- Text: `#E8E6E1`
- Placeholder: `#8B8A87`
- Focus: `0 0 0 3px rgba(201,153,58,0.12)` (gold ring)
- Label: `#8B8A87`, DM Sans / Open Sans 13-14px

### Upload Zone
- Border: `1px dashed #1E2530`
- Radius: 12px
- Background: `#161B24`
- Active/file-selected state: border turns `#3DB06B` (green), subtle green tint
- Icon and text centered, monospace filename display

### Sliders (Sensitivity Controls)
- Track: gradient from dark to gold
- Thumb: gold (`#C9993A`), circular
- Value display: JetBrains Mono, gold text
- Use: Presentation mode sensitivity adjustments

### Score Boxes
- Font: JetBrains Mono, 20-28px weight 600
- Color: tiered by score (green for high, gold for mid, red for low)
- Background: matching color at low opacity (0.08-0.12)
- Radius: 8px
- Use: Deal quality scores, risk ratings

### Presentation Mode (React)
- Sticky navigation bar at top
- Animated number transitions (count-up on load)
- Wider container (1100px)
- Metric card grid layout
- Sensitivity sliders with real-time recalculation
- Section-based scrolling

## 5. Layout Principles

### Spacing System
- Base unit: 4px
- Common values: 8px, 12px, 16px, 20px, 24px, 28px, 32px, 40px, 48px
- Card internal padding: 28px (consistent across all card types)
- Button padding: 18px vertical, 24px horizontal
- Form element gap: 16-20px between fields

### Container Widths
| Page | Max Width | Notes |
|------|-----------|-------|
| Reimport | 600px | Narrow, single-action focus |
| Upload / Index | 720px | Standard form width |
| Results | 800px | Wider for data tables |
| Presentation | 1100px | Full data dashboard |

### Grid & Layout
- Single-column centered for all form pages (upload, reimport)
- Results page: single column with stacked data cards
- Presentation: metric cards in responsive grid (2-3 columns), sticky nav
- No sidebar anywhere in the application
- No responsive mobile layout (desktop-only tool)

### Whitespace Philosophy
- **Generous vertical spacing**: Sections separated by 32-48px, creating clear visual chapters
- **Dense data, open chrome**: Financial figures are tightly grouped within cards, but cards themselves have generous padding (28px) and spacing between them
- **Single-column focus**: The narrow container widths (600-800px on form pages) create natural margins that feel deliberate, not wasted

### Border Radius Scale
- Standard (8px): Buttons, inputs, score boxes
- Comfortable (12px): Cards, upload zone, form containers
- Large (16px): Presentation mode cards, hero elements
- Circle (50%): Avatar-style elements, slider thumbs

## 6. Depth & Elevation

| Level | Treatment | Use |
|-------|-----------|-----|
| Flat (Level 0) | No shadow | Page background, inline text |
| Subtle (Level 1) | `0 2px 8px rgba(0,0,0,0.3)` | Resting cards, form containers |
| Gold Ambient (Level 2) | `0 4px 20px rgba(201,153,58,0.12)` | Buttons, active cards |
| Gold Elevated (Level 3) | `0 8px 32px rgba(201,153,58,0.12)` | Card hover, focused elements |
| Gold Strong (Level 4) | `0 8px 32px rgba(201,153,58,0.25)` | Modal, primary CTA hover |
| Focus Ring | `0 0 0 3px rgba(201,153,58,0.12)` | Keyboard focus, input active |

**Shadow Philosophy**: On dark backgrounds, traditional box-shadows are invisible. SVN-Rock solves this by using gold-tinted shadows exclusively. Every elevation level emits a warm gold glow rather than a dark drop-shadow, creating the impression that interactive elements are lit from within. The gold glow scale (0.12 resting, 0.25 active) provides two distinct levels of emphasis without needing to vary blur or offset. This is the core of the "luxury dark mode" feel: depth is communicated through light, not darkness.

## 7. Do's and Don'ts

### Do
- Use JetBrains Mono for all numbers, buttons, badges, and card titles. Monospace is the brand.
- Use gold (`#C9993A`) as the only accent color for interactive elements. One color, used consistently.
- Apply gold-tinted shadows (`rgba(201,153,58,...)`) for all elevation. Never use neutral shadows on dark backgrounds.
- Use `#E8E6E1` (warm off-white) for primary text, never pure `#FFFFFF`.
- Use `#0F1218` for backgrounds, never pure `#000000`.
- Keep transitions at 0.2-0.3s ease for all hover and focus states.
- Use uppercase + letter-spacing on all button text.
- Use CSS custom properties for all colors. No hardcoded hex values in component styles.
- Keep border-radius in the 8px-12px range for most elements.

### Don't
- Don't mix Open Sans and DM Sans on the same page. **FIX NEEDED:** Unify to DM Sans across all pages.
- Don't mix Playfair Display and Instrument Serif on the same page. **FIX NEEDED:** Unify to Instrument Serif across all pages.
- Don't hardcode color values in presentation mode components. **FIX NEEDED:** Some React components use inline hex instead of CSS variables.
- Don't use different container max-widths without clear justification. The current 600/720/800/1100 spread is acceptable because each page has a distinct purpose, but avoid adding new arbitrary widths.
- Don't use pill-shaped buttons or large border-radius (20px+).
- Don't add a light mode. The dark aesthetic is the product identity.
- Don't use the gold accent for large background fills. Gold is for accents, borders, text highlights, and small interactive surfaces only.
- Don't introduce new accent colors without updating this document.
- Don't use pure black text or backgrounds. Always use the warm variants (`#0F1218`, `#0A0D11`, `#E8E6E1`).

### Font Unification Roadmap
1. Replace all Open Sans imports with DM Sans 300-700
2. Replace all Playfair Display imports with Instrument Serif
3. Audit `index.html` / `index.css` for the old font references
4. Verify JetBrains Mono usage is consistent across all three page contexts
5. Update any inline `font-family` declarations in React components

## 8. Responsive Behavior

### Current State
The Reverse 1B tool is a **desktop-only** application. There is no responsive layout, no mobile breakpoints, and no touch-target optimization. This is intentional: the tool is used in office settings by financial analysts working on desktop/laptop screens.

### Container Behavior
| Viewport | Behavior |
|----------|----------|
| < 800px | No adaptation. Horizontal scroll on narrow viewports. |
| 800-1200px | Centered containers render at their max-widths with auto margins |
| > 1200px | Presentation mode (1100px) centers with generous side margins |

### If Mobile Support Is Added Later
- Minimum touch target: 44px (iOS standard)
- Stack metric card grids to single column below 768px
- Collapse presentation sticky nav to a hamburger or tab strip
- Maintain JetBrains Mono for data values at all sizes (minimum 14px on mobile)
- Gold focus rings must remain visible on touch devices
- Consider the Rock Advisors brand palette for a mobile-friendly lighter theme

### Print Behavior
- Presentation mode should support `@media print` with white background, dark text, and gold accents preserved as border/text color
- Hide interactive elements (sliders, nav) in print output

## 9. Agent Prompt Guide

### Quick Color Reference
- Primary accent: Gold (`#C9993A`)
- Accent hover: Gold Dark (`#B8882F`)
- Background: Deep Dark (`#0F1218`)
- Background deeper: Darkest (`#0A0D11`)
- Card surface: Dark Card (`#161B24`)
- Card border: Subtle Border (`#1E2530`)
- Text primary: Warm White (`#E8E6E1`)
- Text secondary: Muted Gray (`#8B8A87`)
- Success: Green (`#3DB06B`)
- Error: Red (`#D94F4F`)
- Info (presentation): Blue (`#6B8AE0`)
- Gold glow (shadow): `rgba(201,153,58,0.12)`
- Gold glow strong: `rgba(201,153,58,0.25)`

### Example Component Prompts
- "Create a data card on `#0F1218` background. Card uses `#161B24` bg, `1px solid #1E2530` border, 12px radius, 28px padding. Title in JetBrains Mono 16px weight 600, color `#C9993A`. Body text in DM Sans 15px weight 300, line-height 1.6, color `#E8E6E1`. Hover adds `0 8px 32px rgba(201,153,58,0.12)` shadow with 0.2s transition."
- "Build a primary button: `#C9993A` background, `#0F1218` text, JetBrains Mono 14px weight 500 uppercase, letter-spacing 0.5px, 18px 24px padding, 8px radius. Shadow `0 4px 20px rgba(201,153,58,0.2)`. Hover darkens to `#B8882F`."
- "Design an upload zone: `#161B24` background, `1px dashed #1E2530` border, 12px radius. Center-aligned icon and text in `#8B8A87`. On file select, border changes to `#3DB06B` (solid), subtle green tint on background."
- "Create a score display: JetBrains Mono 28px weight 600. Green (`#3DB06B`) for scores above 80, gold (`#C9993A`) for 60-80, red (`#D94F4F`) below 60. Background uses the matching color at 0.08 opacity. 8px radius container."
- "Build a metric card for presentation mode: `#161B24` bg, 16px radius, 28px padding. Label in DM Sans 13px weight 400, `#8B8A87`. Value in JetBrains Mono 32px weight 600, `#E8E6E1`. Animated count-up on load. Gold left-border accent (3px solid `#C9993A`)."

### Iteration Guide
1. Every number visible to the user must be in JetBrains Mono. No exceptions.
2. Gold (`#C9993A`) is the only accent. Do not introduce secondary accent colors.
3. Shadow formula on dark mode: `0 Ypx Bpx rgba(201,153,58, OPACITY)` where opacity is 0.12 (resting) or 0.25 (active/hover).
4. Text is `#E8E6E1` (primary) or `#8B8A87` (secondary). Never `#FFFFFF` or `#999999`.
5. Background layers: page (`#0F1218`), card (`#161B24`), border (`#1E2530`). Three levels of dark.
6. All buttons are JetBrains Mono, uppercase, with letter-spacing. No sentence-case buttons.
7. Transitions are 0.2s for color/opacity changes, 0.3s for shadow/transform changes.
8. When adding new components, check if CSS variables exist before hardcoding values. All colors should reference `--gold`, `--bg`, `--card-bg`, `--text`, `--text-dim`, etc.
9. **Rock Advisors alignment**: If building client-facing or branded contexts, consider substituting `#002868` for deep backgrounds and `#f47c00` for accents. Keep the dark-mode structure but shift the palette.
