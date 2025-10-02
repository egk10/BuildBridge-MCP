"""Parsers for Google Sheets manifest-driven extraction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import re

import pandas as pd

CSI_DIVISION_NAMES = {
    "00": "Procurement and Contracting Requirements",
    "01": "General Requirements",
    "02": "Existing Conditions",
    "03": "Concrete",
    "04": "Masonry",
    "05": "Metals",
    "06": "Wood, Plastics, and Composites",
    "07": "Thermal and Moisture Protection",
    "08": "Openings",
    "09": "Finishes",
    "10": "Specialties",
    "11": "Equipment",
    "12": "Furnishings",
    "13": "Special Construction",
    "14": "Conveying Equipment",
    "21": "Fire Suppression",
    "22": "Plumbing",
    "23": "Heating, Ventilating, and Air Conditioning (HVAC)",
    "25": "Integrated Automation",
    "26": "Electrical",
    "27": "Communications",
    "28": "Electronic Safety and Security",
    "31": "Earthwork",
    "32": "Exterior Improvements",
    "33": "Utilities",
    "34": "Transportation",
    "35": "Waterway and Marine Construction",
    "40": "Process Integration",
    "41": "Material Processing and Handling Equipment",
    "42": "Process Heating, Cooling, and Drying Equipment",
    "43": "Process Gas and Liquid Handling, Purification, and Storage Equipment",
    "44": "Pollution and Waste Control Equipment",
    "45": "Industry-Specific Manufacturing Equipment",
    "48": "Electrical Power Generation",
}


@dataclass
class ParserResult:
    tabs: List[Dict[str, Any]]
    project: Dict[str, Any]


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text in {"nan", "NaN", "#DIV/0!", "-", "—", ""}:
        return ""
    return text


def _to_number(value: Any) -> Optional[float]:
    text = _clean_text(value)
    if not text:
        return None

    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1]

    for ch in ["$", ",", " ", "%"]:
        text = text.replace(ch, "")
    text = text.replace("-", "-")  # normalize hyphen variants

    if not text:
        return None

    try:
        number = float(text)
    except ValueError:
        return None

    if negative:
        number *= -1
    return number


def _format_number(value: Optional[float]) -> Optional[str]:
    if value is None:
        return None
    if abs(value - round(value)) < 1e-6:
        return f"{int(round(value)):,}"
    return f"{value:,.2f}"


def _format_currency(value: Optional[float]) -> Optional[str]:
    number = _format_number(value)
    if number is None:
        return None
    return f"${number}"


def _find_label_value(df: pd.DataFrame, label: str) -> Optional[str]:
    label_upper = label.upper()
    rows = df.fillna(" ").values.tolist()
    column_count = df.shape[1]

    for row_idx, row in enumerate(rows[:20]):
        for col_idx, cell in enumerate(row):
            if _clean_text(cell).upper() == label_upper:
                # scan to the right on the same row
                for offset in range(1, min(6, column_count - col_idx)):
                    candidate = _clean_text(row[col_idx + offset])
                    if candidate:
                        return candidate
                # otherwise scan next row for a non-empty value
                if row_idx + 1 < len(rows):
                    next_row = rows[row_idx + 1]
                    for val in next_row:
                        candidate = _clean_text(val)
                        if candidate:
                            return candidate
    return None


def extract_summary_metrics(df: pd.DataFrame, project_id: str) -> Dict[str, Any]:
    df = df.fillna("")

    project_name = _find_label_value(df, "PROJECT:") or project_id.replace("_", " ").title()
    location = _find_label_value(df, "LOCATION:")
    client = _find_label_value(df, "CLIENT:")
    budget_date = _find_label_value(df, "DATE:")

    summary_row = df.iloc[7] if len(df) > 7 else pd.Series(dtype=object)
    total_row = df.iloc[118] if len(df) > 118 else pd.Series(dtype=object)
    direct_row = df.iloc[106] if len(df) > 106 else pd.Series(dtype=object)

    parking_stalls = _to_number(summary_row.iloc[3]) if not summary_row.empty else None
    gca_metric = _to_number(summary_row.iloc[5]) if not summary_row.empty else None
    gca_imperial = _to_number(summary_row.iloc[14]) if not summary_row.empty else None
    site_area_metric = _to_number(summary_row.iloc[16]) if not summary_row.empty else None
    total_units = _to_number(summary_row.iloc[12]) if not summary_row.empty else None
    total_gca_sf = _to_number(summary_row.iloc[20]) if not summary_row.empty else None

    subtotal_below_grade = _to_number(total_row.iloc[5]) if not total_row.empty else None
    subtotal_siteworks = _to_number(total_row.iloc[12]) if not total_row.empty else None
    total_project_cost = _to_number(total_row.iloc[14]) if not total_row.empty else None
    direct_cost = _to_number(direct_row.iloc[5]) if not direct_row.empty else None

    project_overview: Dict[str, Any] = {
        "Project_ID": project_id,
        "Project_Name": project_name,
        "Location": location,
        "Client": client,
        "Budget_Date": budget_date,
        "Total_Budget": total_project_cost,
        "Total_Budget_Display": _format_number(total_project_cost),
        "Total_Direct_Cost": direct_cost,
        "Building_Area_Metric": gca_metric,
        "Building_Area_Imperial": gca_imperial,
        "Total_Units": total_units,
        "Total_GCA_SF": total_gca_sf,
        "Site_Area_Metric": site_area_metric,
        "Parking_Stalls": parking_stalls,
        "Subtotal_Below_Grade": subtotal_below_grade,
        "Subtotal_Siteworks": subtotal_siteworks,
    }

    summary_tab = {
        "contract_id": "project_info",
        "source_tab": "Project Summary",
        "values": {
            "project_name": project_name,
            "location": location,
            "client": client,
            "budget_date": budget_date,
            "building_area_metric": _format_number(gca_metric),
            "building_area_imperial": _format_number(gca_imperial),
            "functional_units": _format_number(total_units),
            "parking_stalls": _format_number(parking_stalls),
            "total_project_cost": _format_number(total_project_cost),
            "total_direct_cost": _format_number(direct_cost),
            "site_area_metric": _format_number(site_area_metric),
            "total_gca_sf": _format_number(total_gca_sf),
        },
    }

    suite_tab = {
        "contract_id": "suite_count",
        "source_tab": "Project Summary",
        "values": {
            "total_suites": _format_number(total_units),
        },
    }

    financial_tab = {
        "contract_id": "financial_summary",
        "source_tab": "Project Summary",
        "values": {
            "total_project_cost": _format_number(total_project_cost),
            "total_direct_cost": _format_number(direct_cost),
            "subtotal_below_grade": _format_number(subtotal_below_grade),
            "subtotal_siteworks": _format_number(subtotal_siteworks),
        },
    }

    return {
        "tabs": [summary_tab, suite_tab, financial_tab],
        "project": {k: v for k, v in project_overview.items() if v is not None},
    }


def extract_gca_metrics(df: pd.DataFrame, project_id: str) -> Dict[str, Any]:
    df = df.fillna("")
    rows = df.values.tolist()

    parking_below_grade = None
    parking_above_grade = None
    total_gca_sf = None
    total_gca_m2 = None

    for row in rows:
        label = _clean_text(row[1] if len(row) > 1 else "")
        parking_value = _to_number(row[3] if len(row) > 3 else None)
        
        # Extract parking values
        if "SUB-TOTAL - BELOW GRADE" in label.upper():
            parking_below_grade = parking_value
        if "SUB-TOTAL - ABOVE GRADE PARKING" in label.upper():
            parking_above_grade = parking_value
        
        # Extract Total GCA from the "Total GCA" row
        # Column H (index 7) = GCA (M2), Column I (index 8) = GCA (SF)
        if "TOTAL GCA" in label.upper() and "BELOW" not in label.upper() and "ABOVE" not in label.upper():
            total_gca_m2 = _to_number(row[7] if len(row) > 7 else None)
            total_gca_sf = _to_number(row[8] if len(row) > 8 else None)

    total_parking = None
    if parking_below_grade is not None or parking_above_grade is not None:
        total_parking = (parking_below_grade or 0) + (parking_above_grade or 0)

    gca_tab = {
        "contract_id": "gca_stats",
        "source_tab": "GCA Stats",
        "values": {
            "parking_below_grade": _format_number(parking_below_grade),
            "parking_above_grade": _format_number(parking_above_grade),
            "parking_total": _format_number(total_parking),
            "total_gca_sf": _format_number(total_gca_sf),
            "total_gca_m2": _format_number(total_gca_m2),
        },
    }

    return {
        "tabs": [gca_tab],
        "project": {
            key: value
            for key, value in {
                "Parking_Below_Grade": parking_below_grade,
                "Parking_Above_Grade": parking_above_grade,
                "Parking_Total": total_parking,
                "Total_GCA_SF": total_gca_sf,
                "Total_GCA_M2": total_gca_m2,
            }.items()
            if value is not None
        },
    }


def extract_division_costs(df: pd.DataFrame, project_id: str) -> Dict[str, Any]:
    df = df.fillna("")

    divisions: List[Dict[str, Any]] = []
    aggregate_totals: Dict[str, float] = {}

    for _, row in df.iterrows():
        marker = _clean_text(row.iloc[0] if len(row) > 0 else "")
        if marker.upper() != "DIV":
            continue

        code_raw = _clean_text(row.iloc[2] if len(row) > 2 else "")
        if not code_raw:
            continue

        digits = re.findall(r"\d+", code_raw)
        if digits:
            numeric_value = int(digits[0])
            if numeric_value < 100:
                division_code = f"{numeric_value:02d}"
            else:
                division_code = str(numeric_value)
        else:
            division_code = code_raw.upper()

        label = _clean_text(row.iloc[3] if len(row) > 3 else "")
        quantity = _to_number(row.iloc[4] if len(row) > 4 else None)
        unit = _clean_text(row.iloc[5] if len(row) > 5 else "") or None
        rate = _to_number(row.iloc[6] if len(row) > 6 else None)
        total_cost = _to_number(row.iloc[8] if len(row) > 8 else None)
        cost_per_m2 = _to_number(row.iloc[9] if len(row) > 9 else None)
        cost_per_sf = _to_number(row.iloc[10] if len(row) > 10 else None)
        cost_per_stall = _to_number(row.iloc[11] if len(row) > 11 else None)
        percent_total = _to_number(row.iloc[12] if len(row) > 12 else None)

        standard_name = CSI_DIVISION_NAMES.get(division_code)
        display_name = standard_name or label or division_code

        divisions.append(
            {
                "code": division_code,
                "label": label or None,
                "display_name": display_name,
                "standard_name": standard_name,
                "quantity": quantity,
                "unit": unit,
                "rate": rate,
                "rate_display": _format_currency(rate),
                "total_cost": total_cost,
                "total_cost_display": _format_currency(total_cost),
                "cost_per_m2": cost_per_m2,
                "cost_per_m2_display": _format_currency(cost_per_m2),
                "cost_per_sf": cost_per_sf,
                "cost_per_sf_display": _format_currency(cost_per_sf),
                "cost_per_parking_stall": cost_per_stall,
                "cost_per_parking_stall_display": _format_currency(cost_per_stall),
                "percent_total": percent_total,
                "percent_total_display": f"{percent_total:.2f}%" if percent_total is not None else None,
            }
        )

        if total_cost is not None:
            aggregate_totals[division_code] = total_cost

    total_cost_sum = sum(aggregate_totals.values()) if aggregate_totals else None

    cost_tab = {
        "contract_id": "cost_breakdown",
        "source_tab": "Below Grade 1 Detail",
        "values": {
            "project_id": project_id,
            "division_count": len(divisions),
            "total_cost": total_cost_sum,
            "total_cost_display": _format_currency(total_cost_sum),
            "divisions": divisions,
        },
    }

    project_payload = {
        "Division_Cost_Totals": aggregate_totals,
    }
    if total_cost_sum is not None:
        project_payload["Division_Cost_Total"] = total_cost_sum

    return {
        "tabs": [cost_tab],
        "project": project_payload,
    }


PARSER_REGISTRY = {
    "extract_summary_metrics": extract_summary_metrics,
    "extract_gca_metrics": extract_gca_metrics,
    "extract_division_costs": extract_division_costs,
}
