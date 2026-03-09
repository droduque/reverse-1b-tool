"""
SVN Rock — Phase 1: Populate Reverse 1B from 1A Proforma
=========================================================
Reads a 1A proforma Excel file, copies the Reverse 1B template,
and writes the 1A data into the correct cells across 3 sheets.

Usage:
    python populate_reverse_1b.py reference/1A_Birchmount_2240.xlsx
    python populate_reverse_1b.py reference/1A_490_St_Clair.xls

The tool will prompt for municipality selection (for DC rates)
and building type (mid-rise vs high-rise).
"""

import sys
import os
import shutil
import math
import re
from datetime import date
import openpyxl

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "reference", "REVERSE_1B_Template.xlsx")
DC_RATES_PATH = os.path.join(os.path.dirname(__file__), "reference", "Municipalities & DC's & Prop Taxes for Proforma Testing.xlsx")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

# GFA efficiency ratio — derived from Birchmount template (128,853 / 146,346)
GFA_EFFICIENCY = 0.88

# Amenity SF per unit — derived from Birchmount (3,703 / 170 = 21.8)
AMENITY_SF_PER_UNIT = 22

# Parking SF per space — industry standard for underground
PARKING_SF_PER_SPACE = 350

# High-rise threshold — 7+ storeys per Noor (2026-03-09)
HIGH_RISE_FLOOR_THRESHOLD = 7

# Unit type grouping patterns — match labels to 3 template rows
# Order matters: checked top-to-bottom, first match wins
UNIT_GROUP_PATTERNS = [
    ("1 Bed", ["studio", "bachelor", "1 bed", "1bed", "one bed"]),
    ("2 Bed", ["2 bed", "2bed", "two bed"]),
    ("3 Bed", ["3 bed", "3bed", "three bed", "4 bed", "4bed"]),
]

# ---------------------------------------------------------------------------
# DC RATE LOOKUP — loads municipality rates from Kanen's spreadsheet
# ---------------------------------------------------------------------------

def load_dc_rates():
    """
    Parse Kanen's DC spreadsheet into a list of municipality entries.
    Each entry: {name, rates: {1bed, 2bed, 3bed}, notes}

    The spreadsheet has varying column usage per city. We consolidate
    into 3 categories to match the current 3-row template:
      - 1bed: best available from cols C (bachelor), D (1bed), E (1bed), F (1bed+den)
      - 2bed: best available from cols G (2bed), H (2bed+)
      - 3bed: best available from cols I (3bed), J (3bed+), K (4bed+)
    """
    if not os.path.exists(DC_RATES_PATH):
        print(f"Warning: DC rates file not found at {DC_RATES_PATH}")
        return []

    wb = openpyxl.load_workbook(DC_RATES_PATH, data_only=True)
    ws = wb['2026 DC\'s']

    municipalities = []
    for row in ws.iter_rows(min_row=4, max_row=ws.max_row, max_col=12, values_only=False):
        city_cell = row[1]  # Column B
        if not city_cell.value:
            continue

        city_name = str(city_cell.value).strip()

        # Read all rate columns — some cities only populate certain ones
        def num(cell):
            v = cell.value
            if v is None:
                return None
            if isinstance(v, str):
                # Handle text-formatted numbers like "$39,088.07"
                cleaned = v.replace('$', '').replace(',', '').strip()
                try:
                    return float(cleaned)
                except ValueError:
                    return None
            return float(v)

        col_c = num(row[2])   # Bachelor/Studio
        col_d = num(row[3])   # 1 Bed & Bachelor
        col_e = num(row[4])   # 1 Bed
        col_f = num(row[5])   # 1 Bed + Den
        col_g = num(row[6])   # 2 Bed
        col_h = num(row[7])   # 2 Bed +
        col_i = num(row[8])   # 3 Bed
        col_j = num(row[9])   # 3 Bed +
        col_k = num(row[10])  # 4 Bed +
        notes = str(row[11].value or '').strip()

        # Consolidate into 3 categories using fallback chains
        # 1-bed: prefer D (most common), fall back to E, C, F
        rate_1bed = col_d or col_e or col_c or col_f
        # 2-bed: prefer G, fall back to H
        rate_2bed = col_g or col_h
        # 3-bed: prefer J, fall back to I, then K, then 2-bed rate
        rate_3bed = col_j or col_i or col_k or rate_2bed

        # If 2-bed is missing but 3-bed exists, use 3-bed as fallback
        if rate_2bed is None and rate_3bed is not None:
            rate_2bed = rate_3bed
        # If still missing, use 1-bed as last resort
        if rate_2bed is None:
            rate_2bed = rate_1bed
        if rate_3bed is None:
            rate_3bed = rate_2bed

        if rate_1bed is None:
            continue  # Skip rows with no usable data

        municipalities.append({
            'name': city_name,
            'rates': {
                '1bed': round(rate_1bed),
                '2bed': round(rate_2bed),
                '3bed': round(rate_3bed),
            },
            # Keep the granular rates for when Noor expands to 7+ rows
            'rates_detailed': {
                'bachelor': col_c,
                '1bed_bachelor': col_d,
                '1bed': col_e,
                '1bed_den': col_f,
                '2bed': col_g,
                '2bed_plus': col_h,
                '3bed': col_i,
                '3bed_plus': col_j,
                '4bed_plus': col_k,
            },
            'notes': notes,
            'tax_rate': None,  # filled below from Prop Tax sheet
        })

    # --- Load property tax rates from "Prop Tax Rates" sheet ---
    # Match by city name to the municipalities we already loaded.
    # Use "New Multi-Residential" (NT) rate — that's what new builds pay.
    # Prefer 2026 rate (col D), fall back to 2025 (col C).
    if 'Prop Tax Rates' in wb.sheetnames:
        ws_tax = wb['Prop Tax Rates']
        # Build a lookup: normalized city name -> tax rate
        tax_lookup = {}
        for row in ws_tax.iter_rows(min_row=4, max_row=ws_tax.max_row, max_col=7, values_only=False):
            city_cell = row[1]  # Column B
            if not city_cell.value:
                continue
            city_name_tax = str(city_cell.value).strip()
            # Col D = NT 2026, Col C = NT 2025, Col F = MT 2026, Col E = MT 2025
            # Prefer New Multi-Res (NT) — what new builds pay.
            # Fall back to Multi-Res (MT) if NT not available.
            nt_2026 = row[3].value if row[3].value and isinstance(row[3].value, (int, float)) else None
            nt_2025 = row[2].value if row[2].value and isinstance(row[2].value, (int, float)) else None
            mt_2026 = row[5].value if row[5].value and isinstance(row[5].value, (int, float)) else None
            mt_2025 = row[4].value if row[4].value and isinstance(row[4].value, (int, float)) else None
            rate = nt_2026 or nt_2025 or mt_2026 or mt_2025
            if rate:
                # Normalize: "Toronto, ON" -> "TORONTO"
                key = city_name_tax.split(',')[0].strip().upper()
                tax_lookup[key] = rate

        # Attach tax rates to municipalities by matching city names
        for m in municipalities:
            muni_key = m['name'].split(',')[0].split('(')[0].strip().upper()
            if muni_key in tax_lookup:
                m['tax_rate'] = tax_lookup[muni_key]
            else:
                # Try partial matches (e.g., "Hamilton" matches "Hamilton, ON")
                for tax_key, rate in tax_lookup.items():
                    if tax_key in muni_key or muni_key in tax_key:
                        m['tax_rate'] = rate
                        break

    return municipalities


def select_municipality(municipalities):
    """
    Display a numbered list of municipalities and let the user pick one.
    Returns the selected municipality dict, or None if skipped.
    """
    if not municipalities:
        print("\nNo DC rates available. Using defaults.")
        return None

    print(f"\n{'='*60}")
    print("SELECT MUNICIPALITY (for development charges)")
    print(f"{'='*60}")
    for i, m in enumerate(municipalities, 1):
        notes = f"  — {m['notes']}" if m['notes'] else ""
        print(f"  {i:>2}. {m['name']}{notes}")
    print(f"  {len(municipalities)+1:>2}. Skip (use no DC rates)")

    while True:
        try:
            choice = input(f"\nEnter number (1-{len(municipalities)+1}): ").strip()
            idx = int(choice)
            if idx == len(municipalities) + 1:
                return None
            if 1 <= idx <= len(municipalities):
                selected = municipalities[idx - 1]
                print(f"\n  Selected: {selected['name']}")
                print(f"  DC rates: 1-Bed ${selected['rates']['1bed']:,} | "
                      f"2-Bed ${selected['rates']['2bed']:,} | "
                      f"3-Bed ${selected['rates']['3bed']:,}")
                return selected
        except (ValueError, IndexError):
            pass
        print(f"  Please enter a number between 1 and {len(municipalities)+1}")


def select_building_type(total_units):
    """
    Ask user for building type (mid-rise vs high-rise).
    Estimates floor count to suggest the likely answer.
    """
    est_floors = math.ceil(total_units / 12)

    print(f"\n{'='*60}")
    print("SELECT BUILDING TYPE")
    print(f"{'='*60}")
    print(f"  Estimated floors: ~{est_floors} (based on {total_units} units)")
    if est_floors >= HIGH_RISE_FLOOR_THRESHOLD:
        print(f"  Likely HIGH-RISE (7+ storeys)")
    else:
        print(f"  Likely MID-RISE (under 7 storeys)")

    print(f"\n  1. Mid-Rise (up to 6 storeys)")
    print(f"  2. High-Rise (7+ storeys)")

    while True:
        try:
            choice = input(f"\nEnter number (1-2): ").strip()
            idx = int(choice)
            if idx == 1:
                print("  Selected: Mid-Rise")
                return 'mid-rise'
            elif idx == 2:
                print("  Selected: High-Rise")
                return 'high-rise'
        except (ValueError, IndexError):
            pass
        print("  Please enter 1 or 2")


# Default operating expense values (used only if not found in 1A)
DEFAULT_RM_PER_UNIT = 1050
DEFAULT_STAFFING_PER_UNIT = 1200
DEFAULT_INSURANCE_PER_UNIT = 450
DEFAULT_MARKETING_PER_UNIT = 300
DEFAULT_GA_PER_UNIT = 250
DEFAULT_UTILITIES_PSF = 11
DEFAULT_RESERVE_PCT = 0.02


# ---------------------------------------------------------------------------
# 1A PARSER — reads any 1A proforma dynamically
# ---------------------------------------------------------------------------

def parse_1a(filepath):
    """
    Parse a 1A proforma file (.xlsx or .xls) and return a dict of all
    extracted data. Finds sections by scanning for landmark strings,
    not hardcoded row numbers.
    """
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".xls":
        return _parse_1a_xls(filepath)
    else:
        return _parse_1a_xlsx(filepath)


def _parse_1a_xlsx(filepath):
    """Parse .xlsx format using openpyxl."""
    wb = openpyxl.load_workbook(filepath, data_only=True)
    ws = wb.active  # Use the first/active sheet

    # Build a simple cell reader
    def cell(row, col_letter):
        return ws[f"{col_letter}{row}"].value

    return _parse_sheet(cell, ws.max_row)


def _parse_1a_xls(filepath):
    """Parse .xls format using xlrd."""
    import xlrd
    wb = xlrd.open_workbook(filepath)
    ws = wb.sheet_by_index(0)

    # xlrd uses 0-based indexing; our parser uses 1-based rows and letter columns
    def col_to_idx(letter):
        idx = 0
        for ch in letter:
            idx = idx * 26 + (ord(ch) - ord('A') + 1)
        return idx - 1  # 0-based

    def cell(row, col_letter):
        r = row - 1  # xlrd is 0-based
        c = col_to_idx(col_letter)
        if r < 0 or r >= ws.nrows or c >= ws.ncols:
            return None
        val = ws.cell_value(r, c)
        if val == '':
            return None
        return val

    return _parse_sheet(cell, ws.nrows)


def _parse_sheet(cell, max_row):
    """
    Core parser logic — works with any cell accessor function.
    Scans for landmark strings to find each section dynamically.
    """
    data = {}

    # --- TITLE & ADDRESS ---
    # Title is in E2 or F2 — try both
    title = cell(2, 'E') or cell(2, 'F') or ""
    data['title'] = title

    # Extract address from title: "Estimated Stabilized Value - ADDRESS"
    address = ""
    if " - " in str(title):
        address = str(title).split(" - ", 1)[1].strip()
    data['address'] = address

    # --- Find TOTAL/AVG row to locate unit mix ---
    total_row = None
    for r in range(1, min(max_row + 1, 50)):
        val = cell(r, 'D')
        if val and "TOTAL" in str(val).upper() and "AVG" in str(val).upper():
            total_row = r
            break

    if total_row is None:
        raise ValueError("Could not find TOTAL/AVG row in 1A proforma")

    # --- UNIT MIX ---
    # Unit types are the rows between the column headers and the TOTAL row.
    # Headers are 2 rows before the first unit type (typically row 5 for headers,
    # row 6 for first unit). Scan backwards from total_row to find unit rows.
    unit_types = []
    for r in range(total_row - 1, 0, -1):
        label = cell(r, 'D')
        count = cell(r, 'F')
        # A unit row has a label in D and a numeric count in F
        if label and count and isinstance(count, (int, float)) and count > 0:
            sf = cell(r, 'E')
            rent = cell(r, 'I')
            unit_types.insert(0, {
                'label': str(label).strip(),
                'sf': float(sf) if sf else 0,
                'count': int(count),
                'rent': float(rent) if rent else 0,
            })
        else:
            # Hit a non-unit row (header or blank) — stop scanning
            break

    data['unit_types'] = unit_types
    data['total_units'] = sum(u['count'] for u in unit_types)
    data['total_rentable_sf'] = sum(u['sf'] * u['count'] for u in unit_types)

    # --- Find OPERATING REVENUES section ---
    rev_start = None
    for r in range(total_row, min(max_row + 1, 80)):
        val = cell(r, 'E')
        if val and "ESTIMATED OPERATING REVENUES" in str(val).upper():
            rev_start = r
            break

    # Scan revenue section for specific items by label
    data['parking_underground'] = {'spaces': 0, 'fee': 0}
    data['parking_visitor'] = {'spaces': 0, 'fee': 0}
    data['parking_retail'] = {'spaces': 0, 'fee': 0}
    data['storage'] = {'count': 0, 'fee': 0}
    data['submetering'] = {'count': 0, 'fee': 0}
    data['vacancy_rate'] = 0.03  # default
    data['commercial'] = {'sf': 0, 'rate': 0}
    data['commercial_vacancy'] = 0

    if rev_start:
        for r in range(rev_start + 1, rev_start + 20):
            label = str(cell(r, 'E') or '').upper().strip()
            f_val = cell(r, 'F')
            g_val = cell(r, 'G')

            # Skip rows that are totals, subtotals, headers, or vacancies
            # before checking parking — "Vacancies (Rent & Parking)" contains
            # "PARKING" and would falsely match the underground condition
            if 'TOTAL' in label or 'SUB-TOTAL' in label:
                continue

            if 'VACANC' in label:
                # Vacancy rows — check if residential or commercial
                if 'COMMERCIAL' in label:
                    if f_val and isinstance(f_val, (int, float)):
                        data['commercial_vacancy'] = float(f_val)
                else:
                    if f_val and isinstance(f_val, (int, float)):
                        data['vacancy_rate'] = float(f_val)
            elif 'UNDERGROUND' in label or ('PARKING' in label and 'VISITOR' not in label
                    and 'RETAIL' not in label and 'SURFACE' not in label):
                data['parking_underground'] = {
                    'spaces': int(f_val) if f_val else 0,
                    'fee': float(g_val) if g_val else 0,
                }
            elif 'VISITOR' in label:
                data['parking_visitor'] = {
                    'spaces': int(f_val) if f_val else 0,
                    'fee': float(g_val) if g_val else 0,
                }
            elif 'RETAIL' in label and 'COMMERCIAL' not in label:
                data['parking_retail'] = {
                    'spaces': int(f_val) if f_val else 0,
                    'fee': float(g_val) if g_val else 0,
                }
            elif 'STORAGE' in label or 'LOCKER' in label:
                data['storage'] = {
                    'count': int(f_val) if f_val else 0,
                    'fee': float(g_val) if g_val else 0,
                }
            elif 'SUBMETER' in label:
                data['submetering'] = {
                    'count': int(f_val) if f_val else data['total_units'],
                    'fee': float(g_val) if g_val else 20,
                }
            elif 'COMMERCIAL' in label or 'NET COMMERCIAL' in label:
                data['commercial'] = {
                    'sf': int(f_val) if f_val else 0,
                    'rate': float(g_val) if g_val else 0,
                }

    # --- Find OPERATING EXPENSES section ---
    exp_start = None
    for r in range(rev_start or total_row, min(max_row + 1, 100)):
        val = cell(r, 'E')
        if val and "ESTIMATED OPERATING EXPENSES" in str(val).upper():
            exp_start = r
            break

    data['expenses'] = {}
    data['mgmt_fee_pct'] = 0.0425  # default
    data['tax_rate'] = 0
    data['assessed_value'] = 0
    data['reserve_pct'] = DEFAULT_RESERVE_PCT

    if exp_start:
        for r in range(exp_start + 1, exp_start + 15):
            label = str(cell(r, 'E') or '').upper().strip()
            h_val = cell(r, 'H')  # annual per unit
            f_val = cell(r, 'F')
            g_val = cell(r, 'G')

            if 'UTILIT' in label:
                data['expenses']['utilities'] = float(h_val) if h_val else None
            elif 'REPAIR' in label or 'MAINTENANCE' in label:
                data['expenses']['rm'] = float(h_val) if h_val else None
            elif 'STAFF' in label:
                data['expenses']['staffing'] = float(h_val) if h_val else None
            elif 'INSURANCE' in label:
                data['expenses']['insurance'] = float(h_val) if h_val else None
            elif 'MARKETING' in label:
                data['expenses']['marketing'] = float(h_val) if h_val else None
            elif 'GENERAL' in label or 'ADMIN' in label or 'MISCELLANEOUS' in label:
                data['expenses']['ga'] = float(h_val) if h_val else None
            elif 'MANAGEMENT' in label and 'FEE' in label:
                if g_val and isinstance(g_val, (int, float)):
                    data['mgmt_fee_pct'] = float(g_val)
            elif 'PROPERTY TAX' in label or 'MUNICIPAL' in label:
                if f_val and isinstance(f_val, (int, float)):
                    data['tax_rate'] = float(f_val)
                if g_val and isinstance(g_val, (int, float)):
                    data['assessed_value'] = float(g_val)
            elif 'RESERVE' in label:
                if g_val and isinstance(g_val, (int, float)):
                    data['reserve_pct'] = float(g_val)

    # --- Find VALUATION section ---
    data['cap_rates'] = []
    for r in range(exp_start or total_row, min(max_row + 1, 120)):
        val = cell(r, 'G')
        if val and "ESTIMATED VALUATION" in str(val).upper():
            # Next 3 rows have cap rates in column H
            for cr_row in range(r + 1, r + 4):
                cap = cell(cr_row, 'H')
                if cap and isinstance(cap, (int, float)):
                    data['cap_rates'].append(float(cap))
            break

    # --- GFA (from internal section if available) ---
    # Scan for "Building GFA" label in E column, rows 55+
    data['gfa'] = None
    for r in range(50, min(max_row + 1, 80)):
        val = cell(r, 'E')
        if val and 'BUILDING GFA' in str(val).upper():
            gfa_val = cell(r, 'F')
            if gfa_val and isinstance(gfa_val, (int, float)):
                data['gfa'] = float(gfa_val)
            break

    # --- Amenity space (from internal section if available) ---
    data['amenity_sf'] = None
    for r in range(50, min(max_row + 1, 80)):
        val = cell(r, 'E')
        if val and 'AMENITY' in str(val).upper() and 'SPACE' in str(val).upper():
            am_val = cell(r, 'F')
            if am_val and isinstance(am_val, (int, float)):
                data['amenity_sf'] = float(am_val)
            break

    return data


# ---------------------------------------------------------------------------
# UNIT MIX CONSOLIDATION — groups N unit types into 3 rows
# ---------------------------------------------------------------------------

def consolidate_unit_mix(unit_types):
    """
    Groups any number of unit types into 3 categories (1-Bed, 2-Bed, 3-Bed)
    using weighted averages for SF and rent.

    Returns a list of 3 dicts: [{'label', 'sf', 'count', 'rent'}, ...]
    """
    groups = {name: [] for name, _ in UNIT_GROUP_PATTERNS}

    for unit in unit_types:
        label_lower = unit['label'].lower()
        matched = False
        for group_name, patterns in UNIT_GROUP_PATTERNS:
            if any(p in label_lower for p in patterns):
                groups[group_name].append(unit)
                matched = True
                break
        if not matched:
            # Unrecognized type — put it in 1-Bed as a catch-all
            groups["1 Bed"].append(unit)

    result = []
    for group_name, _ in UNIT_GROUP_PATTERNS:
        units_in_group = groups[group_name]
        total_count = sum(u['count'] for u in units_in_group)
        if total_count > 0:
            # Weighted average SF and rent
            weighted_sf = sum(u['sf'] * u['count'] for u in units_in_group) / total_count
            weighted_rent = sum(u['rent'] * u['count'] for u in units_in_group) / total_count
            result.append({
                'label': group_name,
                'sf': round(weighted_sf, 2),
                'count': total_count,
                'rent': round(weighted_rent, 2),
            })
        else:
            result.append({'label': group_name, 'sf': 0, 'count': 0, 'rent': 0})

    return result


# ---------------------------------------------------------------------------
# TEMPLATE WRITER — copies template and writes data to 3 sheets
# ---------------------------------------------------------------------------

def populate_template(data, output_path, municipality=None, building_type='high-rise'):
    """
    Copy the Reverse 1B template and write parsed 1A data into it.
    Uses the ZIP/XML writer to preserve all drawings, images, and formatting.
    Returns a list of log entries documenting every change.

    municipality: dict from load_dc_rates() with 'name' and 'rates' keys, or None
    building_type: 'mid-rise' or 'high-rise' — affects Altus cost guide row reference
    """
    from xml_writer import write_cell, save_workbook

    log = []

    # Consolidate unit mix if needed
    if len(data['unit_types']) <= 3:
        consolidated = data['unit_types']
        # Pad to 3 rows if fewer than 3 types
        while len(consolidated) < 3:
            consolidated.append({'label': f"{len(consolidated)+1} Bed", 'sf': 0, 'count': 0, 'rent': 0})
    else:
        consolidated = consolidate_unit_mix(data['unit_types'])
        log.append(f"CONSOLIDATION: {len(data['unit_types'])} unit types consolidated into 3 groups:")
        for orig in data['unit_types']:
            log.append(f"  {orig['label']}: {orig['count']} units, {orig['sf']} SF, ${orig['rent']}/mo")
        log.append("  Grouped as:")
        for grp in consolidated:
            log.append(f"  → {grp['label']}: {grp['count']} units, {grp['sf']} SF, ${grp['rent']}/mo")
        log.append("")

    # Collect all cell writes per sheet: {cell_ref: (value, description)}
    sheet1_writes = {}
    sheet4_writes = {}
    sheet5_writes = {}

    def queue_write(target, cell_ref, value, description=""):
        """Queue a cell write for later application via XML writer."""
        target[cell_ref] = (value, description)

    # ===================================================================
    # SHEET 1: 1A Proforma
    # ===================================================================
    log.append("=" * 60)
    log.append("SHEET 1: 1. 1A Proforma")
    log.append("=" * 60)

    # Title and address
    queue_write(sheet1_writes, 'F2', "Estimated Stabilized Value - Today", "Title")
    queue_write(sheet1_writes, 'F3', data['address'], "Address from 1A title")

    # Unit mix — rows 7, 8, 9
    for i, unit in enumerate(consolidated):
        row = 7 + i
        queue_write(sheet1_writes, f'D{row}', unit['label'], f"Unit type {i+1} label")
        queue_write(sheet1_writes, f'E{row}', unit['sf'], f"Unit type {i+1} avg SF")
        queue_write(sheet1_writes, f'F{row}', unit['count'], f"Unit type {i+1} count")
        queue_write(sheet1_writes, f'I{row}', unit['rent'], f"Unit type {i+1} monthly rent")

    # Operating revenues
    queue_write(sheet1_writes, 'F18', data['parking_underground']['spaces'], "Underground parking spaces")
    queue_write(sheet1_writes, 'G18', data['parking_underground']['fee'], "Underground parking monthly fee")
    queue_write(sheet1_writes, 'F19', data['parking_visitor']['spaces'], "Visitor parking spaces")
    queue_write(sheet1_writes, 'G19', data['parking_visitor']['fee'], "Visitor parking monthly fee")
    queue_write(sheet1_writes, 'F20', data['parking_retail']['spaces'], "Retail parking spaces")
    queue_write(sheet1_writes, 'G20', data['parking_retail']['fee'], "Retail parking monthly fee")
    queue_write(sheet1_writes, 'F21', data['storage']['count'], "Storage locker count")
    queue_write(sheet1_writes, 'G21', data['storage']['fee'], "Storage locker monthly fee")

    # Submetering — G22 is an external workbook ref, safe to overwrite
    queue_write(sheet1_writes, 'G22', data['submetering']['fee'], "Submetering monthly fee — was external ref")

    queue_write(sheet1_writes, 'F24', data['vacancy_rate'], "Residential vacancy rate")
    queue_write(sheet1_writes, 'F26', data['commercial']['sf'], "Commercial retail SF")
    queue_write(sheet1_writes, 'G26', data['commercial']['rate'], "Commercial retail $/SF rate")
    queue_write(sheet1_writes, 'F27', data['commercial_vacancy'], "Commercial vacancy rate")

    # Operating expenses
    queue_write(sheet1_writes, 'G37', data['mgmt_fee_pct'], "Management fee %")
    queue_write(sheet1_writes, 'F38', data['tax_rate'], "Property tax rate")
    queue_write(sheet1_writes, 'G38', data['assessed_value'], "Assessed value per unit")

    # Cap rates
    if len(data['cap_rates']) >= 3:
        queue_write(sheet1_writes, 'H46', data['cap_rates'][0], "Best case cap rate")
        queue_write(sheet1_writes, 'H47', data['cap_rates'][1], "Base case cap rate")
        queue_write(sheet1_writes, 'H48', data['cap_rates'][2], "Worst case cap rate")

    # --- Internal operating assumptions (rows 58+) ---
    log.append("")
    log.append("--- Sheet 1 Internal Section (Operating Assumptions) ---")

    # GFA — from 1A if available, else estimate from net rentable / efficiency
    gfa = data.get('gfa')
    if gfa:
        queue_write(sheet1_writes, 'F62', gfa, "Building GFA (from 1A internal section)")
    else:
        gfa = round(data['total_rentable_sf'] / GFA_EFFICIENCY)
        queue_write(sheet1_writes, 'F62', gfa,
                    f"ESTIMATED: net rentable {data['total_rentable_sf']:.0f} / {GFA_EFFICIENCY} efficiency")

    # Amenity space — from 1A if available, else estimate
    amenity_sf = data.get('amenity_sf')
    if amenity_sf:
        queue_write(sheet1_writes, 'F64', amenity_sf, "Amenity space (from 1A)")
    else:
        amenity_sf = round(data['total_units'] * AMENITY_SF_PER_UNIT, -2)  # round to 100
        queue_write(sheet1_writes, 'F64', amenity_sf,
                    f"ESTIMATED: {data['total_units']} units x {AMENITY_SF_PER_UNIT} SF/unit, rounded to 100")

    # Per-unit operating costs — use 1A values if available, else defaults
    rm = data['expenses'].get('rm') or DEFAULT_RM_PER_UNIT
    queue_write(sheet1_writes, 'I93', rm,
                f"R&M per unit ({'from 1A' if data['expenses'].get('rm') else 'DEFAULT'})")

    staffing = data['expenses'].get('staffing') or DEFAULT_STAFFING_PER_UNIT
    queue_write(sheet1_writes, 'I109', staffing,
                f"Staffing per unit ({'from 1A' if data['expenses'].get('staffing') else 'DEFAULT'})")

    insurance = data['expenses'].get('insurance') or DEFAULT_INSURANCE_PER_UNIT
    queue_write(sheet1_writes, 'F117', insurance,
                f"Insurance per unit ({'from 1A' if data['expenses'].get('insurance') else 'DEFAULT'})")

    marketing = data['expenses'].get('marketing') or DEFAULT_MARKETING_PER_UNIT
    queue_write(sheet1_writes, 'F122', marketing,
                f"Marketing per unit ({'from 1A' if data['expenses'].get('marketing') else 'DEFAULT'})")

    ga = data['expenses'].get('ga') or DEFAULT_GA_PER_UNIT
    queue_write(sheet1_writes, 'F127', ga,
                f"G&A per unit ({'from 1A' if data['expenses'].get('ga') else 'DEFAULT'})")

    queue_write(sheet1_writes, 'I137', data['reserve_pct'], "Reserve for replacement %")

    # Utilities — back-calculate PSF from per-unit value
    # Formula chain: F80 ($/PSF) -> F81 (=F80*common_area) -> H80 (=ROUND(F81/units,-1))
    # Common area = GFA - net_rentable (approx)
    utilities_per_unit = data['expenses'].get('utilities')
    if utilities_per_unit:
        common_area = gfa - data['total_rentable_sf']
        if common_area > 0:
            utilities_psf = round(utilities_per_unit * data['total_units'] / common_area)
        else:
            utilities_psf = DEFAULT_UTILITIES_PSF
        queue_write(sheet1_writes, 'F80', utilities_psf,
                    f"BACK-CALCULATED: ${utilities_per_unit}/unit x {data['total_units']} units "
                    f"/ {common_area:.0f} SF common area = ${utilities_psf}/PSF")
    else:
        queue_write(sheet1_writes, 'F80', DEFAULT_UTILITIES_PSF, "Utilities $/PSF (DEFAULT)")

    # ===================================================================
    # SHEET 4: Area Schedule
    # ===================================================================
    log.append("")
    log.append("=" * 60)
    log.append("SHEET 4: 4. Area Schedule")
    log.append("=" * 60)

    # Address
    queue_write(sheet4_writes, 'A2', data['address'], "Project address")

    # --- Section 1: Residential Units ---
    log.append("")
    log.append("--- Residential Units (from 1A) ---")
    for i, unit in enumerate(consolidated):
        row = 7 + i
        queue_write(sheet4_writes, f'C{row}', unit['count'], f"{unit['label']} count")
        # Round SF to integer for the area schedule (template uses integers)
        queue_write(sheet4_writes, f'D{row}', round(unit['sf']), f"{unit['label']} avg SF")
        pct = round(unit['count'] / data['total_units'] * 100) if data['total_units'] > 0 else 0
        queue_write(sheet4_writes, f'F{row}', f"{pct}% of total units", f"{unit['label']} note")

    # --- Section 2.1: Amenity Spaces ---
    log.append("")
    log.append("--- Amenity Spaces (ESTIMATED) ---")
    # Total amenity budget then distribute across 5 rooms
    total_amenity = amenity_sf
    # Keep the same proportions as Birchmount: 32%, 27%, 16%, 14%, 11%
    amenity_rooms = [
        ('Fitness Centre', 0.32),
        ('Multi-Purpose/Party Room', 0.27),
        ('Co-Working Space', 0.16),
        ('Games/Lounge Area', 0.14),
        ('Outdoor Terrace/BBQ Area', 0.11),
    ]
    for idx, (name, pct) in enumerate(amenity_rooms):
        row = 14 + idx
        room_sf = round(total_amenity * pct, -1)  # round to 10
        queue_write(sheet4_writes, f'C{row}', 1, f"{name} quantity")
        queue_write(sheet4_writes, f'D{row}', int(room_sf),
                    f"ESTIMATED: {pct:.0%} of {total_amenity} total amenity SF")
        queue_write(sheet4_writes, f'E{row}', int(room_sf), f"{name} total SF")

    # --- Section 2.2: Common Areas ---
    log.append("")
    log.append("--- Common Areas (ESTIMATED) ---")
    est_floors = math.ceil(data['total_units'] / 12)
    elevator_count = 2 if data['total_units'] < 100 else (3 if data['total_units'] <= 250 else 4)

    common_items = [
        # (row, label, qty, sf_each, total_override, note_for_log)
        (22, 'Main Lobby', 1, 800, 800,
         "DEFAULT: 800 SF"),
        (23, 'Corridors & Hallways', data['total_units'], 25, None,
         f"ESTIMATED: {data['total_units']} units x 25 SF/unit"),
        (24, 'Elevator Lobbies', est_floors, 60, None,
         f"ESTIMATED: {est_floors} floors (ceil({data['total_units']}/12)) x 60 SF"),
        (25, 'Stairwells (2)', 2, 600, None,
         "DEFAULT: 2 stairwells x 600 SF"),
        (26, f'Elevators ({elevator_count})', elevator_count, 60, None,
         f"ESTIMATED: {elevator_count} elevators x 60 SF"),
        (27, 'Mail/Parcel Room', 1, 300, 300,
         "DEFAULT: 300 SF"),
        (28, 'Garbage/Recycling Rooms', max(1, est_floors // 4), 200, None,
         f"ESTIMATED: {max(1, est_floors // 4)} rooms (floors/4) x 200 SF"),
        (29, 'Electrical/Mechanical Rooms', 2, 200, None,
         "DEFAULT: 2 rooms x 200 SF"),
        (30, 'Storage Lockers', data['storage']['count'] or round(data['total_units'] * 0.5), 25, None,
         f"{'From 1A' if data['storage']['count'] else 'ESTIMATED: 50% of units'}: "
         f"{data['storage']['count'] or round(data['total_units'] * 0.5)} lockers x 25 SF"),
        (31, 'Janitor/Housekeeping Closets', max(1, est_floors // 5), 40, None,
         f"ESTIMATED: {max(1, est_floors // 5)} closets (floors/5) x 40 SF"),
    ]

    for row, label, qty, sf_each, total_override, note in common_items:
        queue_write(sheet4_writes, f'C{row}', qty, note)
        queue_write(sheet4_writes, f'D{row}', sf_each, f"{label} SF each")
        # E column: write total SF — xml_writer's write_cell will skip if it's a formula
        total_sf = total_override if total_override else qty * sf_each
        queue_write(sheet4_writes, f'E{row}', total_sf, f"{label} total SF")

    # --- Section 3: Commercial ---
    log.append("")
    log.append("--- Commercial (from 1A) ---")
    commercial_sf = data['commercial']['sf']
    if commercial_sf > 0:
        queue_write(sheet4_writes, 'C35', 1, "Commercial unit count")
        queue_write(sheet4_writes, 'D35', commercial_sf, "Commercial SF from 1A")
        queue_write(sheet4_writes, 'E35', commercial_sf, "Commercial total SF")
    else:
        queue_write(sheet4_writes, 'C35', 0, "No commercial in this project")
        queue_write(sheet4_writes, 'D35', 0, "No commercial SF")
        queue_write(sheet4_writes, 'E35', 0, "No commercial total SF")

    # --- Section 4.1: Parking ---
    log.append("")
    log.append("--- Parking (counts from 1A, SF estimated) ---")
    parking_items = [
        (39, 'Underground Parking', data['parking_underground']['spaces']),
        (40, 'Visitor Parking', data['parking_visitor']['spaces']),
        (41, 'Retail Parking', data['parking_retail']['spaces']),
    ]
    for row, label, spaces in parking_items:
        queue_write(sheet4_writes, f'C{row}', spaces, f"{label} spaces (from 1A)")
        queue_write(sheet4_writes, f'D{row}', PARKING_SF_PER_SPACE,
                    f"ESTIMATED: {PARKING_SF_PER_SPACE} SF/space (industry standard)")

    # --- Section 4.2: Back of House ---
    log.append("")
    log.append("--- Back of House (ESTIMATED) ---")
    mech_sf = round(data['total_units'] * 12, -2)  # ~12 SF/unit, rounded to 100
    boh_items = [
        (45, 'Loading Dock', 500, "DEFAULT: 500 SF"),
        (46, 'Building Management Office', 200, "DEFAULT: 200 SF"),
        (47, 'Security Office', 150, "DEFAULT: 150 SF"),
        (48, 'Maintenance Workshop', 300, "DEFAULT: 300 SF"),
        (49, 'Mechanical Penthouse', mech_sf,
         f"ESTIMATED: {data['total_units']} units x 12 SF/unit = {mech_sf} SF"),
    ]
    for row, label, total_sf, note in boh_items:
        queue_write(sheet4_writes, f'C{row}', 1, f"{label} quantity")
        queue_write(sheet4_writes, f'D{row}', total_sf, note)
        queue_write(sheet4_writes, f'E{row}', total_sf, f"{label} total SF")

    # --- Verification: Target GFA ---
    log.append("")
    log.append("--- Verification ---")
    queue_write(sheet4_writes, 'E64', round(gfa),
                f"Target GFA ({'from 1A' if data.get('gfa') else 'ESTIMATED from net rentable / 0.88'})")

    # ===================================================================
    # SHEET 5: Key Assumptions (true inputs only)
    # ===================================================================
    log.append("")
    log.append("=" * 60)
    log.append("SHEET 5: 5. Key Assumptions (true inputs only)")
    log.append("=" * 60)

    queue_write(sheet5_writes, 'E12', 0, "Land purchase duration (months)")
    queue_write(sheet5_writes, 'E13', 12, "Pre-development duration (months)")
    queue_write(sheet5_writes, 'E14', 18, "Construction duration (months)")
    queue_write(sheet5_writes, 'E16', 0, "Stabilized duration (months)")
    queue_write(sheet5_writes, 'F15', -3, "Lease-up offset (months)")
    queue_write(sheet5_writes, 'E37', 0.08, "Profit percentage (8%)")

    # Development charges — from selected municipality or skip
    if municipality:
        dc = municipality['rates']
        dc_label = municipality['name']
        queue_write(sheet5_writes, 'R57', dc['1bed'], f"{dc_label} DC: 1-Bed — ${dc['1bed']:,}")
        queue_write(sheet5_writes, 'R58', dc['2bed'], f"{dc_label} DC: 2-Bed — ${dc['2bed']:,}")
        queue_write(sheet5_writes, 'R59', dc['3bed'], f"{dc_label} DC: 3-Bed — ${dc['3bed']:,}")
        if municipality['notes']:
            log.append(f"  DC NOTES: {municipality['notes']}")
    else:
        log.append("  DC RATES: No municipality selected — cells R57:R59 left unchanged (template defaults)")

    # Building type — affects which Altus Cost Guide row Sheet 5 should reference
    # Sheet 5 F29 currently points to "13-39 Storeys" (Sheet 13 row 7)
    # Mid-rise would be "Up to 12 Storeys" (Sheet 13 row 6)
    log.append(f"  BUILDING TYPE: {building_type}")
    if building_type == 'mid-rise':
        log.append("  *** FLAG: Building is mid-rise but Sheet 5 F29 references '13-39 Storeys'.")
        log.append("      Noor should verify and update the Altus height category if needed.")

    # ===================================================================
    # FLAGS FOR NOOR'S REVIEW
    # ===================================================================
    log.append("")
    log.append("=" * 60)
    log.append("FLAGS FOR NOOR'S REVIEW")
    log.append("=" * 60)
    log.append("1. ALTUS COST GUIDE COLUMNS: Sheet 5 O48/P48 reference Ottawa columns (H/I)")
    log.append("   instead of GTA columns (F/G) on the Altus Cost Guide sheet.")
    log.append("   Parking refs (O49/P49) correctly use GTA. This is a pre-existing")
    log.append("   template issue — not changed by this automation.")
    log.append("")
    log.append(f"2. ALTUS HEIGHT CATEGORY: Building type set to '{building_type}'.")
    log.append(f"   Sheet 5 F29 currently points to '13-39 Storeys' (Sheet 13 row 7).")
    log.append(f"   Estimated floor count: {est_floors}.")
    if building_type == 'mid-rise':
        log.append("   *** BUILDING IS MID-RISE — Noor must update F29 to 'Up to 12 Storeys'.")
    log.append("")
    log.append("3. EXTERNAL WORKBOOK REFERENCES: Sheet 1 rows 70-77, 92-97, 107-113,")
    log.append("   115-116, 120, 125-126, 132 reference '[2]Typical Conv.Operating Expenses'")
    log.append("   which is not included. These cells show stale Birchmount values.")
    log.append("   G22 (submetering fee) was overwritten with the 1A value.")

    # ===================================================================
    # SAVE — apply all queued writes via ZIP/XML writer
    # ===================================================================
    def _make_modifier(writes_dict):
        """Create a modifier function for save_workbook from a writes dict."""
        def modifier(sheet_root, shared_strings, log_entries):
            for cell_ref, (value, description) in writes_dict.items():
                write_cell(sheet_root, cell_ref, value, shared_strings, log_entries, description)
        return modifier

    sheet_modifications = {}
    if sheet1_writes:
        sheet_modifications['xl/worksheets/sheet1.xml'] = _make_modifier(sheet1_writes)
    if sheet4_writes:
        sheet_modifications['xl/worksheets/sheet4.xml'] = _make_modifier(sheet4_writes)
    if sheet5_writes:
        sheet_modifications['xl/worksheets/sheet5.xml'] = _make_modifier(sheet5_writes)

    save_workbook(TEMPLATE_PATH, output_path, sheet_modifications, log)

    return log


# ---------------------------------------------------------------------------
# CLI ENTRY POINT
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python populate_reverse_1b.py <path_to_1a_proforma>")
        print("Example: python populate_reverse_1b.py reference/1A_Birchmount_2240.xlsx")
        sys.exit(1)

    input_path = sys.argv[1]
    if not os.path.exists(input_path):
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    if not os.path.exists(TEMPLATE_PATH):
        print(f"Error: Template not found: {TEMPLATE_PATH}")
        sys.exit(1)

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Parse the 1A
    print(f"Parsing 1A proforma: {input_path}")
    data = parse_1a(input_path)

    # Print parsed data summary
    print(f"\nProject: {data['address']}")
    print(f"Unit types found: {len(data['unit_types'])}")
    for u in data['unit_types']:
        print(f"  {u['label']}: {u['count']} units, {u['sf']} SF, ${u['rent']}/mo")
    print(f"Total units: {data['total_units']}")
    print(f"Total rentable SF: {data['total_rentable_sf']:,.0f}")
    print(f"Parking: {data['parking_underground']['spaces']} underground, "
          f"{data['parking_visitor']['spaces']} visitor, {data['parking_retail']['spaces']} retail")
    print(f"Storage: {data['storage']['count']} lockers @ ${data['storage']['fee']}/mo")
    print(f"Commercial: {data['commercial']['sf']} SF @ ${data['commercial']['rate']}/SF")
    print(f"Vacancy: {data['vacancy_rate']:.1%} residential, {data['commercial_vacancy']:.1%} commercial")
    print(f"Cap rates: {', '.join(f'{c:.2%}' for c in data['cap_rates'])}")
    if data.get('gfa'):
        print(f"GFA: {data['gfa']:,.0f} (from 1A)")
    else:
        print(f"GFA: will estimate from net rentable SF")

    # --- Interactive selections ---

    # 1. Municipality for DC rates
    municipalities = load_dc_rates()
    municipality = select_municipality(municipalities)

    # 2. Building type (mid-rise vs high-rise)
    building_type = select_building_type(data['total_units'])

    # --- Generate output ---
    project_name = data['address'].split(',')[0].strip().replace(' ', '_') or "project"
    project_name = re.sub(r'[^\w\-]', '', project_name)
    today = date.today().strftime("%Y%m%d")
    output_filename = f"Reverse_1B_{project_name}_{today}.xlsx"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    # Populate the template
    print(f"\nPopulating template...")
    log = populate_template(data, output_path, municipality=municipality, building_type=building_type)

    # Save log
    log_filename = f"Reverse_1B_{project_name}_{today}_log.txt"
    log_path = os.path.join(OUTPUT_DIR, log_filename)
    with open(log_path, 'w') as f:
        f.write(f"SVN Rock — Reverse 1B Population Log\n")
        f.write(f"Source: {input_path}\n")
        f.write(f"Output: {output_path}\n")
        f.write(f"Municipality: {municipality['name'] if municipality else 'None selected'}\n")
        f.write(f"Building Type: {building_type}\n")
        f.write(f"Date: {date.today()}\n")
        f.write(f"\n")
        for line in log:
            f.write(line + "\n")

    print(f"\n{'='*60}")
    print(f"DONE!")
    print(f"{'='*60}")
    print(f"Output: {output_path}")
    print(f"Log:    {log_path}")
    if municipality:
        print(f"Municipality: {municipality['name']}")
        print(f"DC rates: 1-Bed ${municipality['rates']['1bed']:,} | "
              f"2-Bed ${municipality['rates']['2bed']:,} | "
              f"3-Bed ${municipality['rates']['3bed']:,}")
    print(f"Building type: {building_type}")
    print(f"\nLog contains {len([l for l in log if l.startswith('  ')])} cell writes "
          f"and {len([l for l in log if 'ESTIMATED' in l])} estimated values.")
    print(f"Review the log file for every assumption made.")


if __name__ == "__main__":
    main()
