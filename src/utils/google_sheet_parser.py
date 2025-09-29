"""Utilities for parsing semi-structured Google Sheet tabs into label/value maps."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple

import pandas as pd


@dataclass
class ParsedSheet:
    """Structured representation of a parsed tab."""

    label_value_map: Dict[str, str]
    cell_presence: Set[str]
    raw_rows: List[List[str]]

    def get_value(self, labels: Iterable[str]) -> Optional[str]:
        """Return the first value for any label alias (case-insensitive)."""

        for label in labels:
            key = label.strip().lower()
            if key in self.label_value_map:
                return self.label_value_map[key]
        return None

    def has_label(self, labels: Iterable[str]) -> bool:
        """Check whether any label alias is present in the sheet (case-insensitive)."""

        for label in labels:
            target = label.strip().lower()
            if not target:
                continue
            for cell in self.cell_presence:
                if target in cell:
                    return True
        return False


def _normalise_cell(value: object) -> Optional[str]:
    if isinstance(value, str):
        # Collapse repeated whitespace so label matching is consistent across tabs.
        stripped = " ".join(value.split())
        return stripped or None
    if value is None:
        return None
    return str(value).strip() or None


def parse_sheet(df: pd.DataFrame) -> ParsedSheet:
    """Parse a Google Sheet tab into label/value and presence mappings."""

    label_value_map: Dict[str, str] = {}
    cell_presence: Set[str] = set()
    raw_rows: List[List[str]] = []

    for _, row in df.iterrows():
        cleaned: List[str] = []
        for cell in row:
            normalised = _normalise_cell(cell)
            if normalised:
                cleaned.append(normalised)
                cell_presence.add(normalised.lower())
        if not cleaned:
            continue
        raw_rows.append(cleaned)
        _ingest_row(cleaned, label_value_map)

    return ParsedSheet(label_value_map=label_value_map, cell_presence=cell_presence, raw_rows=raw_rows)


def _ingest_row(cells: List[str], label_value_map: Dict[str, str]) -> None:
    """Populate the label/value map from a given row."""

    if not cells:
        return

    for idx, cell in enumerate(cells):
        lower_cell = cell.lower()

        if ":" in cell:
            label, remainder = cell.split(":", 1)
            label_key = label.strip().lower()
            value = remainder.strip() or None
            if not value and idx + 1 < len(cells):
                value = cells[idx + 1].strip()
            if value and label_key not in label_value_map:
                label_value_map[label_key] = value
            continue

        # Handle key/value without colon (e.g., first column label, second column value)
        if idx == 0 and len(cells) > 1:
            label_key = lower_cell
            value = cells[1].strip()
            if value and label_key not in label_value_map:
                label_value_map[label_key] = value

        # Handle table header rows by mapping column header to value in same column (only if header-like)
        if idx > 0 and idx < len(cells):
            header_candidate = cells[0].strip().lower()
            if header_candidate and header_candidate not in label_value_map and len(cells) == 2:
                label_value_map[header_candidate] = cells[1].strip()
                break


def flatten_dataframe(df: pd.DataFrame) -> List[Tuple[str, str]]:
    """Return a list of (label, value) pairs extracted from the tab."""
    parsed = parse_sheet(df)
    return list(parsed.label_value_map.items())
