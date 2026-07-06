"""Session state management for the Split Testing Suite dashboard.

Responsibilities
----------------
- Persist the last-used input values across reruns so the form doesn't reset.
- Maintain a capped history of experiment runs for comparison and undo.
- Provide a stable label for each history entry (timestamp + short description).

History schema (each entry is a dict)
--------------------------------------
{
    "label":         str,   # e.g. "14:32:05 — Control 4.50% → Treatment 5.20%"
    "visitors_a":    int,
    "conversions_a": int,
    "visitors_b":    int,
    "conversions_b": int,
    "alpha":         float,
    "alternative":   str,
    "result":        AbTestResult,
}
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import streamlit as st

from dashboard.config import DEFAULTS

if TYPE_CHECKING:
    from ab_testing_framework.analysis import AbTestResult

_HISTORY_KEY = "experiment_history"
_MAX_HISTORY = 10


def init_state() -> None:
    """Initialise all session state keys with sensible defaults."""
    defaults = {
        "theme":               "dark",
        _HISTORY_KEY:          [],
        "last_visitors_a":     DEFAULTS["visitors_a"],
        "last_conversions_a":  DEFAULTS["conversions_a"],
        "last_visitors_b":     DEFAULTS["visitors_b"],
        "last_conversions_b":  DEFAULTS["conversions_b"],
        "last_alpha":          0.05,
        "last_alternative":    "two-sided",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def save_inputs(
    visitors_a: int,
    conversions_a: int,
    visitors_b: int,
    conversions_b: int,
    alpha: float,
    alternative: str,
) -> None:
    """Persist the current input values so they survive reruns."""
    st.session_state["last_visitors_a"]    = visitors_a
    st.session_state["last_conversions_a"] = conversions_a
    st.session_state["last_visitors_b"]    = visitors_b
    st.session_state["last_conversions_b"] = conversions_b
    st.session_state["last_alpha"]         = alpha
    st.session_state["last_alternative"]   = alternative


def push_history(
    visitors_a: int,
    conversions_a: int,
    visitors_b: int,
    conversions_b: int,
    alpha: float,
    alternative: str,
    result: "AbTestResult",
) -> None:
    """Add a run to the history list, evicting the oldest if at capacity."""
    history: list[dict] = st.session_state[_HISTORY_KEY]

    rate_a = result.metrics.conversion_rate_a
    rate_b = result.metrics.conversion_rate_b
    ts     = datetime.now().strftime("%H:%M:%S")
    label  = f"{ts}  —  Control {rate_a:.2%} → Treatment {rate_b:.2%}"

    entry = {
        "label":         label,
        "visitors_a":    visitors_a,
        "conversions_a": conversions_a,
        "visitors_b":    visitors_b,
        "conversions_b": conversions_b,
        "alpha":         alpha,
        "alternative":   alternative,
        "result":        result,
    }

    history.append(entry)
    if len(history) > _MAX_HISTORY:
        history.pop(0)   # evict oldest

    st.session_state[_HISTORY_KEY] = history


def undo_last() -> None:
    """Remove the most recent history entry."""
    history: list[dict] = st.session_state.get(_HISTORY_KEY, [])
    if history:
        history.pop()
    st.session_state[_HISTORY_KEY] = history


def get_history() -> list[dict]:
    return st.session_state.get(_HISTORY_KEY, [])


def clear_history() -> None:
    st.session_state[_HISTORY_KEY] = []
