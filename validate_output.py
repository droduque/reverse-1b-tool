"""
SVN Rock — Post-Generation XLSX Validator
==========================================
Opens a generated Reverse 1B file at the raw XML level and checks for
common bugs: string-typed numbers, overwritten formulas, stale cached
values, missing fullCalcOnLoad, etc.

Usage:
    # Validate a single file with parsed data dict
    from validate_output import validate_output
    result = validate_output("output/file.xlsx", parsed_data)

    # Validate all output files (re-parses their 1A sources)
    python validate_output.py
"""

import os
import sys
import re
import zipfile
from xml.etree import ElementTree as ET

NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'

# Birchmount template fingerprints — if we see these in rows 7-9,
# the template's cached values weren't recalculated
BIRCHMOUNT_FINGERPRINTS = {
    170,      # total units
    128853,   # total rentable SF
    489850,   # monthly rent total
    5878200,  # annual rent total
}


def _read_sheet_xml(zf, sheet_path):
    """Read and parse a sheet's XML from the XLSX zip."""
    raw = zf.read(sheet_path)
    root = ET.fromstring(raw)
    return root, raw


def _read_shared_strings(zf):
    """Parse shared strings table, return list of strings."""
    raw = zf.read('xl/sharedStrings.xml')
    root = ET.fromstring(raw)
    strings = []
    for si in root.findall(f'{{{NS}}}si'):
        t = si.find(f'{{{NS}}}t')
        if t is not None and t.text is not None:
            strings.append(t.text)
        else:
            parts = []
            for r in si.findall(f'{{{NS}}}r'):
                rt = r.find(f'{{{NS}}}t')
                if rt is not None and rt.text:
                    parts.append(rt.text)
            strings.append(''.join(parts))
    return strings


def _get_cell(sheet_root, cell_ref):
    """
    Find a cell element in a sheet. Returns (cell_element, value, cell_type, has_formula).
    value is the raw <v> text. cell_type is the 't' attribute (None, 's', 'str', 'b', etc).
    """
    col_letter, row_num = re.match(r'^([A-Z]+)(\d+)$', cell_ref).groups()
    row_num = int(row_num)

    sheet_data = sheet_root.find(f'{{{NS}}}sheetData')
    if sheet_data is None:
        return None, None, None, False

    for row_el in sheet_data.findall(f'{{{NS}}}row'):
        if int(row_el.get('r', '0')) == row_num:
            for cell_el in row_el.findall(f'{{{NS}}}c'):
                if cell_el.get('r') == cell_ref:
                    v_el = cell_el.find(f'{{{NS}}}v')
                    f_el = cell_el.find(f'{{{NS}}}f')
                    val = v_el.text if v_el is not None else None
                    ctype = cell_el.get('t')
                    return cell_el, val, ctype, (f_el is not None)
            break
    return None, None, None, False


def _resolve_value(raw_val, cell_type, shared_strings):
    """Convert raw cell value + type into a Python value."""
    if raw_val is None:
        return None
    if cell_type == 's':
        idx = int(raw_val)
        return shared_strings[idx] if idx < len(shared_strings) else f"<string #{idx}>"
    try:
        # Try int first, then float
        if '.' in raw_val or 'E' in raw_val or 'e' in raw_val:
            return float(raw_val)
        return int(raw_val)
    except (ValueError, TypeError):
        return raw_val


def validate_output(xlsx_path, parsed_data):
    """
    Validate a generated Reverse 1B file against the source data.

    Args:
        xlsx_path: path to the generated .xlsx file
        parsed_data: dict returned by parse_1a() — the original parsed 1A data

    Returns:
        dict with keys: passed, errors, warnings, checks_run, checks_passed
    """
    errors = []
    warnings = []
    checks_run = 0
    checks_passed = 0

    def check(passed, msg, is_error=True):
        nonlocal checks_run, checks_passed
        checks_run += 1
        if passed:
            checks_passed += 1
        else:
            (errors if is_error else warnings).append(msg)

    # --- Open the XLSX as a zip ---
    if not os.path.exists(xlsx_path):
        return {'passed': False, 'errors': [f"File not found: {xlsx_path}"],
                'warnings': [], 'checks_run': 1, 'checks_passed': 0}

    with zipfile.ZipFile(xlsx_path, 'r') as zf:
        shared_strings = _read_shared_strings(zf)
        sheet1_root, _ = _read_sheet_xml(zf, 'xl/worksheets/sheet1.xml')
        sheet4_root, _ = _read_sheet_xml(zf, 'xl/worksheets/sheet4.xml')

        # ===================================================================
        # WORKBOOK-LEVEL CHECKS
        # ===================================================================

        # fullCalcOnLoad must be present so Excel recalculates on open
        wb_raw = zf.read('xl/workbook.xml').decode('utf-8')
        check('fullCalcOnLoad' in wb_raw,
              "workbook.xml missing fullCalcOnLoad='1' — formulas won't recalculate on open")

        # calcChain.xml must NOT be present — it references the template's
        # formula layout and becomes stale after we modify cells, causing
        # Excel to show a repair warning on open
        check('xl/calcChain.xml' not in zf.namelist(),
              "calcChain.xml present — will trigger Excel repair warning on open")

        # Formula cells must NOT have cached <v> values (stale template data).
        # fullCalcOnLoad makes Excel recalculate, but other tools (PDF export,
        # preview, data_only readers) would show wrong numbers.
        stale_count = 0
        stale_examples = []
        for sheet_name in zf.namelist():
            if not (sheet_name.startswith('xl/worksheets/') and sheet_name.endswith('.xml')):
                continue
            sroot = ET.fromstring(zf.read(sheet_name))
            sd = sroot.find(f'{{{NS}}}sheetData')
            if sd is None:
                continue
            for row_el in sd.findall(f'{{{NS}}}row'):
                for cell_el in row_el.findall(f'{{{NS}}}c'):
                    f_el = cell_el.find(f'{{{NS}}}f')
                    v_el = cell_el.find(f'{{{NS}}}v')
                    if f_el is not None and v_el is not None:
                        stale_count += 1
                        if len(stale_examples) < 3:
                            stale_examples.append(f"{sheet_name}:{cell_el.get('r','?')}={v_el.text}")
        if stale_count > 0:
            examples = ', '.join(stale_examples)
            check(False, f"{stale_count} formula cells have stale cached values (e.g. {examples})")
        else:
            check(True, "No stale cached values in formula cells")

        # Shared strings XML well-formedness (already parsed above, but verify count)
        ss_raw = zf.read('xl/sharedStrings.xml')
        try:
            ss_root = ET.fromstring(ss_raw)
            claimed_count = int(ss_root.get('uniqueCount', '0'))
            actual_count = len(ss_root.findall(f'{{{NS}}}si'))
            check(claimed_count == actual_count,
                  f"sharedStrings uniqueCount mismatch: claims {claimed_count}, has {actual_count}")
        except ET.ParseError as e:
            check(False, f"sharedStrings.xml is malformed: {e}")

        # ===================================================================
        # SHEET 1: CELL TYPE CHECKS — numeric cells must not be type="s"
        # ===================================================================

        # Build the list of cells that must be numeric
        numeric_cells_sheet1 = []

        # Unit mix rows 7-9
        for row in (7, 8, 9):
            numeric_cells_sheet1.extend([
                (f'E{row}', 'unit SF'),
                (f'F{row}', 'unit count'),
                (f'I{row}', 'monthly rent'),
            ])

        # Parking and storage
        for row in (18, 19, 20, 21):
            numeric_cells_sheet1.extend([
                (f'F{row}', 'parking/storage count'),
                (f'G{row}', 'parking/storage fee'),
            ])

        # Other numeric cells
        numeric_cells_sheet1.extend([
            ('F24', 'vacancy rate'),
            ('G37', 'management fee %'),
            ('F38', 'tax rate'),
            ('G38', 'assessed value per unit'),
            ('H46', 'cap rate best'),
            ('H47', 'cap rate base'),
            ('H48', 'cap rate worst'),
            ('F62', 'building GFA'),
        ])

        for cell_ref, desc in numeric_cells_sheet1:
            cell_el, raw_val, ctype, has_formula = _get_cell(sheet1_root, cell_ref)
            if has_formula:
                # Formula cell — we shouldn't have written to it, skip type check
                continue
            if cell_el is not None and raw_val is not None:
                check(ctype != 's',
                      f"Sheet 1 {cell_ref} ({desc}): stored as shared string (type='s') "
                      f"— will cause #VALUE! in formulas. Value: '{_resolve_value(raw_val, ctype, shared_strings)}'")

        # ===================================================================
        # SHEET 1: FORMULA INTEGRITY — rows 7-9 formula columns
        # ===================================================================

        # Columns G, H, J, K, L in rows 7-9 should still have formulas
        formula_cols = ['G', 'H', 'J', 'K', 'L']
        for row in (7, 8, 9):
            for col in formula_cols:
                ref = f'{col}{row}'
                _, _, _, has_formula = _get_cell(sheet1_root, ref)
                check(has_formula,
                      f"Sheet 1 {ref}: expected formula but none found — may have been overwritten",
                      is_error=True)

        # Row 10 TOTAL row — key formulas must still exist
        total_formula_cells = ['F10', 'H10', 'K10', 'L10']
        for ref in total_formula_cells:
            _, _, _, has_formula = _get_cell(sheet1_root, ref)
            check(has_formula,
                  f"Sheet 1 {ref}: TOTAL row formula missing — model broken",
                  is_error=True)

        # Division-by-zero risk: if E{row}=0 and formulas reference it
        for row in (7, 8, 9):
            _, e_val, e_type, _ = _get_cell(sheet1_root, f'E{row}')
            e_numeric = _resolve_value(e_val, e_type, shared_strings)
            _, f_val, f_type, _ = _get_cell(sheet1_root, f'F{row}')
            f_numeric = _resolve_value(f_val, f_type, shared_strings)
            if isinstance(e_numeric, (int, float)) and e_numeric == 0:
                if isinstance(f_numeric, (int, float)) and f_numeric > 0:
                    # Units exist but SF is zero — J column ($/SF) will divide by zero
                    check(False,
                          f"Sheet 1 E{row}=0 but F{row}={f_numeric}: $/SF formula (J{row}) will divide by zero",
                          is_error=True)
                else:
                    # Both zero — no units in this row, formulas will produce 0/0
                    # but that's expected for empty groups
                    check(True, "")  # count as passed check

        # ===================================================================
        # SHEET 1: DATA ACCURACY — cross-check against parsed data
        # ===================================================================

        # Total units: F7+F8+F9 must equal parsed total
        unit_sum = 0
        for row in (7, 8, 9):
            _, val, ctype, _ = _get_cell(sheet1_root, f'F{row}')
            resolved = _resolve_value(val, ctype, shared_strings)
            if isinstance(resolved, (int, float)):
                unit_sum += resolved
        check(unit_sum == parsed_data['total_units'],
              f"Sheet 1 unit count mismatch: F7+F8+F9 = {unit_sum}, "
              f"parsed total = {parsed_data['total_units']}")

        # Vacancy rate
        _, vac_val, vac_type, _ = _get_cell(sheet1_root, 'F24')
        vac_resolved = _resolve_value(vac_val, vac_type, shared_strings)
        if isinstance(vac_resolved, (int, float)):
            check(abs(vac_resolved - parsed_data['vacancy_rate']) < 0.001,
                  f"Sheet 1 F24 vacancy rate: {vac_resolved} vs parsed {parsed_data['vacancy_rate']}")

        # Cap rates
        if len(parsed_data.get('cap_rates', [])) >= 3:
            for i, ref in enumerate(['H46', 'H47', 'H48']):
                _, cap_val, cap_type, _ = _get_cell(sheet1_root, ref)
                cap_resolved = _resolve_value(cap_val, cap_type, shared_strings)
                if isinstance(cap_resolved, (int, float)):
                    check(abs(cap_resolved - parsed_data['cap_rates'][i]) < 0.0001,
                          f"Sheet 1 {ref} cap rate: {cap_resolved} vs parsed {parsed_data['cap_rates'][i]}")

        # Zero-count unit groups: E and I should be numeric 0, not strings
        for row in (7, 8, 9):
            _, f_val, f_type, _ = _get_cell(sheet1_root, f'F{row}')
            f_resolved = _resolve_value(f_val, f_type, shared_strings)
            if isinstance(f_resolved, (int, float)) and f_resolved == 0:
                for col, desc in [('E', 'SF'), ('I', 'rent')]:
                    ref = f'{col}{row}'
                    _, val, ctype, has_f = _get_cell(sheet1_root, ref)
                    if has_f:
                        continue  # formula cell, skip
                    resolved = _resolve_value(val, ctype, shared_strings)
                    check(isinstance(resolved, (int, float)) and resolved == 0,
                          f"Sheet 1 {ref}: unit count is 0 but {desc} is {repr(resolved)} "
                          f"(type='{ctype}') — should be numeric 0",
                          is_error=True)

        # ===================================================================
        # TEMPLATE BLEED-THROUGH — stale Birchmount values
        # ===================================================================

        # Check cached values in formula cells for Birchmount fingerprints
        # Only flag if this ISN'T the Birchmount project itself
        is_birchmount = parsed_data['total_units'] == 170
        if not is_birchmount:
            # F10 cached value should match sum of F7:F9
            _, f10_val, f10_type, f10_has_f = _get_cell(sheet1_root, 'F10')
            f10_resolved = _resolve_value(f10_val, f10_type, shared_strings)
            if f10_has_f and isinstance(f10_resolved, (int, float)):
                check(f10_resolved != 170,
                      f"Sheet 1 F10: cached value is 170 (Birchmount) — "
                      f"fullCalcOnLoad should fix this on open, but flagging",
                      is_error=False)

            # Scan formula cells in rows 7-9 for Birchmount fingerprints
            for row in (7, 8, 9):
                for col in formula_cols:
                    ref = f'{col}{row}'
                    _, val, ctype, has_f = _get_cell(sheet1_root, ref)
                    if has_f and val is not None:
                        resolved = _resolve_value(val, ctype, shared_strings)
                        if isinstance(resolved, (int, float)) and resolved in BIRCHMOUNT_FINGERPRINTS:
                            check(False,
                                  f"Sheet 1 {ref}: cached formula value {resolved} "
                                  f"matches Birchmount template — stale cached value "
                                  f"(fullCalcOnLoad should fix on open)",
                                  is_error=False)

        # ===================================================================
        # SHEET 4: CROSS-CHECK with Sheet 1
        # ===================================================================

        # C7-C9 (unit counts) and D7-D9 (unit SF) must be numeric and match Sheet 1
        for row in (7, 8, 9):
            # Unit count: Sheet 4 C{row} vs Sheet 1 F{row}
            _, s4c_val, s4c_type, s4c_f = _get_cell(sheet4_root, f'C{row}')
            _, s1f_val, s1f_type, _ = _get_cell(sheet1_root, f'F{row}')

            if not s4c_f:  # only check if not a formula
                check(s4c_type != 's',
                      f"Sheet 4 C{row} (unit count): stored as string — must be numeric",
                      is_error=True)

                s4c_resolved = _resolve_value(s4c_val, s4c_type, shared_strings)
                s1f_resolved = _resolve_value(s1f_val, s1f_type, shared_strings)
                if isinstance(s4c_resolved, (int, float)) and isinstance(s1f_resolved, (int, float)):
                    check(s4c_resolved == s1f_resolved,
                          f"Sheet 4 C{row}={s4c_resolved} doesn't match Sheet 1 F{row}={s1f_resolved}")

            # Unit SF: Sheet 4 D{row} vs Sheet 1 E{row}
            _, s4d_val, s4d_type, s4d_f = _get_cell(sheet4_root, f'D{row}')
            _, s1e_val, s1e_type, _ = _get_cell(sheet1_root, f'E{row}')

            if not s4d_f:
                check(s4d_type != 's',
                      f"Sheet 4 D{row} (unit SF): stored as string — must be numeric",
                      is_error=True)

                s4d_resolved = _resolve_value(s4d_val, s4d_type, shared_strings)
                s1e_resolved = _resolve_value(s1e_val, s1e_type, shared_strings)
                if isinstance(s4d_resolved, (int, float)) and isinstance(s1e_resolved, (int, float)):
                    # Sheet 4 rounds SF to integer, Sheet 1 keeps decimals — allow rounding
                    check(abs(s4d_resolved - round(s1e_resolved)) <= 1,
                          f"Sheet 4 D{row}={s4d_resolved} doesn't match Sheet 1 E{row}={s1e_resolved} "
                          f"(rounded: {round(s1e_resolved)})")

    # ===================================================================
    # RESULT
    # ===================================================================
    return {
        'passed': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'checks_run': checks_run,
        'checks_passed': checks_passed,
    }


def validate_financials(project_json, verified=None):
    """
    Run financial plausibility checks on a project JSON.
    Non-blocking — returns warnings/errors for display, doesn't prevent download.

    Args:
        project_json: dict from the project JSON file
        verified: optional dict of auto-recalculated or reimported metrics

    Returns:
        {'warnings': [...], 'errors': [...]}
    """
    warnings = []
    errors = []

    def _fmt(v, fmt):
        """Format a value for human display."""
        if fmt == 'pct':
            return f"{v * 100:.1f}%"
        elif fmt == 'dollar':
            return f"${v:,.0f}"
        elif fmt == 'ratio':
            return f"{v:.2f}"
        else:
            return f"{v:,.2f}"

    def _check_range(val, lo, hi, label, warn_only=True, fmt=None):
        """Flag if val is outside (lo, hi). None/0 values are skipped."""
        if val is None:
            return
        try:
            v = float(val)
        except (ValueError, TypeError):
            return
        if v == 0:
            return  # zero is often intentional (no commercial, no parking, etc.)
        target = warnings if warn_only else errors
        if v < lo:
            target.append(f"{label}: {_fmt(v, fmt)} is below expected range ({_fmt(lo, fmt)}–{_fmt(hi, fmt)})")
        elif v > hi:
            target.append(f"{label}: {_fmt(v, fmt)} is above expected range ({_fmt(lo, fmt)}–{_fmt(hi, fmt)})")

    # --- Checks from project JSON (always run) ---

    cap = project_json.get('cap_rates', {})
    for tier in ('best', 'base', 'worst'):
        _check_range(cap.get(tier), 0.02, 0.10, f"Cap rate ({tier})", fmt='pct')

    opex = project_json.get('opex', {})
    _check_range(opex.get('tax_rate'), 0.005, 0.03, "Property tax rate", fmt='pct')
    if opex.get('tax_rate', 0) > 0:
        _check_range(opex.get('assessed_value_per_unit'), 150000, 1000000,
                     "Assessed value per unit", fmt='dollar')

    _check_range(opex.get('insurance_per_unit'), 200, 800, "Insurance per unit", fmt='dollar')
    _check_range(opex.get('staffing_per_unit'), 800, 2000, "Staffing per unit", fmt='dollar')
    _check_range(opex.get('rm_per_unit'), 500, 1500, "R&M per unit", fmt='dollar')
    _check_range(opex.get('mgmt_fee_pct'), 0.03, 0.05, "Management fee %", fmt='pct')

    # Revenue cross-check
    units = project_json.get('units', {})
    total_annual_rent = sum(
        u.get('count', 0) * u.get('rent', 0) * 12
        for u in units.get('types', [])
    )
    if total_annual_rent <= 0:
        errors.append("Total annual rent is zero or negative — check unit mix")

    # Zero-ancillary flags (Improvement #4)
    total_units = units.get('total', 0)
    parking = project_json.get('parking', {})
    underground_spaces = parking.get('underground', {}).get('spaces', 0)
    storage = project_json.get('storage', {})
    storage_count = storage.get('count', 0)
    submetering = project_json.get('submetering', {})
    sub_fee = submetering.get('fee', 0) if isinstance(submetering, dict) else 0

    if total_units > 50 and underground_spaces == 0:
        warnings.append(f"No underground parking for {total_units}-unit building — verify this is correct")
    if total_units > 50 and storage_count == 0:
        warnings.append(f"No storage lockers for {total_units}-unit building — verify this is correct")
    if total_units > 100 and sub_fee == 0:
        warnings.append(f"No submetering for {total_units}-unit building — verify this is correct")

    # --- Checks from verified metrics (when available after recalc) ---
    if verified:
        # NOI is stabilized (inflated 2% over dev years) and revenue includes
        # parking/storage/submetering/commercial, so ratio can exceed 0.75
        v_noi = verified.get('noi')
        if v_noi and total_annual_rent > 0:
            noi_ratio = v_noi / total_annual_rent
            _check_range(noi_ratio, 0.30, 0.90, "NOI/revenue ratio", fmt='pct')

        _check_range(verified.get('merchant_irr'), 0.05, 0.60, "Merchant IRR", fmt='pct')
        _check_range(verified.get('hold_irr'), 0.05, 0.30, "Hold IRR", fmt='pct')

        v_dev_cost = verified.get('total_dev_cost')
        if v_dev_cost and total_units > 0:
            cost_per_unit = v_dev_cost / total_units
            _check_range(cost_per_unit, 200000, 800000, "Dev cost per unit", fmt='dollar')

        _check_range(verified.get('dscr'), 1.0, 2.0, "DSCR", fmt='ratio')
        _check_range(verified.get('ltv'), 0.50, 0.98, "LTV", fmt='pct')

        # Dev cost breakdown consistency — line items must sum to TDC
        breakdown = verified.get('dev_breakdown')
        if breakdown and v_dev_cost:
            bd_sum = sum(breakdown.values())
            gap_pct = abs(bd_sum - v_dev_cost) / v_dev_cost if v_dev_cost else 0
            if gap_pct > 0.01:
                errors.append(
                    f"Dev cost breakdown sum (${bd_sum:,.0f}) differs from TDC "
                    f"(${v_dev_cost:,.0f}) by {gap_pct:.1%}"
                )
            # Individual items sanity
            for label, key, lo, hi in [
                ('Land', 'land', 0.05, 0.25),
                ('Construction', 'construction', 0.50, 0.85),
                ('Permits', 'permits', 0.02, 0.15),
                ('Marketing', 'marketing', 0.005, 0.05),
                ('Lease-up', 'lease_up', -0.10, 0),
            ]:
                val = breakdown.get(key, 0)
                ratio = val / v_dev_cost if v_dev_cost else 0
                if not (lo <= ratio <= hi):
                    warnings.append(
                        f"Dev breakdown {label}: ${val:,.0f} = {ratio:.1%} of TDC "
                        f"(expected {lo:.0%}–{hi:.0%})"
                    )

    return {'warnings': warnings, 'errors': errors}


def _print_result(xlsx_path, result):
    """Pretty-print validation results."""
    name = os.path.basename(xlsx_path)
    status = "PASS" if result['passed'] else "FAIL"
    print(f"\n{'=' * 60}")
    print(f"  {status}: {name}")
    print(f"  {result['checks_passed']}/{result['checks_run']} checks passed")
    print(f"{'=' * 60}")

    if result['errors']:
        print(f"\n  ERRORS ({len(result['errors'])}):")
        for e in result['errors']:
            print(f"    [X] {e}")

    if result['warnings']:
        print(f"\n  WARNINGS ({len(result['warnings'])}):")
        for w in result['warnings']:
            print(f"    [!] {w}")

    if result['passed'] and not result['warnings']:
        print("    All checks passed.")
    print()


# ---------------------------------------------------------------------------
# CLI: validate all .xlsx files in output/ by re-parsing their 1A sources
# ---------------------------------------------------------------------------

# Map output filenames to their 1A source files.
# The populator names outputs as "Reverse_1B_{address}_{date}.xlsx" — we
# match by keywords in the filename to the correct 1A proforma.
_1A_LOOKUP = [
    ('Birchmount', 'reference/1A_Birchmount_2240.xlsx'),
    ('Bayview', 'reference/1A_2470 Bayview Proforma - Feb 2025 v2.xls'),
    ('St_Clair', 'reference/1A_490_St_Clair.xls'),
    ('Old_Weston', 'reference/1A_290 Old Weston Rd Client Proforma - Feb 2025.xls'),
    ('Glenavy', 'reference/1A_Glenavy Ave Proforma - May 2024 v2.xls'),
]


def _find_1a_source(xlsx_filename, base_dir):
    """Match an output filename to its 1A source file."""
    name_upper = xlsx_filename.upper()
    for keyword, rel_path in _1A_LOOKUP:
        if keyword.upper() in name_upper:
            full = os.path.join(base_dir, rel_path)
            if os.path.exists(full):
                return full
    return None


if __name__ == '__main__':
    # Allow passing a specific file, or validate all in output/
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, 'output')

    # Import the parser from the populator
    sys.path.insert(0, base_dir)
    from populate_reverse_1b import parse_1a

    if len(sys.argv) > 1:
        # Validate specific file(s)
        targets = sys.argv[1:]
    else:
        # Find all .xlsx in output/
        if not os.path.isdir(output_dir):
            print(f"No output/ directory found at {output_dir}")
            sys.exit(1)
        targets = [
            os.path.join(output_dir, f)
            for f in sorted(os.listdir(output_dir))
            if f.endswith('.xlsx')
        ]

    if not targets:
        print("No .xlsx files found to validate.")
        sys.exit(0)

    total_pass = 0
    total_fail = 0

    for xlsx_path in targets:
        if not os.path.isabs(xlsx_path):
            xlsx_path = os.path.join(os.getcwd(), xlsx_path)

        source = _find_1a_source(os.path.basename(xlsx_path), base_dir)
        if source is None:
            print(f"\nSKIPPED: {os.path.basename(xlsx_path)} — no matching 1A source found")
            continue

        try:
            parsed = parse_1a(source)
        except Exception as e:
            print(f"\nSKIPPED: {os.path.basename(xlsx_path)} — failed to parse 1A: {e}")
            continue

        result = validate_output(xlsx_path, parsed)
        _print_result(xlsx_path, result)

        if result['passed']:
            total_pass += 1
        else:
            total_fail += 1

    print(f"\nSummary: {total_pass} passed, {total_fail} failed out of {total_pass + total_fail} validated")
    sys.exit(1 if total_fail > 0 else 0)
