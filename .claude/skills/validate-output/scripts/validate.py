#!/usr/bin/env python3
"""
Thin wrapper around the existing validate_output.py at the repo root.

Takes a generated Reverse 1B output xlsx, re-parses its 1A source (from the
output filename via _find_1a_source), runs all XML-level checks, and prints
either a human-readable table or a machine-readable JSON report.

Usage:
    validate.py <output_xlsx> [--source <1A_path>] [--json]

If --source is not given, the engine's filename lookup is used.
Exit 0 on PASS (no errors), 1 on FAIL.
"""
import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]  # .../svn-rock/


def _fmt_table(xlsx_path: str, result: dict) -> str:
    name = os.path.basename(xlsx_path)
    status = "PASS" if result["passed"] else "FAIL"
    lines = []
    lines.append("=" * 72)
    lines.append(f"  {status}: {name}")
    lines.append(f"  {result['checks_passed']}/{result['checks_run']} checks passed")
    lines.append("=" * 72)
    lines.append("")
    lines.append(f"{'CATEGORY':<30} {'COUNT':>6}  DETAIL")
    lines.append("-" * 72)
    lines.append(f"{'Errors':<30} {len(result['errors']):>6}")
    for e in result["errors"]:
        lines.append(f"   [X] {e}")
    lines.append(f"{'Warnings':<30} {len(result['warnings']):>6}")
    for w in result["warnings"]:
        lines.append(f"   [!] {w}")
    if result["passed"] and not result["warnings"]:
        lines.append("   All checks passed.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx", help="Path to the generated Reverse 1B xlsx")
    ap.add_argument("--source", default=None,
                    help="Explicit path to the 1A source (.xlsx/.xls). "
                         "If omitted, looked up from output filename.")
    ap.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = ap.parse_args()

    xlsx = Path(args.xlsx).expanduser().resolve()
    if not xlsx.exists():
        msg = f"Output file not found: {xlsx}"
        if args.json:
            print(json.dumps({"passed": False, "errors": [msg], "warnings": [],
                              "checks_run": 1, "checks_passed": 0}))
        else:
            print(msg, file=sys.stderr)
        return 1

    if not (REPO_ROOT / "validate_output.py").exists():
        msg = f"Cannot locate validate_output.py in {REPO_ROOT}"
        if args.json:
            print(json.dumps({"passed": False, "errors": [msg], "warnings": [],
                              "checks_run": 1, "checks_passed": 0}))
        else:
            print(msg, file=sys.stderr)
        return 1

    sys.path.insert(0, str(REPO_ROOT))
    try:
        from validate_output import validate_output, _find_1a_source
        from populate_reverse_1b import parse_1a
    except Exception as e:
        msg = f"Failed to import engine: {e}"
        if args.json:
            print(json.dumps({"passed": False, "errors": [msg], "warnings": [],
                              "checks_run": 1, "checks_passed": 0}))
        else:
            print(msg, file=sys.stderr)
        return 1

    # Resolve 1A source
    if args.source:
        source = Path(args.source).expanduser().resolve()
        if not source.exists():
            msg = f"--source not found: {source}"
            if args.json:
                print(json.dumps({"passed": False, "errors": [msg], "warnings": [],
                                  "checks_run": 1, "checks_passed": 0}))
            else:
                print(msg, file=sys.stderr)
            return 1
        source_str = str(source)
    else:
        source_str = _find_1a_source(xlsx.name, str(REPO_ROOT))
        if source_str is None:
            msg = (f"No 1A source matched filename {xlsx.name!r}. "
                   f"Pass --source <path_to_1A>.")
            if args.json:
                print(json.dumps({"passed": False, "errors": [msg], "warnings": [],
                                  "checks_run": 1, "checks_passed": 0}))
            else:
                print(msg, file=sys.stderr)
            return 1

    try:
        parsed = parse_1a(source_str)
    except Exception as e:
        msg = f"Failed to parse 1A source {source_str}: {e}"
        if args.json:
            print(json.dumps({"passed": False, "errors": [msg], "warnings": [],
                              "checks_run": 1, "checks_passed": 0}))
        else:
            print(msg, file=sys.stderr)
        return 1

    result = validate_output(str(xlsx), parsed)

    if args.json:
        out = dict(result)
        out["xlsx"] = str(xlsx)
        out["source_1a"] = source_str
        print(json.dumps(out, indent=2))
    else:
        print(_fmt_table(str(xlsx), result))
        print(f"Source 1A: {source_str}")

    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
