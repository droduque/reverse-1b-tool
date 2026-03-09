"""
SVN Rock — Reverse 1B Web App
==============================
Flask web app that wraps populate_reverse_1b.py in a browser interface.
Users upload a 1A proforma, pick municipality + building type, and
download a ready-to-review Reverse 1B Excel file.
"""

import os
import tempfile
import re
from datetime import date

from flask import Flask, render_template, request, send_file, redirect, url_for, flash

import math

from populate_reverse_1b import (
    parse_1a,
    load_dc_rates,
    populate_template,
    HIGH_RISE_FLOOR_THRESHOLD,
)

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Load DC rates once at startup
MUNICIPALITIES = load_dc_rates()


@app.route('/', methods=['GET'])
def index():
    """Main page — upload form with municipality and building type selectors."""
    return render_template('index.html', municipalities=MUNICIPALITIES, current_year=date.today().year)


@app.route('/preview', methods=['POST'])
def preview():
    """Parse uploaded 1A and return project summary (for auto-detecting building type + municipality)."""
    from flask import jsonify

    if 'proforma' not in request.files:
        return jsonify({'error': 'No file'}), 400

    file = request.files['proforma']
    ext = os.path.splitext(file.filename)[1].lower()

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        data = parse_1a(tmp_path)
        est_floors = math.ceil(data['total_units'] / 12)

        # Auto-detect municipality from project address
        muni_match = detect_municipality(data.get('address', ''))

        return jsonify({
            'address': data['address'],
            'total_units': data['total_units'],
            'unit_types': len(data['unit_types']),
            'est_floors': est_floors,
            'building_type': 'mid-rise' if est_floors < HIGH_RISE_FLOOR_THRESHOLD else 'high-rise',
            'municipality_index': muni_match['index'],
            'municipality_name': muni_match['name'],
            'tax_rate': data.get('tax_rate', 0),
            'assessed_value': data.get('assessed_value', 0),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def detect_municipality(address):
    """
    Match a project address to a municipality in Kanen's DC list.
    Returns {'index': int or None, 'name': str}.

    Only matches the CITY — doesn't guess the zone. If a city has
    multiple zones, returns the first match so the user can pick the
    correct zone from nearby options.
    """
    if not address or not MUNICIPALITIES:
        return {'index': None, 'name': ''}

    addr_upper = address.upper()

    # Build a list of city keywords to check against the address.
    # Order matters — check specific names before generic ones.
    # Each entry: (keyword to find in address, index in MUNICIPALITIES list)
    city_keywords = []
    for i, m in enumerate(MUNICIPALITIES):
        # Extract city name: "Toronto, ON" -> "TORONTO"
        # "Burlington, ON (Built Boundary)" -> "BURLINGTON"
        city = m['name'].split(',')[0].split('(')[0].strip().upper()
        city_keywords.append((city, i, m['name']))

    # Sort by length descending so "Niagara Falls" matches before "Niagara"
    city_keywords.sort(key=lambda x: len(x[0]), reverse=True)

    # Also handle common alternate names
    aliases = {
        'SCARBOROUGH': 'SCARBOROUGH',
        'ETOBICOKE': 'ETOBICOKE',
        'NORTH YORK': 'TORONTO',
        'EAST YORK': 'TORONTO',
        'YORK': 'TORONTO',
    }

    # First try direct match against municipality city names
    for keyword, idx, full_name in city_keywords:
        if keyword in addr_upper:
            return {'index': idx, 'name': full_name}

    # Then try aliases
    for alias, target_city in aliases.items():
        if alias in addr_upper:
            for keyword, idx, full_name in city_keywords:
                city = full_name.split(',')[0].split('(')[0].strip().upper()
                if city == target_city:
                    return {'index': idx, 'name': full_name}

    return {'index': None, 'name': ''}


@app.route('/generate', methods=['POST'])
def generate():
    """Process the uploaded 1A and return the generated Reverse 1B."""

    # Validate file upload
    if 'proforma' not in request.files:
        flash('Please upload a 1A proforma file.')
        return redirect(url_for('index'))

    file = request.files['proforma']
    if file.filename == '':
        flash('Please select a file.')
        return redirect(url_for('index'))

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ('.xlsx', '.xls'):
        flash('File must be .xlsx or .xls format.')
        return redirect(url_for('index'))

    # Get municipality selection
    municipality = None
    muni_idx = request.form.get('municipality', '')
    if muni_idx and muni_idx != 'skip':
        try:
            idx = int(muni_idx)
            if 0 <= idx < len(MUNICIPALITIES):
                municipality = MUNICIPALITIES[idx]
        except (ValueError, IndexError):
            pass

    # Get building type
    building_type = request.form.get('building_type', 'high-rise')
    if building_type not in ('mid-rise', 'high-rise'):
        building_type = 'high-rise'

    # Get property tax overrides (empty string = use 1A value, 0 = explicitly zero)
    tax_overrides = {}
    tax_rate_str = request.form.get('tax_rate', '').strip()
    assessed_str = request.form.get('assessed_value', '').strip()
    if tax_rate_str != '':
        try:
            tax_overrides['tax_rate'] = float(tax_rate_str)
        except ValueError:
            pass
    if assessed_str != '':
        try:
            tax_overrides['assessed_value'] = float(assessed_str)
        except ValueError:
            pass

    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        # Parse the 1A
        data = parse_1a(tmp_path)

        # Generate output filename
        project_name = data['address'].split(',')[0].strip().replace(' ', '_') or "project"
        project_name = re.sub(r'[^\w\-]', '', project_name)
        today = date.today().strftime("%Y%m%d")
        output_filename = f"Reverse_1B_{project_name}_{today}.xlsx"

        # Generate to temp file
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as out_tmp:
            output_path = out_tmp.name

        # Apply property tax overrides if the user changed them
        if 'tax_rate' in tax_overrides:
            data['tax_rate'] = tax_overrides['tax_rate']
        if 'assessed_value' in tax_overrides:
            data['assessed_value'] = tax_overrides['assessed_value']

        populate_template(data, output_path, municipality=municipality, building_type=building_type)

        # Send file to browser for download
        return send_file(
            output_path,
            as_attachment=True,
            download_name=output_filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

    except Exception as e:
        flash(f'Error processing file: {str(e)}')
        return redirect(url_for('index'))

    finally:
        # Clean up temp upload
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


if __name__ == '__main__':
    app.run(debug=True, port=5001)
