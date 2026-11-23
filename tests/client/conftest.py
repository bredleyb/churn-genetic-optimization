"""Infraestrutura do contrato de Cliente: Streamlit simulado só para unidades.

Testes de geometria, foco, hover e navegador real são responsabilidade do
Playwright. Esta implementação registra parâmetros e aplica callbacks de botão
na mesma ordem lógica que o Streamlit.
"""
import importlib.util
import sys
from contextlib import nullcontext
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]


class Slot:
    def __init__(self):
        self.markup = []
        self.errors = []

    def markdown(self, value, **kwargs):
        self.markup.append(value)

    def error(self, value, **kwargs):
        self.errors.append(value)

    def progress(self, *args, **kwargs):
        return None

    def download_button(self, *args, **kwargs):
        return False

    def empty(self):
        return Slot()


class StreamlitContract(ModuleType):
    def __init__(self):
        super().__init__("streamlit")
        self.session_state = {}
        self.markup = []
        self.buttons = []
        self.inputs = []
        self.tab_sets = []
        self.containers = []
        self.component_defs = []
        self.component_mounts = []
        self.component_values = {}
        self.click_next = None
        self.reruns = 0
        self.components = SimpleNamespace(
            v2=SimpleNamespace(component=self._component),
        )

    def set_page_config(self, **kwargs):
        self.page_config = kwargs

    def markdown(self, html, **kwargs):
        self.markup.append(html)

    def caption(self, *args, **kwargs):
        pass

    def info(self, *args, **kwargs):
        pass

    def empty(self):
        return Slot()

    def container(self, **kwargs):
        self.containers.append(kwargs)
        return nullcontext()

    def columns(self, spec, **kwargs):
        count = spec if isinstance(spec, int) else len(spec)
        return tuple(nullcontext() for _ in range(count))

    def tabs(self, names, **kwargs):
        self.tab_sets.append(tuple(names))
        return tuple(nullcontext() for _ in names)

    def button(self, text, **kwargs):
        self.buttons.append((text, kwargs))
        clicked = self.click_next == text and not kwargs.get("disabled", False)
        if clicked:
            self.click_next = None
            callback = kwargs.get("on_click")
            if callback:
                callback(*kwargs.get("args", ()), **kwargs.get("kwargs", {}))
        return clicked

    def selectbox(self, label, options, *, key, **kwargs):
        self.inputs.append(("selectbox", label, key, kwargs))
        self.session_state.setdefault(key, options[0])
        return self.session_state[key]

    def number_input(self, label, *, key, **kwargs):
        self.inputs.append(("number_input", label, key, kwargs))
        return self.session_state[key]

    def checkbox(self, label, *, key, **kwargs):
        self.inputs.append(("checkbox", label, key, kwargs))
        return self.session_state[key]

    def _component(self, name, **definition):
        self.component_defs.append((name, definition))

        def render(*, key, data=None, default=None, on_value_change=None):
            self.component_mounts.append((key, data, default, on_value_change))
            value = self.component_values.get(key)
            if value is None:
                value = (default or {}).get("value")
            return SimpleNamespace(value=value)

        return render

    def rerun(self):
        self.reruns += 1

    def button_options(self, text):
        results = [kwargs for label, kwargs in self.buttons if label == text]
        assert len(results) == 1, f"Botão ausente ou duplicado: {text!r}"
        return results[0]

    def reset_render(self):
        self.buttons.clear()
        self.inputs.clear()
        self.tab_sets.clear()
        self.containers.clear()
        self.component_mounts.clear()


@pytest.fixture
def client_app(monkeypatch):
    fake = StreamlitContract()
    monkeypatch.setitem(sys.modules, "streamlit", fake)
    spec = importlib.util.spec_from_file_location(
        "n3_client_contract", ROOT / "streamlit_app.py",
    )
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    return app, fake
