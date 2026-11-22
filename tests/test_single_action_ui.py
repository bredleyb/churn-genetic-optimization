"""Verifica a composição do dashboard sem depender de navegador ou Streamlit instalado."""

import importlib.util
import sys
from contextlib import nullcontext
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]


class DummySlot:
    def markdown(self, *_args, **_kwargs):
        pass

    def progress(self, *_args, **_kwargs):
        pass

    def line_chart(self, *_args, **_kwargs):
        pass

    def download_button(self, *_args, **_kwargs):
        pass


class DummyUI(ModuleType):
    def __init__(self, clicked: bool):
        super().__init__("streamlit")
        self.session_state = {}
        self.clicked = clicked
        self.buttons = []
        self.panel_keys = []
        self.styled_markup = []

    def set_page_config(self, **kwargs):
        pass

    def markdown(self, html, **_kwargs):
        self.styled_markup.append(html)

    def empty(self):
        return DummySlot()

    def container(self, **kwargs):
        self.panel_keys.append(kwargs.get("key"))
        return nullcontext()

    def columns(self, spec, **kwargs):
        return (nullcontext(), nullcontext())

    def selectbox(self, name, options, *, key, **kwargs):
        self.session_state.setdefault(key, options[0])
        return self.session_state[key]

    def segmented_control(self, label, options, *, key, default, **kwargs):
        self.session_state.setdefault(key, default)
        return self.session_state[key]

    def number_input(self, label, *, key, **kwargs):
        return self.session_state[key]

    def checkbox(self, label, *, key, **kwargs):
        return self.session_state[key]

    def button(self, label, **kwargs):
        self.buttons.append(label)
        return self.clicked and label == "Calcular previsão"

    def caption(self, *args, **kwargs):
        pass

    def info(self, *args, **kwargs):
        pass


@pytest.mark.parametrize("clicked", [False, True])
def test_single_button_starts_workflow_from_client_panel(monkeypatch, clicked):
    ui = DummyUI(clicked)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_dashboard_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    monkeypatch.setattr(app, "DATASET", Path(__file__))
    executed = []
    monkeypatch.setattr(app, "_execute_full_workflow", lambda customer, slots: executed.append(customer))

    app.main()

    assert "dashboard-client" in ui.panel_keys
    assert "dashboard-workspace" in ui.panel_keys
    assert "dashboard-client-fields" in ui.panel_keys
    assert "dashboard-client-footer" in ui.panel_keys
    assert ui.buttons == ["Restaurar exemplo", "Calcular previsão"]
    assert len(executed) == int(clicked)
    if clicked:
        assert len(executed[0]) == 19


def test_css_is_dark_and_scoped_to_viewport(monkeypatch):
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_dashboard_css_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    style = ui.styled_markup[0]
    assert "100dvh" in style
    assert "overflow: hidden" in style
    assert "dashboard-client-fields" in style
    assert "dashboard-workspace" in style
    assert "#0B111B" in style


def test_result_is_invalidated_after_customer_changes(monkeypatch):
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_dashboard_state_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    app._apply_profile("Exemplo 1")
    original = app._current_customer()
    run = {"customer": original}
    assert not app._is_stale(run)
    ui.session_state["field_tenure"] = 4
    assert app._is_stale(run)
