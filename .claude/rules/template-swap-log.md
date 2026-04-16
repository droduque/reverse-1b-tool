## Template Swap Logging

Every time `reference/REVERSE_1B_Template.xlsx` is replaced (Noor ships a new master, Fran restyles, etc.), leave a reference trail so we can track what changed and why.

### On every template swap

1. **Back up the outgoing template** as `REVERSE_1B_Template_V<N>.xlsx.bak` before overwriting. The version number matches the `template_history` entry about to be added.
2. **Keep the original source file in `reference/`** under the name Noor/Fran gave it (don't rename). Commit it alongside the active template.
3. **Bump `data_registry.json`**:
   - Update `last_updated` on the `reverse_1b_template` entry to today
   - Prepend a new object to `template_history` with:
     - `date` (YYYY-MM-DD)
     - `version` (V4, V5, etc. — match the Noor filename convention)
     - `source_file` (the original filename as delivered)
     - `backup` (path to the .bak)
     - `author` (who sent it)
     - `change` (1-2 sentences: what shifted, what formulas added, what pointers were rewired)
     - `verified` (regression evidence: same-code V-prev vs V-new diff, validator pass count, live-on-Railway confirmation)
4. **Commit message** leads with `Swap Reverse 1B template to V<N>` and cites the regression evidence.

### Before declaring the swap done

Always run:
1. Same-code regression: Birchmount (3-type) and 490 St Clair (9-type consolidation) with both V-prev and V-new, diff the JSON output. Zero numeric diffs OR explain each one.
2. Validator: both projects must pass 66/66.
3. Cross-reference audit: grep all 15 sheets for references to the changed sheet's shifted rows. Any F-cell pointing into shifted territory must be verified-updated by Noor, or flagged.
4. Live verification: POST a 1A to the Railway `/generate` endpoint, download the resulting xlsx, inspect the specific cell(s) that changed.

### Why this exists

Established 2026-04-16 after swapping V3 → V4 (Noor added Equity Multiple KPI on Sheet 3). Without a template history log, it's easy to lose track of which version introduced which KPI, which formula was rewired, and what regression evidence was gathered. When Noor or Kanen asks "when did the Equity Multiple show up?" six months from now, the answer should be in `data_registry.json`, not in a commit message that may or may not be easy to find.
