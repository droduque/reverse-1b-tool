"""
SVN Rock — Reverse 1B Web App
==============================
Flask web app that wraps populate_reverse_1b.py in a browser interface.
Users upload a 1A proforma, pick municipality + building type, and
download a ready-to-review Reverse 1B Excel file.

Also serves the client presentation / sensitivity tool.
"""

import os
import tempfile
import re
import json
import glob
import logging
from datetime import date

import requests
from flask import (Flask, render_template, request, send_file,
                   redirect, url_for, flash, jsonify)

import math

from populate_reverse_1b import (
    parse_1a,
    load_dc_rates,
    populate_template,
    export_project_json,
    import_reverse_1b,
    calculate_verified_metrics,
    diff_projects,
    _log_municipality_gap,
    HIGH_RISE_FLOOR_THRESHOLD,
    FINANCING_PROGRAMS,
    PARKING_SF_PER_SPACE,
    GFA_EFFICIENCY,
)
from data_freshness import get_freshness_report, get_alerts
from validate_output import validate_output, validate_financials

app = Flask(__name__)
app.secret_key = os.urandom(24)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')

# Load DC rates once at startup
MUNICIPALITIES = load_dc_rates()

# Fetch Bank of Canada prime rate once at startup
# Policy rate + 2.20% spread = prime. Falls back to 4.45% if API unavailable.
PRIME_RATE_CACHE = {'prime': 0.0445, 'policy': 0.0225, 'fetched': None}

def fetch_prime_rate():
    """Fetch Bank of Canada overnight rate target, derive prime = policy + 2.20%."""
    try:
        url = 'https://www.bankofcanada.ca/valet/observations/V39079/json?recent=1'
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        obs = resp.json()['observations'][-1]
        policy = float(obs['V39079']['v']) / 100  # API returns e.g. 2.25 meaning 2.25%
        prime = policy + 0.0220
        PRIME_RATE_CACHE['policy'] = policy
        PRIME_RATE_CACHE['prime'] = prime
        PRIME_RATE_CACHE['fetched'] = date.today().isoformat()
        logging.info(f"Bank of Canada prime rate: {prime:.2%} (policy {policy:.2%} + 2.20%)")
    except Exception as e:
        logging.warning(f"Could not fetch Bank of Canada rate, using default 4.45%: {e}")

fetch_prime_rate()


@app.route('/refresh-prime', methods=['POST'])
def refresh_prime():
    """Re-fetch the Bank of Canada prime rate on demand."""
    fetch_prime_rate()
    return jsonify({
        'prime': round(PRIME_RATE_CACHE['prime'] * 100, 2),
        'fetched': PRIME_RATE_CACHE['fetched'],
    })


@app.route('/', methods=['GET'])
def index():
    """Main page — upload form with municipality and building type selectors."""
    alerts = get_alerts()
    freshness = get_freshness_report()
    return render_template('index.html', municipalities=MUNICIPALITIES,
                           current_year=date.today().year,
                           freshness_alerts=alerts, freshness_report=freshness,
                           prime_rate=PRIME_RATE_CACHE)


@app.route('/preview', methods=['POST'])
def preview():
    """Parse uploaded 1A and return project summary (for auto-detecting building type + municipality)."""

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

        # GFA: from 1A if available, else estimate
        gfa = data.get('gfa')
        gfa_estimated = gfa is None
        if gfa is None:
            gfa = round(data['total_rentable_sf'] / GFA_EFFICIENCY)

        # Parking SF: spaces × standard SF/space
        total_spaces = (data['parking_underground']['spaces']
                        + data['parking_visitor']['spaces']
                        + data['parking_retail']['spaces'])
        parking_sf = total_spaces * PARKING_SF_PER_SPACE

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
            'gfa': gfa,
            'gfa_estimated': gfa_estimated,
            'parking_sf': parking_sf,
            'parking_spaces': total_spaces,
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

    # Get financing program selection
    fp_key = request.form.get('financing_program', 'cmhc_mli_100')
    financing_program = FINANCING_PROGRAMS.get(fp_key, FINANCING_PROGRAMS['cmhc_mli_100'])

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

    # Get construction duration override (blank = auto from unit count)
    construction_months = None
    constr_str = request.form.get('construction_months', '').strip()
    if constr_str != '':
        try:
            construction_months = int(constr_str)
        except ValueError:
            pass

    # Get GFA and parking SF overrides
    gfa_override = None
    gfa_str = request.form.get('gfa_override', '').strip()
    if gfa_str:
        try:
            gfa_override = float(gfa_str)
        except ValueError:
            pass

    parking_sf_override = None
    parking_sf_str = request.form.get('parking_sf_override', '').strip()
    if parking_sf_str:
        try:
            parking_sf_override = float(parking_sf_str)
        except ValueError:
            pass

    # Get construction financing parameters (form shows %, we convert to decimal)
    default_prime = PRIME_RATE_CACHE['prime']
    construction_financing = {}
    for field, key, default in [
        ('mezz_debt_pct', 'mezz_debt_pct', 15),
        ('mezz_prime_rate', 'mezz_prime_rate', default_prime * 100),
        ('mezz_margin', 'mezz_margin', 3.5),
        ('bank_debt_pct', 'bank_debt_pct', 75),
        ('bank_prime_rate', 'bank_prime_rate', default_prime * 100),
        ('bank_margin', 'bank_margin', 1.0),
        ('financing_fees_pct', 'financing_fees_pct', 1.0),
        ('financing_contingency_pct', 'financing_contingency_pct', 0.5),
    ]:
        val_str = request.form.get(field, '').strip()
        try:
            construction_financing[key] = float(val_str) / 100 if val_str else default / 100
        except ValueError:
            construction_financing[key] = default / 100

    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        # Parse the 1A
        data = parse_1a(tmp_path)

        # Collect parser warnings (Improvement #3)
        parse_warnings = data.get('parse_warnings', [])

        # Municipality gap tracking (Improvement #6)
        if municipality is None and muni_idx != 'skip':
            _log_municipality_gap(data.get('address', ''), 'auto-detect failed', OUTPUT_DIR)

        # Generate output filename
        project_name = data['address'].split(',')[0].strip().replace(' ', '_') or "project"
        project_name = re.sub(r'[^\w\-]', '', project_name)
        today = date.today().strftime("%Y%m%d")
        output_filename = f"Reverse_1B_{project_name}_{today}.xlsx"

        # Ensure output directory exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # Generate Excel to output directory (persistent, for presentation tool)
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        # Apply property tax overrides if the user changed them
        if 'tax_rate' in tax_overrides:
            data['tax_rate'] = tax_overrides['tax_rate']
        if 'assessed_value' in tax_overrides:
            data['assessed_value'] = tax_overrides['assessed_value']

        log = populate_template(data, output_path, municipality=municipality,
                                building_type=building_type, financing_program=financing_program,
                                construction_months=construction_months,
                                gfa_override=gfa_override, parking_sf_override=parking_sf_override,
                                construction_financing=construction_financing)

        # Also export the project JSON for the presentation tool
        json_filename = f"Reverse_1B_{project_name}_{today}.json"
        json_path = os.path.join(OUTPUT_DIR, json_filename)
        export_project_json(data, json_path, municipality=municipality, building_type=building_type,
                            financing_program=financing_program, construction_financing=construction_financing)

        # Save the generation log — documents every cell written, estimated,
        # and skipped. Serves as an audit trail for Noor's review.
        log_filename = f"Reverse_1B_{project_name}_{today}_log.txt"
        log_path = os.path.join(OUTPUT_DIR, log_filename)
        with open(log_path, 'w') as f:
            f.write(f"SVN Rock — Reverse 1B Population Log\n")
            f.write(f"Source: {file.filename}\n")
            f.write(f"Output: {output_path}\n")
            f.write(f"Municipality: {municipality['name'] if municipality else 'None selected'}\n")
            f.write(f"Building Type: {building_type}\n")
            f.write(f"Date: {date.today().isoformat()}\n\n")
            f.write('\n'.join(log))

        # Validate before delivering — catch #VALUE!, wrong types, stale data
        validation = validate_output(output_path, data)
        if not validation['passed']:
            error_list = '; '.join(validation['errors'][:5])
            flash(f'Generation failed validation ({len(validation["errors"])} errors): {error_list}')
            os.unlink(output_path)  # don't leave a bad file around
            if os.path.exists(json_path):
                os.unlink(json_path)
            return redirect(url_for('index'))

        # Extract verified metrics — uses formulas library to evaluate real Excel
        # formulas, falls back to Python calculation if library unavailable
        with open(json_path) as f:
            proj = json.load(f)
        verified = calculate_verified_metrics(proj, xlsx_path=output_path)
        if verified:
            proj['verified'] = verified
            proj['project']['source'] = 'auto-calc'
            with open(json_path, 'w') as f:
                json.dump(proj, f, indent=2)

        # Financial sanity checks (Improvement #2 + #4)
        # Reuse proj dict from above — no need to re-read the JSON file
        fin_check = validate_financials(proj, proj.get('verified'))
        all_warnings = parse_warnings + fin_check.get('warnings', [])

        # Municipality warning
        if municipality is None and muni_idx != 'skip':
            all_warnings.insert(0, f"Municipality not found for {data.get('address', 'this project')}. Using template defaults for DC rates.")

        # Redirect to results page with THIS project's specific links.
        # Pass warnings as pipe-separated query param (avoids session state issues).
        present_slug = json_filename.replace('.json', '')
        return redirect(url_for('results',
                                download=output_filename,
                                present=present_slug,
                                address=data['address'],
                                units=data['total_units'],
                                warnings='|'.join(all_warnings) if all_warnings else ''))

    except Exception as e:
        flash(f'Error processing file: {str(e)}')
        return redirect(url_for('index'))

    finally:
        # Clean up temp upload
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# RESULTS PAGE — shown after generation, with project-specific links
# ---------------------------------------------------------------------------

@app.route('/results')
def results():
    """
    Post-generation results page. Shows download + presentation links
    for the SPECIFIC project that was just generated. Each user lands on
    their own results page, so 10 simultaneous users never cross wires.
    """
    download = request.args.get('download', '')
    present = request.args.get('present', '')
    address = request.args.get('address', 'Project')
    units = request.args.get('units', '')
    warnings_str = request.args.get('warnings', '')
    warnings = [w for w in warnings_str.split('|') if w] if warnings_str else []
    return render_template('results.html',
                           download_filename=download,
                           present_slug=present,
                           address=address,
                           units=units,
                           warnings=warnings)


@app.route('/download/<filename>')
def download_file(filename):
    """Serve a generated file from the output directory."""
    safe_name = os.path.basename(filename)
    file_path = os.path.join(OUTPUT_DIR, safe_name)
    if not os.path.exists(file_path):
        flash('File not found.')
        return redirect(url_for('index'))
    return send_file(
        file_path,
        as_attachment=True,
        download_name=safe_name,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )


# ---------------------------------------------------------------------------
# PRESENTATION TOOL ROUTES
# ---------------------------------------------------------------------------

@app.route('/projects', methods=['GET'])
def list_projects():
    """List all generated projects (JSON files in output/)."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # Sort by modification time (most recently generated first), not alphabetically
    json_files = sorted(glob.glob(os.path.join(OUTPUT_DIR, '*.json')),
                        key=lambda f: os.path.getmtime(f), reverse=True)
    projects = []
    for jf in json_files:
        try:
            with open(jf) as f:
                proj = json.load(f)
            projects.append({
                'filename': os.path.basename(jf),
                'name': proj['project']['name'],
                'address': proj['project']['address'],
                'municipality': proj['project']['municipality'],
                'generated': proj['project']['generated'],
                'units': proj['units']['total'],
            })
        except (json.JSONDecodeError, KeyError):
            continue
    return jsonify(projects)


@app.route('/projects/<filename>', methods=['GET'])
def get_project(filename):
    """Return a specific project's JSON data."""
    # Sanitize filename to prevent path traversal
    safe_name = os.path.basename(filename)
    if not safe_name.endswith('.json'):
        safe_name += '.json'
    filepath = os.path.join(OUTPUT_DIR, safe_name)
    if not os.path.exists(filepath):
        return jsonify({'error': 'Project not found'}), 404
    with open(filepath) as f:
        return jsonify(json.load(f))


@app.route('/present/<filename>')
def present(filename):
    """Serve the presentation tool for a specific project.
    We inject the filename via a small script tag to avoid Jinja/JSX conflicts."""
    # Read the static presentation HTML and inject the project filename
    html_path = os.path.join(os.path.dirname(__file__), 'templates', 'presentation.html')
    with open(html_path) as f:
        html = f.read()
    # Replace the placeholder with the actual filename
    html = html.replace('__PROJECT_FILENAME__', filename)
    from flask import Response
    return Response(html, mimetype='text/html')


@app.route('/present')
def present_latest():
    """Serve the presentation tool with the most recent project."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    json_files = sorted(glob.glob(os.path.join(OUTPUT_DIR, '*.json')),
                        key=lambda f: os.path.getmtime(f), reverse=True)
    if not json_files:
        flash('No projects generated yet. Upload a 1A first.')
        return redirect(url_for('index'))
    latest = os.path.basename(json_files[0])
    return redirect(url_for('present', filename=latest.replace('.json', '')))


def _project_json_to_data(proj):
    """
    Reconstruct the parse_1a()-style data dict from a project JSON.
    populate_template() expects keys like 'unit_types', 'parking_underground',
    'cap_rates' (list), 'mgmt_fee_pct', etc. The project JSON uses a different
    structure (nested objects, cap_rates as dict), so we translate here.
    """
    data = {}
    data['title'] = "Estimated Stabilized Value - " + proj['project']['address']
    data['address'] = proj['project']['address']
    data['unit_types'] = [
        {'label': u['label'], 'sf': u['sf'], 'count': u['count'], 'rent': u['rent']}
        for u in proj['units']['types']
    ]
    data['total_units'] = proj['units']['total']
    data['total_rentable_sf'] = proj['areas']['total_rentable_sf']
    data['gfa'] = proj['areas']['gfa']
    data['amenity_sf'] = proj['areas']['amenity_sf']

    data['parking_underground'] = proj['parking']['underground']
    data['parking_visitor'] = proj['parking']['visitor']
    data['parking_retail'] = proj['parking']['retail']
    data['storage'] = proj['storage']

    # Submetering can be a number or an object in the JSON
    sub = proj.get('submetering', 0)
    if isinstance(sub, dict):
        data['submetering'] = sub
    else:
        data['submetering'] = {'count': proj['units']['total'], 'fee': 20}

    data['commercial'] = {
        'sf': proj['commercial']['sf'],
        'rate': proj['commercial']['rate'],
    }
    data['commercial_vacancy'] = proj['commercial']['vacancy']
    data['vacancy_rate'] = proj['vacancy_rate']

    # cap_rates: populate_template expects a list [best, base, worst]
    data['cap_rates'] = [
        proj['cap_rates']['best'],
        proj['cap_rates']['base'],
        proj['cap_rates']['worst'],
    ]

    data['mgmt_fee_pct'] = proj['opex']['mgmt_fee_pct']
    data['tax_rate'] = proj['opex']['tax_rate']
    data['assessed_value'] = proj['opex']['assessed_value_per_unit']
    data['reserve_pct'] = proj['opex']['reserve_pct']

    # Expenses sub-dict — populate_template reads from data['expenses']
    # for per-unit costs; if missing it uses defaults, so we populate them
    data['expenses'] = {
        'rm': proj['opex']['rm_per_unit'],
        'staffing': proj['opex']['staffing_per_unit'],
        'insurance': proj['opex']['insurance_per_unit'],
        'marketing': proj['opex']['marketing_per_unit'],
        'ga': proj['opex']['ga_per_unit'],
    }

    return data


@app.route('/export-scenario', methods=['POST'])
def export_scenario():
    """
    Re-generate a Reverse 1B Excel with adjusted sensitivity values.
    Receives JSON with the project filename and slider overrides,
    applies them to the original project data, and returns a new Excel.
    """
    payload = request.get_json()
    if not payload:
        return jsonify({'error': 'No JSON payload'}), 400

    filename = payload.get('filename', '')
    if not filename:
        return jsonify({'error': 'Missing filename'}), 400

    # Load the original project JSON
    safe_name = os.path.basename(filename)
    if not safe_name.endswith('.json'):
        safe_name += '.json'
    json_path = os.path.join(OUTPUT_DIR, safe_name)
    if not os.path.exists(json_path):
        return jsonify({'error': 'Project not found'}), 404

    with open(json_path) as f:
        proj = json.load(f)

    # Reconstruct the data dict that populate_template() expects
    data = _project_json_to_data(proj)

    # Apply scenario overrides
    rent_multiplier = payload.get('rentMultiplier', 1.0)
    new_cap_rate = payload.get('capRate')
    new_vacancy = payload.get('vacancyRate')
    construction_psf = payload.get('constructionPsf')
    new_interest_rate = payload.get('interestRate')
    scenario_program_key = payload.get('programKey')

    # Adjust rents by multiplier
    if rent_multiplier and rent_multiplier != 1.0:
        for ut in data['unit_types']:
            ut['rent'] = round(ut['rent'] * rent_multiplier, 2)

    # Update cap rates — shift best/worst proportionally to base change
    if new_cap_rate and len(data['cap_rates']) >= 3:
        original_base = data['cap_rates'][1]
        if original_base > 0:
            shift = new_cap_rate - original_base
            data['cap_rates'][0] = round(data['cap_rates'][0] + shift, 6)
            data['cap_rates'][1] = round(new_cap_rate, 6)
            data['cap_rates'][2] = round(data['cap_rates'][2] + shift, 6)

    # Update vacancy rate
    if new_vacancy is not None:
        data['vacancy_rate'] = new_vacancy

    # Log construction PSF override (it doesn't map directly to Excel cells)
    if construction_psf:
        app.logger.info(
            f"Scenario export for {safe_name}: construction PSF override = ${construction_psf}/sf "
            f"(not written to Excel — Altus guide reference only)"
        )

    # Resolve municipality for DC rates
    municipality = None
    muni_name = proj['project'].get('municipality', '')
    if muni_name and muni_name != 'Not selected':
        for m in MUNICIPALITIES:
            if m['name'] == muni_name:
                municipality = m
                break

    building_type = proj['project'].get('building_type', 'high-rise')

    # Resolve financing program — prefer payload key, fall back to original JSON
    fp_key = scenario_program_key or proj.get('financing', {}).get('program_key', 'cmhc_mli_100')
    financing_program = dict(FINANCING_PROGRAMS.get(fp_key, FINANCING_PROGRAMS['cmhc_mli_100']))
    if new_interest_rate is not None:
        financing_program['interest_rate'] = new_interest_rate

    # Generate the scenario Excel
    project_name = data['address'].split(',')[0].strip().replace(' ', '_') or "project"
    project_name = re.sub(r'[^\w\-]', '', project_name)
    today = date.today().strftime("%Y%m%d")
    output_filename = f"Reverse_1B_{project_name}_{today}_scenario.xlsx"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    try:
        populate_template(data, output_path, municipality=municipality, building_type=building_type, financing_program=financing_program)

        # Validate before delivering
        validation = validate_output(output_path, data)
        if not validation['passed']:
            error_list = '; '.join(validation['errors'][:5])
            os.unlink(output_path)
            return jsonify({'error': f'Validation failed: {error_list}'}), 500

        return send_file(
            output_path,
            as_attachment=True,
            download_name=output_filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# REIMPORT — upload a Noor-reviewed Reverse 1B to update presentation data
# ---------------------------------------------------------------------------

@app.route('/reimport', methods=['GET'])
def reimport_page():
    """Show the reimport upload form."""
    return render_template('reimport.html')


@app.route('/reimport', methods=['POST'])
def reimport():
    """
    Accept a reviewed Reverse 1B Excel, extract all data into JSON,
    and redirect to the presentation tool with verified numbers.
    """
    if 'reverse1b' not in request.files:
        flash('Please upload a Reverse 1B Excel file.')
        return redirect(url_for('reimport_page'))

    file = request.files['reverse1b']
    if file.filename == '':
        flash('Please select a file.')
        return redirect(url_for('reimport_page'))

    ext = os.path.splitext(file.filename)[1].lower()
    if ext != '.xlsx':
        flash('File must be .xlsx format (the Reverse 1B output).')
        return redirect(url_for('reimport_page'))

    # Save to temp
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        # Extract data from the reviewed Reverse 1B
        project = import_reverse_1b(tmp_path)

        # Generate JSON filename
        project_name = project['project']['name'].replace(' ', '_')
        project_name = re.sub(r'[^\w\-]', '', project_name)
        today = date.today().strftime("%Y%m%d")
        json_filename = f"Reverse_1B_{project_name}_{today}_verified.json"
        json_path = os.path.join(OUTPUT_DIR, json_filename)

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(json_path, 'w') as f:
            json.dump(project, f, indent=2)

        # Diff against original generation (Improvement #5)
        diff_changes = []
        try:
            # Find the original (non-verified, non-scenario) JSON by project name
            for fn in os.listdir(OUTPUT_DIR):
                if (fn.endswith('.json') and project_name in fn
                        and '_verified' not in fn and '_scenario' not in fn):
                    orig_path = os.path.join(OUTPUT_DIR, fn)
                    with open(orig_path) as f:
                        original = json.load(f)
                    diff_result = diff_projects(original, project)
                    diff_changes = diff_result.get('changes', [])
                    # Save structured diff
                    diff_path = os.path.join(OUTPUT_DIR,
                                             json_filename.replace('.json', '_diff.json'))
                    with open(diff_path, 'w') as f:
                        json.dump(diff_result, f, indent=2)
                    break
        except Exception:
            pass  # non-critical — don't break reimport

        # Redirect to presentation tool
        present_slug = json_filename.replace('.json', '')
        return redirect(url_for('results_reimport',
                                present=present_slug,
                                address=project['project']['address'],
                                units=project['units']['total'],
                                diff='|'.join(diff_changes) if diff_changes else ''))

    except Exception as e:
        flash(f'Error reading Reverse 1B: {str(e)}')
        return redirect(url_for('reimport_page'))

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.route('/results-reimport')
def results_reimport():
    """Post-reimport results page — shows presentation link only (no Excel download)."""
    present = request.args.get('present', '')
    address = request.args.get('address', 'Project')
    units = request.args.get('units', '')
    diff_str = request.args.get('diff', '')
    diff_changes = [d for d in diff_str.split('|') if d] if diff_str else []
    return render_template('results_reimport.html',
                           present_slug=present,
                           address=address,
                           units=units,
                           diff_changes=diff_changes)


if __name__ == '__main__':
    app.run(debug=True, port=5001)
