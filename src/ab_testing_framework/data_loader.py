"""CSV loading helpers for experiment data.

Supported CSV formats
---------------------
**Aggregated (one row)**  — each column holds the total for that variant::

    visitors_a,conversions_a,visitors_b,conversions_b
    10000,450,10000,520

**Segmented (multiple rows)** — each row is a segment (device, country, etc.).
All rows are summed before the test is run::

    visitors_a,conversions_a,visitors_b,conversions_b
    3000,135,3100,160
    7000,315,6900,360

**Per-user (one row per visitor)** — detected automatically when values in the
conversion columns are exclusively 0 or 1.  The loader counts the rows that
belong to each variant using a ``variant`` column (values ``"A"`` / ``"B"``) and
a ``converted`` column (0/1)::

    variant,converted
    A,0
    A,1
    B,0
    B,1

All non-numeric rows and completely empty rows are dropped silently.
"""

from __future__ import annotations

import csv
import logging
from io import StringIO
from pathlib import Path
from typing import IO

import pandas as pd

from .validation import ExperimentInput, validate_input

logger = logging.getLogger(__name__)

# ── aggregated-format columns ─────────────────────────────────────────────────
_AGG_REQUIRED = {"visitors_a", "conversions_a", "visitors_b", "conversions_b"}
_AGG_ORDER    = ["visitors_a", "conversions_a", "visitors_b", "conversions_b"]

# ── per-user-format columns ───────────────────────────────────────────────────
_USER_REQUIRED = {"variant", "converted"}


def _decode_text(raw: bytes | str) -> tuple[str, str]:
    if isinstance(raw, str):
        return raw, "text"

    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue

    return raw.decode("utf-8", errors="replace"), "utf-8-replace"


def _detect_delimiter(text: str) -> str:
    sample = "\n".join(text.splitlines()[:5])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        candidates = [",", ";", "\t", "|"]
        counts = {delimiter: sample.count(delimiter) for delimiter in candidates}
        delimiter, count = max(counts.items(), key=lambda item: item[1])
        return delimiter if count > 0 else ","


def _read_csv_frame(file_path: str | Path | IO) -> tuple[pd.DataFrame, str, str]:
    if isinstance(file_path, (str, Path)):
        raw = Path(file_path).read_bytes()
    else:
        raw = file_path.read()

    text, encoding = _decode_text(raw)
    delimiter = _detect_delimiter(text)
    frame = pd.read_csv(StringIO(text), sep=delimiter)
    logger.info(
        "csv_loaded",
        extra={"encoding": encoding, "delimiter": delimiter, "row_count": len(frame)},
    )
    return frame, encoding, delimiter


def _is_binary_column(series: pd.Series) -> bool:
    """Return True if all non-null values in series are 0 or 1."""
    unique = set(series.dropna().unique())
    return unique.issubset({0, 1, 0.0, 1.0})


def _load_aggregated(frame: pd.DataFrame) -> ExperimentInput:
    """Sum aggregated / segmented rows and validate."""
    # drop rows that are completely empty or all-NaN
    frame = frame.dropna(how="all")

    for col in _AGG_ORDER:
        if not pd.api.types.is_numeric_dtype(frame[col]):
            raise ValueError(
                f"Column '{col}' contains non-numeric values. "
                "Check your CSV for text or missing data."
            )

    totals = frame[_AGG_ORDER].sum(numeric_only=True)

    # sanity-check: conversions should not exceed visitors in any individual row
    bad_a = frame[frame["conversions_a"] > frame["visitors_a"]]
    bad_b = frame[frame["conversions_b"] > frame["visitors_b"]]
    if not bad_a.empty:
        raise ValueError(
            f"Row(s) {bad_a.index.tolist()} have conversions_a > visitors_a."
        )
    if not bad_b.empty:
        raise ValueError(
            f"Row(s) {bad_b.index.tolist()} have conversions_b > visitors_b."
        )

    return validate_input(
        visitors_a=int(totals["visitors_a"]),
        conversions_a=int(totals["conversions_a"]),
        visitors_b=int(totals["visitors_b"]),
        conversions_b=int(totals["conversions_b"]),
    )


def _load_per_user(frame: pd.DataFrame) -> ExperimentInput:
    """Aggregate a per-user CSV (variant column A/B + converted column 0/1)."""
    frame = frame.dropna(subset=["variant", "converted"])

    # normalise variant labels to uppercase A/B
    frame = frame.copy()
    frame["variant"] = frame["variant"].astype(str).str.strip().str.upper()
    valid_variants = {"A", "B"}
    unknown = set(frame["variant"].unique()) - valid_variants
    if unknown:
        raise ValueError(
            f"Unknown variant labels {unknown!r}. Expected 'A' and 'B'."
        )

    converted = pd.to_numeric(frame["converted"], errors="coerce")
    if converted.isna().any():
        raise ValueError(
            "Column 'converted' contains non-numeric values. "
            "Expected 0 or 1 for each row."
        )
    frame = frame.copy()
    frame["converted"] = converted

    if not _is_binary_column(frame["converted"]):
        raise ValueError(
            "Column 'converted' must contain only 0 or 1 values in per-user format."
        )

    group = frame.groupby("variant")["converted"]
    visitors_a    = int(group.count().get("A", 0))
    conversions_a = int(group.sum().get("A", 0))
    visitors_b    = int(group.count().get("B", 0))
    conversions_b = int(group.sum().get("B", 0))

    if visitors_a == 0 or visitors_b == 0:
        raise ValueError(
            "Both variants 'A' and 'B' must have at least one row in per-user format."
        )

    return validate_input(
        visitors_a=visitors_a,
        conversions_a=conversions_a,
        visitors_b=visitors_b,
        conversions_b=conversions_b,
    )


def load_data(file_path: str | Path | IO) -> ExperimentInput:
    """
    Load experiment data from a CSV file.

    Automatically detects whether the file is in aggregated/segmented format
    or per-user format and parses accordingly.  See module docstring for
    examples of each format.

    Parameters
    ----------
    file_path:
        Path to a CSV file, or any file-like object accepted by ``pd.read_csv``.

    Returns
    -------
    ExperimentInput
        Validated experiment parameters ready for statistical analysis.

    Raises
    ------
    ValueError
        If required columns are missing, values are non-numeric, or
        per-row validation fails.
    """
    frame, _encoding, _delimiter = _read_csv_frame(file_path)

    columns = set(frame.columns.str.strip().str.lower())

    # ── per-user format ───────────────────────────────────────────────────────
    if _USER_REQUIRED.issubset(columns):
        return _load_per_user(frame)

    # ── aggregated / segmented format ─────────────────────────────────────────
    missing = _AGG_REQUIRED.difference(columns)
    if missing:
        raise ValueError(
            f"Missing required columns: {', '.join(sorted(missing))}. "
            "Expected either:\n"
            "  • Aggregated format: visitors_a, conversions_a, visitors_b, conversions_b\n"
            "  • Per-user format:   variant (A/B), converted (0/1)"
        )

    return _load_aggregated(frame)
