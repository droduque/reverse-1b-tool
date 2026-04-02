---
description: Every UI change must match existing design system — no unstyled elements ever
globs: ["templates/*.html", "static/**"]
---

## UI Quality Gate

When adding or modifying ANY visible element in the upload tool or presentation tool:

1. **Check the existing CSS first.** Find how similar elements are styled (inputs, cards, buttons, labels, hints). Match exactly.
2. **Use the design tokens.** Colors from :root vars, fonts from the established stack (Open Sans body, Playfair Display headings, JetBrains Mono numbers/badges).
3. **No native browser widgets.** Replace `<input type="number">` with custom steppers, replace default checkboxes/radios with styled toggles, etc. Native controls look broken in dark themes.
4. **Test font sizes.** Nothing below 12px. Labels 15px, hints 14px, inputs 16px, card titles 12px mono.
5. **Victor's accessibility.** Text contrast, click targets min 44px, readable font sizes.

**The rule:** If a new element doesn't look like it belongs on the page, it doesn't ship. Design is not a follow-up — it's part of the feature.

Learned 2026-04-01 after construction duration field shipped unstyled (wrong input type, no matching CSS, looked broken).
