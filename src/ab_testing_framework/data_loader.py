"""CSV loading helpers for experiment data."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .validation import ExperimentInput, validate_input

REQUIRED_COLUMNS = {
    "visitors_a",
    "conversions_a",
    "visitors_b",
    "conversions_b",
}

COLUMN_ORDER = [
    "visitors_a",
    "conversions_a",
    "visitors_b",
    "conversions_b",
]


def load_data(file_path: str | Path) -> ExperimentInput:
    frame = pd.read_csv(file_path)
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"missing required columns: {missing_list}")

    totals = frame[COLUMN_ORDER].sum(numeric_only=True)
    return validate_input(
        visitors_a=int(totals["visitors_a"]),
        conversions_a=int(totals["conversions_a"]),
        visitors_b=int(totals["visitors_b"]),
        conversions_b=int(totals["conversions_b"]),
    )
