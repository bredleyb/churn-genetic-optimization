"""A página oferece uma única ação para iniciar o processamento completo."""

import importlib.util
import sys
from contextlib import nullcontext
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]


class _Grid:
    def cell(self):
        return nullcontext()


class _StreamlitStub(ModuleType):
    def __init__(self, should_calculate):
        super().__init__("streamlit")
        self.session_state = {}
        self.should_calculate = should_calculate
        self.buttons = []

    def set_page_config(self, **kwargs):
        pass

    def markdown(self, *args, **kwargs):
        pass

    def caption(self, *args, **kwargs):
        pass

    def info(self, *args, **kwargs):
        pass

    def container(self, **kwargs):
        return nullcontext()

    def grid(self, *args, **kwargs):
        assert kwargs.get("wrap") is True
        return _Grid()

    def columns(self, *args, **kwargs):
        return nullcontext(), nullcontext()

    def expander(self, *args, **kwargs):
        return nullcontext()

    def selectbox(self, name, options, *, key, **kwargs):
        self.session_state.setdefault(key, options[0])
        return self.session_state[key]

    def number_input(self, name, *, key, **kwargs):
        return self.session_state[key]

    def checkbox(self, name, *, key, **kwargs):
        return self.session_state[key]

    def button(self, name, **kwargs):
        self.buttons.append(name)
        return name == "Calcular previsão" and self.should_calculate


@pytest.mark.parametrize("should_calculate", [False, True])
def test_only_client_button_starts_complete_experiment(monkeypatch, should_calculate):
    stub = _StreamlitStub(should_calculate)
    monkeypatch.setitem(sys.modules, "streamlit", stub)
    spec = importlib.util.spec_from_file_location(
        "streamlit_app_ui_test", ROOT / "streamlit_app.py"
    )
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    monkeypatch.setattr(app, "DATASET", Path(__file__))  # O botão precisa estar habilitado.
    executed = []
    monkeypatch.setattr(app, "_execute_full_workflow", executed.append)

    app.main()

    assert stub.buttons == ["Restaurar exemplo", "Calcular previsão"]
    assert len(executed) == int(should_calculate)
    if should_calculate:
        assert len(executed[0]) == 19
        assert executed[0]["tenure"] == 3
    assert "preview_requested" not in stub.session_state
