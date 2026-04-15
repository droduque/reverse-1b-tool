#!/usr/bin/env python3
"""
Thin wrapper around the existing populate_reverse_1b.py engine at the repo root.

Validates the 1A path (must exist and be .xlsx/.xls), then imports and runs the
engine's parse_1a() + populate_template() with defaults. No re-implementation of
cell mapping or consolidation — single source of truth stays in the repo script.

Usage:
    populate.py <path_to_1A.xlsx> [--municipality NAME] [--building-type high-rise|mid-rise]
                                  [--output-dir DIR] [--json]

Exit 0 on success, non-zero on validation/runtime error.
Prints a JSON summary when --json is passed; otherwise a short human summary.
"""
import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]  # .../svn-rock/
VALID_EXT = {".xlsx", ".xls"}


def _fail(msg: str, as_json: bool) -> int:
    if as_json:
        print(json.dumps({"ok": False, "error": msg}))
    else:
        print(f"ERROR: {msg}", file=sys.stderr)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="Path to 1A proforma (.xlsx or .xls)")
    ap.add_argument("--municipality", default=None,
                    help="Municipality name for DC rates (exact match in data_registry). Default: none.")
    ap.add_argument("--building-type", default=None, choices=["mid-rise", "high-rise"],
                    help="Override building type. Default: auto-select by unit count.")
    ap.add_argument("--output-dir", default=None,
                    help="Output directory. Default: <repo>/output/")
    ap.add_argument("--json", action="store_true", help="Emit machine-readable JSON result")
    args = ap.parse_args()

    as_json = args.json

    # --- Input validation ---
    src = Path(args.input).expanduser().resolve()
    if not src.exists():
        return _fail(f"Input not found: {src}", as_json)
    if src.suffix.lower() not in VALID_EXT:
        return _fail(f"Input must be .xlsx or .xls, got {src.suffix}", as_json)

    if not REPO_ROOT.exists() or not (REPO_ROOT / "populate_reverse_1b.py").exists():
        return _fail(f"Cannot locate populate_reverse_1b.py in {REPO_ROOT}", as_json)

    sys.path.insert(0, str(REPO_ROOT))

    try:
        from populate_reverse_1b import (
            parse_1a, populate_template, export_project_json,
            load_dc_rates, select_building_type, TEMPLATE_PATH, OUTPUT_DIR,
        )
    except Exception as e:
        return _fail(f"Failed to import engine: {e}", as_json)

    if not os.path.exists(TEMPLATE_PATH):
        return _fail(f"Template missing: {TEMPLATE_PATH}", as_json)

    out_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Parse ---
    try:
        data = parse_1a(str(src))
    except Exception as e:
        return _fail(f"parse_1a failed: {e}", as_json)

    # --- Resolve municipality non-interactively ---
    municipality = None
    if args.municipality:
        for m in load_dc_rates():
            if m.get("name", "").lower() == args.municipality.lower():
                municipality = m
                break
        if municipality is None:
            return _fail(f"Municipality not found in registry: {args.municipality}", as_json)

    # --- Resolve building type non-interactively ---
    if args.building_type:
        building_type = args.building_type
    else:
        total_units = data.get("total_units", 0)
        building_type = "high-rise" if total_units >= 75 else "mid-rise"

    # --- Output path (mirror main() naming) ---
    project_name = (data.get("address", "") or "project").split(",")[0].strip().replace(" ", "_")
    project_name = re.sub(r"[^\w\-]", "", project_name) or "project"
    today = date.today().strftime("%Y%m%d")
    out_path = out_dir / f"Reverse_1B_{project_name}_{today}.xlsx"
    json_path = out_dir / f"Reverse_1B_{project_name}_{today}.json"

    # --- Populate ---
    try:
        log = populate_template(data, str(out_path),
                                municipality=municipality,
                                building_type=building_type)
    except Exception as e:
        return _fail(f"populate_template failed: {e}", as_json)

    # --- Export companion JSON ---
    try:
        export_project_json(data, str(json_path),
                            municipality=municipality,
                            building_type=building_type)
    except Exception as e:
        # Non-fatal: output xlsx still valid.
        log.append(f"WARNING: export_project_json failed: {e}")

    # --- Verify output exists and has size ---
    if not out_path.exists() or out_path.stat().st_size == 0:
        return _fail(f"Output file missing or empty: {out_path}", as_json)

    result = {
        "ok": True,
        "input": str(src),
        "output_xlsx": str(out_path),
        "output_json": str(json_path) if json_path.exists() else None,
        "municipality": municipality["name"] if municipality else None,
        "building_type": building_type,
        "total_units": data.get("total_units"),
        "unit_types_count": len(data.get("unit_types", [])),
        "consolidated": len(data.get("unit_types", [])) > 3,
        "log_lines": len(log),
    }

    if as_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"OK  {out_path}")
        print(f"    units={result['total_units']}  types={result['unit_types_count']}  "
              f"consolidated={result['consolidated']}  building={building_type}  "
              f"municipality={result['municipality']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
