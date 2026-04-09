---
description: SVN Rock-specific verification steps (extends verify-completion skill)
globs: ["*.py", "*.html"]
---

## SVN Rock Verification Details

The global verify-completion skill applies (see ~/.claude/skills/verify-completion/SKILL.md).
This file adds project-specific steps.

### Web app test sequence
1. Start Flask on localhost:5001
2. POST to /preview with the 1A file (form field: "proforma")
3. POST to /generate with municipality + building type
4. Confirm 302 redirect, check warnings in the redirect URL
5. Read the generated .xlsx and .json from output/

### Output-vs-source comparison
- Read the 1A file's revenue section (rent, parking, storage, submetering, NOI)
- Read the Reverse 1B Sheet 1 cells we wrote (E18, F18, F22, etc.)
- Formula cells will show None (cached values cleared). Compute manually:
  e.g., annual submetering = count x fee x 12
- Compare to 1A annual totals. Exact match or explain the difference.

### Regression baseline
- Always re-run Birchmount (the template source project) as baseline
- Run `python3 validate_output.py` on ALL output/ files (17+ files)

### Triggers
- Any change to populate_reverse_1b.py, app.py, validate_output.py, xml_writer.py
