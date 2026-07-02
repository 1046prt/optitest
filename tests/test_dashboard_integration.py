from __future__ import annotations

from collections.abc import Callable
from runpy import run_module
from types import ModuleType

import pytest


class _DummyBlock:
    def __init__(self, owner: "FakeStreamlit", name: str = "block") -> None:
        self._owner = owner
        self._name = name

    def __enter__(self):
        self._owner.events.append(("enter", self._name))
        return self

    def __exit__(self, exc_type, exc, tb):
        self._owner.events.append(("exit", self._name))
        return False

    def metric(self, label, value, delta=None, delta_color=None):
        self._owner.metrics.append(
            {
                "label": label,
                "value": value,
                "delta": delta,
                "delta_color": delta_color,
            }
        )


class FakeStreamlit(ModuleType):
    def __init__(self, name: str = "streamlit") -> None:
        super().__init__(name)
        self.events: list[tuple[str, str]] = []
        self.markdowns: list[str] = []
        self.errors: list[str] = []
        self.metrics: list[dict[str, object]] = []
        self.charts: list[object] = []
        self.buttons: list[str] = []
        self.downloads: list[str] = []
        self.config: dict[str, object] = {}
        self.sidebar = _DummyBlock(self, "sidebar")

    def cache_data(self, show_spinner=False):
        def decorator(func):
            return func

        return decorator

    def set_page_config(self, **kwargs):
        self.config.update(kwargs)

    def markdown(self, text, unsafe_allow_html=False):
        self.markdowns.append(text)

    def file_uploader(self, *args, **kwargs):
        return None

    def number_input(self, *args, **kwargs):
        return kwargs.get("value", 0)

    def slider(self, *args, **kwargs):
        return kwargs.get("value", 0.0)

    def selectbox(self, *args, **kwargs):
        options = kwargs.get("options", [])
        index = kwargs.get("index", 0)
        return options[index]

    def download_button(self, *args, **kwargs):
        label = kwargs.get("label") or (args[0] if args else "download")
        self.downloads.append(label)
        return False

    def columns(self, spec):
        if isinstance(spec, int):
            return [_DummyBlock(self, f"column-{index}") for index in range(spec)]
        return [_DummyBlock(self, f"column-{index}") for index, _ in enumerate(spec)]

    def plotly_chart(self, figure, **kwargs):
        self.charts.append(figure)

    def expander(self, label):
        return _DummyBlock(self, f"expander:{label}")

    def code(self, text, language=None):
        self.markdowns.append(text)

    def button(self, label):
        self.buttons.append(label)
        return False

    def success(self, text):
        self.events.append(("success", text))

    def error(self, text):
        self.errors.append(text)

    def stop(self):
        raise AssertionError("dashboard requested an early stop")


@pytest.fixture
def fake_streamlit():
    return FakeStreamlit()


def test_dashboard_script_renders_with_default_inputs(monkeypatch, fake_streamlit):
    monkeypatch.setitem(__import__("sys").modules, "streamlit", fake_streamlit)

    run_module("dashboard.app", run_name="__main__")

    assert fake_streamlit.config["page_title"] == "Split Testing Suite"
    assert any("A/B Test Results" in text for text in fake_streamlit.markdowns)
    assert len(fake_streamlit.charts) == 5
    assert fake_streamlit.errors == []
    assert fake_streamlit.buttons == ["Save to reports/"]


def test_dashboard_helpers_remain_importable():
    from dashboard.app import _lift_class, _pval_badge, _rel_lift_display

    assert "p &lt; 0.05" in _pval_badge(0.04)
    assert _rel_lift_display(None) == "N/A (zero baseline)"
    assert _lift_class(-0.01) == "negative"
