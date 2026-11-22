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


    def download_button(self, *_args, **_kwargs):
        pass


class DummyUI(ModuleType):
    def __init__(self, clicked: bool):
        super().__init__("streamlit")
        self.session_state = {}
        self.clicked = clicked
        self.buttons = []
        self.panel_keys = []
        self.panel_settings = []
        self.styled_markup = []
        self.selectbox_labels = []

    def set_page_config(self, **kwargs):
        pass

    def markdown(self, html, **_kwargs):
        self.styled_markup.append(html)

    def empty(self):
        return DummySlot()

    def container(self, **kwargs):
        self.panel_keys.append(kwargs.get("key"))
        self.panel_settings.append(kwargs)
        return nullcontext()

    def columns(self, spec, **kwargs):
        return (nullcontext(), nullcontext())

    def tabs(self, names, **kwargs):
        return tuple(nullcontext() for _ in names)

    def selectbox(self, name, options, *, key, **kwargs):
        self.selectbox_labels.append(name)
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
    # O Streamlit não deve impor min-height em pixels às colunas empilhadas.
    for panel in ui.panel_settings:
        if panel.get("key") in {"dashboard-client", "dashboard-workspace", "dashboard-client-fields"}:
            assert "height" not in panel
    assert ui.buttons == ["Restaurar", "Calcular previsão"]
    assert "Características" in ui.selectbox_labels
    assert "Editar características" not in ui.selectbox_labels
    assert not any("churn-topbar" in markup for markup in ui.styled_markup)
    assert not any("Outras características" in markup for markup in ui.styled_markup)
    assert len(executed) == int(clicked)
    if clicked:
        assert len(executed[0]) == 19


def test_css_is_monochrome_and_scoped_to_viewport(monkeypatch):
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_dashboard_css_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    style = ui.styled_markup[0]
    assert "100dvh" in style
    assert "overflow:hidden" in style
    assert "--n3-bg:#000000" in style
    assert "family=Familjen+Grotesk" in style
    assert '--n3-font-ui:"Familjen Grotesk","Segoe UI",Arial,sans-serif' in style
    assert ".stApp [data-testid=\"stWidgetLabel\"]" in style
    assert ".stApp .churn-console-lines" in style
    assert "top:12px!important;right:18px!important;bottom:10px!important" in style
    assert "top:9px!important;right:10px!important;bottom:8px!important" in style
    assert "top:8px!important;right:8px!important;bottom:8px!important" in style
    assert "churn-topbar" not in style
    assert "churn-chart-descriptor" not in style
    assert "stMarkdownContainer\"]:has(.churn-monitor-title)" in style
    assert "--n3-positive:#5FE29A" in style
    assert "--n3-negative:#FF6464" in style
    assert "grid-template-rows:minmax(0,36fr) minmax(0,64fr)" in style
    assert "position:fixed!important" in style
    assert '> [data-testid="stColumn"] > [data-testid="stVerticalBlock"]' in style
    assert ".st-key-dashboard-mobile-detail" in style
    assert ".st-key-dashboard-desktop-detail" in style
    assert "#30B6A7" not in style
    assert "Painel técnico desktop: a área do console absorve o espaço restante" in style
    assert "Em desktop, a faixa inferior reúne as características e o monitor" in style
    assert "grid-template-rows:minmax(0,1fr) minmax(184px,24dvh)" in style
    assert '[data-testid="stMarkdownContainer"]:has(.churn-chromosome)' in style
    assert '[data-testid="stMarkdownContainer"]:has(.churn-technical)' in style


def test_results_use_semantic_classification_only(monkeypatch):
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_dashboard_result_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    class Capture:
        def __init__(self): self.content = ""
        def markdown(self, content, **kwargs): self.content = content
    slot = Capture()
    run = {"summary": {"genetic_count": 9}, "predictions": {
        "baseline": {"classe": 1,"probabilidade_cancelamento": 0.8204},
        "genetico": {"classe": 0,"probabilidade_cancelamento": 0.0037},
    }}
    app._render_prediction_comparison(run, "complete", slot=slot)
    assert "82,04%" in slot.content
    assert "0,37%" in slot.content
    assert 'is-negative">Cancelamento' in slot.content
    assert 'is-positive">Permanência' in slot.content
    assert "churn-kpi" not in slot.content


def test_chart_starts_y_axis_at_zero_and_uses_white_line(monkeypatch):
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_dashboard_chart_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    class Capture:
        def __init__(self): self.content = ""
        def markdown(self, content, **kwargs): self.content = content
    slot = Capture()
    app._history_chart([{"geracao":i,"melhor_f1_cv":.60+i/1000} for i in range(1,16)], slot=slot)
    assert "0,0" in slot.content
    assert "0,8" in slot.content
    assert "F1-score" in slot.content
    assert "<polyline" in slot.content
    assert "churn-chart-line" in slot.content
    assert "Validação cruzada · 15 gerações" not in slot.content


def test_console_shows_recent_events_first(monkeypatch):
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_dashboard_log_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    class Capture:
        def __init__(self): self.content = ""
        def markdown(self, content, **kwargs): self.content = content
    slot = Capture()
    app._render_console(["[INÍCIO] Teste", "[GERAÇÃO] 14", "[FIM] concluído"], slot=slot, complete=True)
    assert slot.content.index("[FIM]") < slot.content.index("[GERAÇÃO]")


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



def test_stale_result_uses_one_message_and_preserves_test_metrics(monkeypatch):
    """Editar cliente mantém o F1 anterior e informa o estado só na comparação."""
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_stale_summary_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)

    class Capture:
        def __init__(self):
            self.content = ""

        def markdown(self, content, **kwargs):
            self.content = content

    run = {
        "summary": {
            "genetic_count": 9,
            "baseline": {"f1": 0.6040},
            "genetico": {"f1": 0.5869},
            "reduction_pct": 52.6,
            "test_count": 1409,
        },
        "evaluated_subsets": 121,
        "predictions": {
            "baseline": {"classe": 1, "probabilidade_cancelamento": 0.8204},
            "genetico": {"classe": 1, "probabilidade_cancelamento": 0.7666},
        },
    }
    comparison, technical = Capture(), Capture()
    app._render_prediction_comparison(run, "stale", slot=comparison)
    app._render_technical(run, slot=technical)

    assert "Dados alterados" in comparison.content
    assert "82,04%" not in comparison.content
    assert "76,66%" not in comparison.content
    assert "0,6040" in technical.content
    assert "0,5869" in technical.content
    assert "ΔF1" in technical.content
    assert "Dados alterados" not in technical.content
    assert "Os dados do cliente foram alterados" not in technical.content


def test_phone_service_callback_keeps_values_from_hidden_tabs(monkeypatch):
    """A troca de aba remove chaves de widgets; os dados do cliente permanecem."""
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_phone_session_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    app._apply_profile("Exemplo 1")

    original_gender = ui.session_state["field_gender"]
    changed_gender = "Male" if original_gender == "Female" else "Female"
    ui.session_state["field_gender"] = changed_gender
    app._remember_field("gender")

    for feature in app.PROFILE_FEATURES:
        ui.session_state.pop(f"field_{feature}", None)
    ui.session_state["detail_tab"] = "Telefonia"

    ui.session_state["field_PhoneService"] = "No"
    app._on_service_change("PhoneService")
    app._render_client_details()

    assert app._form_data()["gender"] == changed_gender
    assert app._form_data()["PhoneService"] == "No"
    assert app._form_data()["MultipleLines"] == "No phone service"
    assert app._current_customer()["MultipleLines"] == "No phone service"

    ui.session_state["field_PhoneService"] = "Yes"
    app._on_service_change("PhoneService")
    assert app._form_data()["MultipleLines"] == "No"
    ui.session_state.pop("field_gender", None)
    app._ensure_widget_field("gender")
    assert ui.session_state["field_gender"] == changed_gender


def test_internet_service_callback_keeps_hidden_fields(monkeypatch):
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_internet_session_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    app._apply_profile("Exemplo 1")

    for name in (*app.PROFILE_FEATURES, *app.INTERNET_FEATURES):
        ui.session_state.pop(f"field_{name}", None)
    ui.session_state["field_InternetService"] = "No"
    app._on_service_change("InternetService")
    assert app._form_data()["InternetService"] == "No"
    assert all(app._form_data()[name] == "No internet service" for name in app.INTERNET_FEATURES)
    assert app._current_customer() is not None

    ui.session_state["field_InternetService"] = "DSL"
    app._on_service_change("InternetService")
    assert all(app._form_data()[name] == "No" for name in app.INTERNET_FEATURES)
    assert app._current_customer() is not None
