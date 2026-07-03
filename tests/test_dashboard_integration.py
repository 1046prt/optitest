from __future__ import annotations

from io import StringIO
from collections.abc import Callable
from runpy import run_module
from types import ModuleType
import sys

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
        self.warnings: list[str] = []
        self.infos: list[str] = []
        self.captions: list[str] = []
        self.widget_calls: list[tuple[str, dict[str, object]]] = []
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

    def caption(self, text):
        self.captions.append(text)

    def file_uploader(self, *args, **kwargs):
        self.widget_calls.append(("file_uploader", kwargs))
        return None

    def number_input(self, *args, **kwargs):
        self.widget_calls.append(("number_input", kwargs))
        return kwargs.get("value", 0)

    def slider(self, *args, **kwargs):
        self.widget_calls.append(("slider", kwargs))
        return kwargs.get("value", 0.0)

    def selectbox(self, *args, **kwargs):
        self.widget_calls.append(("selectbox", kwargs))
        options = kwargs.get("options", [])
        index = kwargs.get("index", 0)
        return options[index]

    def download_button(self, *args, **kwargs):
        self.widget_calls.append(("download_button", kwargs))
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

    def warning(self, text):
        self.warnings.append(text)

    def info(self, text):
        self.infos.append(text)

    def stop(self):
        raise AssertionError("dashboard requested an early stop")


@pytest.fixture
def fake_streamlit():
    return FakeStreamlit()


def test_dashboard_script_renders_with_default_inputs(monkeypatch, fake_streamlit):
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    run_module("dashboard.app", run_name="__main__")

    assert fake_streamlit.config["page_title"] == "Split Testing Suite"
    assert any("A/B Test Results" in text for text in fake_streamlit.markdowns)
    assert len(fake_streamlit.charts) == 5
    assert fake_streamlit.errors == []
    assert fake_streamlit.buttons == ["Save to reports/"]
    assert any(call[0] == "file_uploader" and call[1].get("help") for call in fake_streamlit.widget_calls)
    assert any(call[0] == "number_input" and call[1].get("help") for call in fake_streamlit.widget_calls)


def test_dashboard_script_uses_uploaded_csv(monkeypatch):
    fake_streamlit = FakeStreamlit()
    fake_streamlit.file_uploader = lambda *args, **kwargs: StringIO(
        "variant,converted\n"
        "A,1\n"
        "A,0\n"
        "B,1\n"
        "B,1\n"
    )
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    run_module("dashboard.app", run_name="__main__")

    assert any(metric["label"] == "Control rate" for metric in fake_streamlit.metrics)
    assert any("A/B Test Results" in text for text in fake_streamlit.markdowns)


def test_dashboard_recovers_from_invalid_csv(monkeypatch):
    fake_streamlit = FakeStreamlit()
    fake_streamlit.file_uploader = lambda *args, **kwargs: StringIO("foo,bar\n1,2\n")
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    run_module("dashboard.app", run_name="__main__")

    assert fake_streamlit.warnings
    assert fake_streamlit.infos
    assert len(fake_streamlit.charts) == 5
    assert any("uploaded CSV" in warning or "Could not use" in warning for warning in fake_streamlit.warnings)


def test_dashboard_helpers_remain_importable():
    from dashboard.app import _lift_class, _pval_badge, _rel_lift_display

    assert "p &lt; 0.05" in _pval_badge(0.04)
    assert _rel_lift_display(None) == "N/A (zero baseline)"
    assert _lift_class(-0.01) == "negative"
