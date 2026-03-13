"""
SVN Rock — Data Freshness Tracker
==================================
Reads data_registry.json and provides:
- Status for each dataset (Current / Expiring Soon / Expired / Not Integrated)
- Alerts for datasets needing attention
- A compact "Data Sources" footer for output logs and reports

Usage:
    from data_freshness import get_freshness_report, get_data_sources_footer, get_alerts
"""

import json
import os
from datetime import date, datetime, timedelta

REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "data_registry.json")

# How many days before expiry to flag "Expiring Soon"
EXPIRING_SOON_DAYS = 30


def load_registry():
    """Load the data registry JSON file."""
    with open(REGISTRY_PATH, 'r') as f:
        return json.load(f)


def _parse_date(date_str):
    """Parse a YYYY-MM-DD string into a date object. Returns None if null/empty."""
    if not date_str:
        return None
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def _calc_status(dataset, today=None):
    """
    Calculate freshness status for a single dataset.
    Returns one of: "Current", "Expiring Soon", "Expired", "Not Integrated"
    """
    if today is None:
        today = date.today()

    coverage_end = _parse_date(dataset.get("coverage_end"))
    last_updated = _parse_date(dataset.get("last_updated"))

    # If never updated or no coverage period, it's not integrated yet
    if not last_updated or not coverage_end:
        return "Not Integrated"

    if today > coverage_end:
        return "Expired"

    if today >= coverage_end - timedelta(days=EXPIRING_SOON_DAYS):
        return "Expiring Soon"

    return "Current"


def _format_date_display(date_str):
    """
    Format a YYYY-MM-DD string into a readable date like 'March 9th, 2026'.
    Returns empty string if null/empty.
    """
    if not date_str:
        return ""
    d = _parse_date(date_str)
    if not d:
        return ""
    # Ordinal suffix for the day
    day = d.day
    if 11 <= day <= 13:
        suffix = "th"
    elif day % 10 == 1:
        suffix = "st"
    elif day % 10 == 2:
        suffix = "nd"
    elif day % 10 == 3:
        suffix = "rd"
    else:
        suffix = "th"
    return d.strftime(f"%B {day}{suffix}, %Y")


def get_freshness_report(today=None):
    """
    Return a list of dicts with dataset info + calculated status.
    Includes both raw dates and formatted display dates for the UI.
    """
    if today is None:
        today = date.today()

    registry = load_registry()
    report = []

    for ds in registry["datasets"]:
        status = _calc_status(ds, today)
        report.append({
            "id": ds["id"],
            "name": ds["name"],
            "source": ds["source"],
            "file": ds.get("file"),
            "coverage_end": ds.get("coverage_end"),
            "coverage_end_display": _format_date_display(ds.get("coverage_end")),
            "last_updated": ds.get("last_updated"),
            "last_updated_display": _format_date_display(ds.get("last_updated")),
            "next_release": ds.get("next_release"),
            "status": status,
            "notes": ds.get("notes", ""),
        })

    return report


def get_alerts(today=None):
    """
    Return a list of alert strings for datasets that need attention.
    Only returns alerts for Expiring Soon, Expired, or Not Integrated datasets.
    """
    report = get_freshness_report(today)
    alerts = []

    for ds in report:
        if ds["status"] == "Expired":
            end = ds["coverage_end"] or "unknown"
            next_rel = ds.get("next_release")
            msg = f"{ds['name']}: EXPIRED (valid through {end})"
            if next_rel:
                msg += f" — next release expected {next_rel}"
            alerts.append({"level": "expired", "message": msg})

        elif ds["status"] == "Expiring Soon":
            end = ds["coverage_end"]
            alerts.append({
                "level": "warning",
                "message": f"{ds['name']}: expiring {end} — update before next client meeting"
            })

        elif ds["status"] == "Not Integrated":
            alerts.append({
                "level": "info",
                "message": f"{ds['name']}: not yet integrated ({ds['source']})"
            })

    return alerts


def get_data_sources_footer(today=None):
    """
    Return a compact one-line string listing each active dataset and its valid-through date.
    Suitable for appending to logs, reports, or output.

    Example: "DC Rates: Kanen (through 2026-12-31) | Property Tax: Kanen (2025-2026) | ..."
    """
    report = get_freshness_report(today)
    parts = []

    # Only include integrated datasets (skip Not Integrated)
    for ds in report:
        if ds["status"] == "Not Integrated":
            continue

        # Short name for display
        short_names = {
            "dc_rates": "DC Rates",
            "property_tax_rates": "Property Tax",
            "altus_cost_guide": "Construction Costs",
            "reverse_1b_template": "Template",
            "opex_defaults": "OpEx Defaults",
            "area_estimation": "Area Rules",
            "cmhc_rental_market": "CMHC Rental",
        }
        label = short_names.get(ds["id"], ds["name"])

        # Short source
        source = ds["source"].split("(")[0].strip()
        if source.startswith("Kanen"):
            source = "Kanen"
        elif source.startswith("Noor"):
            source = "Noor"
        elif source.startswith("Altus"):
            source = "Altus"
        elif source.startswith("Derived"):
            source = "Noor-reviewed"

        end = ds["coverage_end"] or "TBD"
        status_flag = ""
        if ds["status"] == "Expired":
            status_flag = " [EXPIRED]"
        elif ds["status"] == "Expiring Soon":
            status_flag = " [UPDATE SOON]"

        parts.append(f"{label}: {source} (through {end}){status_flag}")

    return " | ".join(parts)


def get_data_sources_log_block(today=None):
    """
    Return a multi-line log block listing all datasets with their status.
    Suitable for appending to the generation log file.
    """
    report = get_freshness_report(today)
    lines = []
    lines.append("=" * 60)
    lines.append("DATA SOURCES & FRESHNESS")
    lines.append("=" * 60)

    for ds in report:
        status_marker = {
            "Current": "OK",
            "Expiring Soon": "!! EXPIRING SOON",
            "Expired": "** EXPIRED **",
            "Not Integrated": "-- not integrated",
        }.get(ds["status"], ds["status"])

        lines.append(f"  {ds['name']}")
        lines.append(f"    Source: {ds['source']}")
        lines.append(f"    Status: [{status_marker}]")
        if ds["coverage_end"]:
            lines.append(f"    Valid through: {ds['coverage_end']}")
        if ds["last_updated"]:
            lines.append(f"    Last updated: {ds['last_updated']}")
        if ds.get("next_release"):
            lines.append(f"    Next release: {ds['next_release']}")
        if ds["status"] in ("Expired", "Expiring Soon"):
            lines.append(f"    ACTION NEEDED: Get updated data before client meetings")
        lines.append("")

    lines.append(f"Report generated: {date.today()}")
    return lines


# CLI entry point — run standalone to check freshness
if __name__ == "__main__":
    print()
    alerts = get_alerts()
    if alerts:
        print("ALERTS:")
        for a in alerts:
            icon = {"expired": "!!!", "warning": " ! ", "info": "   "}.get(a["level"], "   ")
            print(f"  [{icon}] {a['message']}")
        print()

    print("DATA SOURCES:")
    print(f"  {get_data_sources_footer()}")
    print()

    for line in get_data_sources_log_block():
        print(line)
