"""Shared pytest fixtures and factories for the test suite."""

from __future__ import annotations

import sys
from pathlib import Path
from collections.abc import Callable
from io import StringIO

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
	sys.path.insert(0, str(SRC_PATH))

from ab_testing_framework.analysis import AbTestResult
from ab_testing_framework.data_loader import load_data
from ab_testing_framework import run_ab_test
from ab_testing_framework.validation import ExperimentInput, validate_input


@pytest.fixture
def experiment_factory() -> Callable[..., ExperimentInput]:
	"""Build validated experiment inputs with sensible defaults."""

	def _factory(
		visitors_a: int = 10_000,
		conversions_a: int = 450,
		visitors_b: int = 10_000,
		conversions_b: int = 520,
		alpha: float = 0.05,
	) -> ExperimentInput:
		return validate_input(
			visitors_a=visitors_a,
			conversions_a=conversions_a,
			visitors_b=visitors_b,
			conversions_b=conversions_b,
			alpha=alpha,
		)

	return _factory


@pytest.fixture
def result_factory() -> Callable[..., AbTestResult]:
	"""Build a complete A/B test result for dashboard and report tests."""

	def _factory(
		visitors_a: int = 10_000,
		conversions_a: int = 450,
		visitors_b: int = 10_000,
		conversions_b: int = 520,
		alpha: float = 0.05,
		alternative: str = "two-sided",
	) -> AbTestResult:
		return run_ab_test(
			visitors_a=visitors_a,
			conversions_a=conversions_a,
			visitors_b=visitors_b,
			conversions_b=conversions_b,
			alpha=alpha,
			alternative=alternative,
		)

	return _factory


@pytest.fixture
def csv_text_factory() -> Callable[[str], StringIO]:
	"""Create in-memory CSV streams for data-loader tests."""

	def _factory(text: str) -> StringIO:
		return StringIO(text)

	return _factory


@pytest.fixture
def aggregated_frame_factory() -> Callable[[list[tuple[int, int, int, int]]], pd.DataFrame]:
	"""Create aggregated-format frames used by loader and integration tests."""

	def _factory(rows: list[tuple[int, int, int, int]]) -> pd.DataFrame:
		return pd.DataFrame(
			rows,
			columns=["visitors_a", "conversions_a", "visitors_b", "conversions_b"],
		)

	return _factory


@pytest.fixture
def per_user_frame_factory() -> Callable[[list[tuple[str, int]]], pd.DataFrame]:
	"""Create per-user frames for data-loader tests."""

	def _factory(rows: list[tuple[str, int]]) -> pd.DataFrame:
		return pd.DataFrame(rows, columns=["variant", "converted"])

	return _factory


@pytest.fixture
def load_data_csv_factory(monkeypatch: pytest.MonkeyPatch) -> Callable[[pd.DataFrame], ExperimentInput]:
	"""Route DataFrame inputs through the loader without touching disk."""

	def _factory(frame: pd.DataFrame) -> ExperimentInput:
		monkeypatch.setattr("ab_testing_framework.data_loader.pd.read_csv", lambda *_args, **_kwargs: frame)
		return load_data("ignored.csv")

	return _factory
