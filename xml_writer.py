"""
SVN Rock — ZIP/XML Template Writer
====================================
Writes values directly into the XLSX ZIP archive's XML files,
bypassing openpyxl's save mechanism. This preserves all drawings,
images, charts, and formatting exactly as they are in the template.

Strategy: parse sheet XML with ElementTree to find and modify cells,
then splice the modified <sheetData> section back into the original
raw XML string. This preserves all namespace declarations, XML
declarations, and non-sheetData content byte-for-byte.
"""

import os
import zipfile
import shutil
import re
from xml.etree import ElementTree as ET

# Excel XLSX namespace
NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'


def _register_namespaces_from_xml(xml_bytes):
    """
    Scan raw XML for ALL xmlns declarations and register them with ET.
    Must be called before ET.fromstring() to preserve namespace prefixes.
    """
    text = xml_bytes if isinstance(xml_bytes, str) else xml_bytes.decode('utf-8', errors='replace')
    for match in re.finditer(r'xmlns(?::(\w+))?="([^"]+)"', text):
        prefix = match.group(1) or ''
        uri = match.group(2)
        ET.register_namespace(prefix, uri)


def _col_letter_to_num(col_str):
    """Convert column letter(s) to 1-based number. A=1, B=2, Z=26, AA=27."""
    num = 0
    for ch in col_str:
        num = num * 26 + (ord(ch) - ord('A') + 1)
    return num


def _parse_cell_ref(ref):
    """Split 'F2' into ('F', 2)."""
    match = re.match(r'^([A-Z]+)(\d+)$', ref)
    if match:
        return match.group(1), int(match.group(2))
    return None, None


def _find_or_create_row(sheet_data_el, row_num):
    """Find <row r="N"> in <sheetData>, or create it in the correct position."""
    for row_el in sheet_data_el.findall(f'{{{NS}}}row'):
        r = int(row_el.get('r', '0'))
        if r == row_num:
            return row_el
    # Row doesn't exist — create it in sorted position
    new_row = ET.SubElement(sheet_data_el, f'{{{NS}}}row')
    new_row.set('r', str(row_num))
    return new_row


def _find_or_create_cell(row_el, cell_ref, row_num):
    """Find <c r="F2"> in a row, or create it in the correct column position."""
    col_letter, _ = _parse_cell_ref(cell_ref)
    col_num = _col_letter_to_num(col_letter)

    for cell_el in row_el.findall(f'{{{NS}}}c'):
        if cell_el.get('r') == cell_ref:
            return cell_el
        # Check if we've passed where this cell should be
        existing_col, _ = _parse_cell_ref(cell_el.get('r', 'A1'))
        if existing_col and _col_letter_to_num(existing_col) > col_num:
            # Insert before this cell
            new_cell = ET.Element(f'{{{NS}}}c')
            new_cell.set('r', cell_ref)
            idx = list(row_el).index(cell_el)
            row_el.insert(idx, new_cell)
            return new_cell

    # Append at end of row
    new_cell = ET.SubElement(row_el, f'{{{NS}}}c')
    new_cell.set('r', cell_ref)
    return new_cell


def _add_shared_string(shared_strings, text):
    """
    Add a string to the shared strings table and return its index.
    If the string already exists, return its existing index.
    """
    for i, existing in enumerate(shared_strings):
        if existing == text:
            return i
    shared_strings.append(text)
    return len(shared_strings) - 1


def _parse_shared_strings(xml_bytes):
    """Parse sharedStrings.xml and return list of strings."""
    _register_namespaces_from_xml(xml_bytes)
    root = ET.fromstring(xml_bytes)
    strings = []
    for si in root.findall(f'{{{NS}}}si'):
        t = si.find(f'{{{NS}}}t')
        if t is not None and t.text is not None:
            strings.append(t.text)
        else:
            # Rich text with multiple <r> elements
            parts = []
            for r in si.findall(f'{{{NS}}}r'):
                rt = r.find(f'{{{NS}}}t')
                if rt is not None and rt.text:
                    parts.append(rt.text)
            strings.append(''.join(parts))
    return strings


def _patch_shared_strings_xml(original_xml_bytes, original_count, updated_strings):
    """
    Patch the original shared strings XML by appending new <si> entries.
    Preserves ALL original XML byte-for-byte — only adds new strings at the end
    and updates the count attributes.
    """
    new_strings = updated_strings[original_count:]

    if not new_strings:
        return original_xml_bytes

    xml_text = original_xml_bytes.decode('utf-8') if isinstance(original_xml_bytes, bytes) else original_xml_bytes

    # Build new <si> elements for appended strings
    new_si_xml = ''
    for s in new_strings:
        escaped = s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
        space_attr = ''
        if s and (s[0] == ' ' or s[-1] == ' ' or '\n' in s):
            space_attr = ' xml:space="preserve"'
        new_si_xml += f'<si><t{space_attr}>{escaped}</t></si>'

    # Insert before closing </sst> tag
    xml_text = xml_text.replace('</sst>', new_si_xml + '</sst>')

    # Update count and uniqueCount in the <sst> opening tag
    new_unique = len(updated_strings)
    xml_text = re.sub(r'(count=")(\d+)(")', lambda m: f'{m.group(1)}{new_unique}{m.group(3)}', xml_text, count=1)
    xml_text = re.sub(r'(uniqueCount=")(\d+)(")', lambda m: f'{m.group(1)}{new_unique}{m.group(3)}', xml_text, count=1)

    return xml_text.encode('utf-8')


def _splice_sheet_data(original_xml_bytes, modified_sheet_data_xml):
    """
    Replace the <sheetData>...</sheetData> section in the original raw XML
    with the modified version. Everything outside <sheetData> is preserved
    byte-for-byte — namespace declarations, XML declaration, all other elements.
    """
    xml_text = original_xml_bytes.decode('utf-8') if isinstance(original_xml_bytes, bytes) else original_xml_bytes

    # Find the original <sheetData>...</sheetData> block
    # Use a non-greedy match to find the section
    pattern = r'<sheetData[^>]*>.*?</sheetData>'
    match = re.search(pattern, xml_text, re.DOTALL)

    if not match:
        raise ValueError("Could not find <sheetData> section in sheet XML")

    # Replace the original sheetData with the modified version
    result = xml_text[:match.start()] + modified_sheet_data_xml + xml_text[match.end():]
    return result.encode('utf-8')


def _strip_external_formulas(sheet_root, log_entries):
    """
    Remove formulas that reference external workbooks (e.g. [2]Sheet!Cell).
    Keeps cached <v> values intact so Excel still shows numbers.
    Without this, the formulas library can't evaluate the file (cascading #REF!).
    """
    sheet_data = sheet_root.find(f'{{{NS}}}sheetData')
    if sheet_data is None:
        return 0

    count = 0
    for row_el in sheet_data.findall(f'{{{NS}}}row'):
        for cell_el in row_el.findall(f'{{{NS}}}c'):
            f_el = cell_el.find(f'{{{NS}}}f')
            if f_el is not None and f_el.text and '[' in f_el.text:
                cell_el.remove(f_el)
                count += 1

    if count > 0:
        log_entries.append(f"  Stripped {count} external workbook formulas (cached values preserved)")
    return count


def write_cell(sheet_root, cell_ref, value, shared_strings, log_entries, description="", force=False):
    """
    Write a value to a cell in the parsed sheet XML.

    - Numeric values: stored inline as <v>
    - String values: added to shared strings table, stored as index
    - Preserves the cell's style attribute
    - SKIPS cells that contain formulas (has <f> element) unless force=True
    - force=True: removes the formula and writes the value (for external refs)
    """
    col_letter, row_num = _parse_cell_ref(cell_ref)
    if col_letter is None:
        return False

    sheet_data = sheet_root.find(f'{{{NS}}}sheetData')
    if sheet_data is None:
        return False

    row_el = _find_or_create_row(sheet_data, row_num)
    cell_el = _find_or_create_cell(row_el, cell_ref, row_num)

    # Check for formula — never overwrite formula cells unless forced
    formula_el = cell_el.find(f'{{{NS}}}f')
    if formula_el is not None:
        if force:
            cell_el.remove(formula_el)
            log_entries.append(f"  FORCE {cell_ref}: removed formula '{formula_el.text}', replacing with value")
        else:
            log_entries.append(f"  SKIPPED {cell_ref}: contains formula '{formula_el.text}' — not overwritten")
            return False

    # Preserve existing style
    existing_style = cell_el.get('s')

    # Remove old value element if present
    old_v = cell_el.find(f'{{{NS}}}v')
    if old_v is not None:
        cell_el.remove(old_v)

    # Write the new value
    v_el = ET.SubElement(cell_el, f'{{{NS}}}v')

    if isinstance(value, str):
        idx = _add_shared_string(shared_strings, value)
        cell_el.set('t', 's')
        v_el.text = str(idx)
    elif isinstance(value, (int, float)):
        if 't' in cell_el.attrib:
            del cell_el.attrib['t']
        if isinstance(value, float):
            v_el.text = repr(value)
        else:
            v_el.text = str(value)
    elif value is None or value == 0:
        v_el.text = '0'
    else:
        v_el.text = str(value)

    # Restore style
    if existing_style:
        cell_el.set('s', existing_style)

    if description:
        log_entries.append(f"  {cell_ref} = {repr(value)}  ({description})")
    else:
        log_entries.append(f"  {cell_ref} = {repr(value)}")

    return True


def save_workbook(template_path, output_path, sheet_modifications, log_entries):
    """
    Copy the template XLSX and apply modifications to specific sheets.

    Uses a splice approach: parse <sheetData> with ElementTree to modify cells,
    then splice the modified <sheetData> back into the original raw XML.
    Everything outside <sheetData> is preserved byte-for-byte.
    """
    import tempfile

    # Read shared strings from template
    with zipfile.ZipFile(template_path, 'r') as z_in:
        ss_bytes = z_in.read('xl/sharedStrings.xml')
        shared_strings = _parse_shared_strings(ss_bytes)
        original_string_count = len(shared_strings)
        all_names = z_in.namelist()

    modified_sheets = set(sheet_modifications.keys())

    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        tmp_path = tmp.name

    with zipfile.ZipFile(template_path, 'r') as z_in:
        with zipfile.ZipFile(tmp_path, 'w', zipfile.ZIP_DEFLATED) as z_out:
            for name in all_names:
                if name in modified_sheets:
                    xml_bytes = z_in.read(name)

                    # Register namespaces before parsing
                    _register_namespaces_from_xml(xml_bytes)

                    # Parse the full XML to modify cells within <sheetData>
                    root = ET.fromstring(xml_bytes)
                    modify_fn = sheet_modifications[name]
                    modify_fn(root, shared_strings, log_entries)

                    # Remove external workbook formulas (e.g. [2]Sheet!Cell)
                    # These reference Noor's local file and cause #REF! in
                    # the formulas library. Cached values are preserved.
                    _strip_external_formulas(root, log_entries)

                    # Extract only the modified <sheetData> as a string
                    sheet_data = root.find(f'{{{NS}}}sheetData')
                    modified_sd = ET.tostring(sheet_data, encoding='unicode')

                    # Splice modified <sheetData> into original raw XML
                    patched_xml = _splice_sheet_data(xml_bytes, modified_sd)
                    z_out.writestr(name, patched_xml)

                elif name.startswith('xl/worksheets/') and name.endswith('.xml'):
                    # Non-modified sheets: strip external refs via regex
                    # (avoids full ET parse, preserves everything else)
                    raw = z_in.read(name)
                    xml_text = raw.decode('utf-8') if isinstance(raw, bytes) else raw
                    stripped, n = re.subn(r'<f>[^<]*\[[^\]]+\][^<]*</f>', '', xml_text)
                    if n > 0:
                        log_entries.append(f"  {name}: stripped {n} external formulas")
                    z_out.writestr(name, stripped.encode('utf-8'))

                elif name == 'xl/sharedStrings.xml':
                    pass  # handled after all sheets
                elif name == 'xl/workbook.xml':
                    # Force Excel to recalculate all formulas on open.
                    # Without this, formula cells show stale cached values
                    # from the template (e.g., Birchmount's 170 units).
                    wb_raw = z_in.read(name)
                    wb_str = wb_raw.decode('utf-8') if isinstance(wb_raw, bytes) else wb_raw
                    if 'fullCalcOnLoad' not in wb_str:
                        wb_str = wb_str.replace(
                            '<calcPr calcId="191029"/>',
                            '<calcPr calcId="191029" fullCalcOnLoad="1"/>'
                        )
                    z_out.writestr(name, wb_str.encode('utf-8') if isinstance(wb_str, str) else wb_str)
                    log_entries.append("  workbook.xml: added fullCalcOnLoad=1 to force formula recalculation")
                else:
                    z_out.writestr(name, z_in.read(name))

            # Patch shared strings (append new, preserve original)
            patched_ss = _patch_shared_strings_xml(ss_bytes, original_string_count, shared_strings)
            z_out.writestr('xl/sharedStrings.xml', patched_ss)

    shutil.move(tmp_path, output_path)
