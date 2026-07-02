from __future__ import annotations

from io import StringIO

import pandas as pd
import pytest

from ab_testing_framework.data_loader import load_data


@pytest.mark.parametrize(
    "rows, expected",
    [
        ([(100, 4, 100, 6)], (100, 4, 100, 6)),
        ([(100, 4, 100, 6), (200, 8, 200, 10)], (300, 12, 300, 16)),
    ],
)
def test_load_data_from_mocked_aggregated_frame(
    load_data_csv_factory,
    aggregated_frame_factory,
    rows,
    expected,
):
    frame = aggregated_frame_factory(rows)
    experiment = load_data_csv_factory(frame)

    assert (experiment.visitors_a, experiment.conversions_a, experiment.visitors_b, experiment.conversions_b) == expected


def test_load_data_from_in_memory_aggregated_csv(csv_text_factory):
    csv = csv_text_factory(
        "visitors_a,conversions_a,visitors_b,conversions_b\n"
        "250,12,300,18\n"
    )

    experiment = load_data(csv)

    assert experiment.visitors_a == 250
    assert experiment.conversions_b == 18


@pytest.mark.parametrize(
    "rows, expected",
    [
        (
            [("A", 1), ("A", 0), ("B", 1), ("B", 1)],
            (2, 1, 2, 2),
        ),
        (
            [("a", 0), ("A", 1), ("b", 0), ("B", 1), ("B", 1)],
            (2, 1, 3, 2),
        ),
    ],
)
def test_load_data_from_in_memory_per_user_csv(csv_text_factory, rows, expected):
    lines = ["variant,converted"]
    lines.extend(f"{variant},{converted}" for variant, converted in rows)
    csv = csv_text_factory("\n".join(lines) + "\n")

    experiment = load_data(csv)

    assert (experiment.visitors_a, experiment.conversions_a, experiment.visitors_b, experiment.conversions_b) == expected


def test_load_data_rejects_non_numeric_aggregated_rows(monkeypatch):
    frame = pd.DataFrame(
        {
            "visitors_a": [100, "bad"],
            "conversions_a": [4, 8],
            "visitors_b": [100, 200],
            "conversions_b": [6, 10],
        }
    )
    monkeypatch.setattr("ab_testing_framework.data_loader.pd.read_csv", lambda *_args, **_kwargs: frame)

    with pytest.raises(ValueError, match="non-numeric"):
        load_data(StringIO("ignored"))


def test_load_data_rejects_treatment_rows_with_too_many_conversions(monkeypatch):
    frame = pd.DataFrame(
        {
            "visitors_a": [100],
            "conversions_a": [4],
            "visitors_b": [100],
            "conversions_b": [120],
        }
    )
    monkeypatch.setattr("ab_testing_framework.data_loader.pd.read_csv", lambda *_args, **_kwargs: frame)

    with pytest.raises(ValueError, match="conversions_b > visitors_b"):
        load_data(StringIO("ignored"))


def test_load_data_rejects_non_numeric_per_user_values(monkeypatch):
    frame = pd.DataFrame(
        {
            "variant": ["A", "B"],
            "converted": [1, "bad"],
        }
    )
    monkeypatch.setattr("ab_testing_framework.data_loader.pd.read_csv", lambda *_args, **_kwargs: frame)

    with pytest.raises(ValueError, match="contains non-numeric values"):
        load_data(StringIO("ignored"))


def test_load_data_rejects_missing_variant_side(monkeypatch):
    frame = pd.DataFrame(
        {
            "variant": ["A", "A"],
            "converted": [1, 0],
        }
    )
    monkeypatch.setattr("ab_testing_framework.data_loader.pd.read_csv", lambda *_args, **_kwargs: frame)

    with pytest.raises(ValueError, match="must have at least one row"):
        load_data(StringIO("ignored"))
