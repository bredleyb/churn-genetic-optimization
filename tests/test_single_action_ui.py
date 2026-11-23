"""Verifica a composição do dashboard sem depender de navegador ou Streamlit instalado."""

import importlib.util
import sys
from contextlib import nullcontext
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


class DummySlot:
    def empty(self):
        pass

    def markdown(self, *_args, **_kwargs):
        pass

    def progress(self, *_args, **_kwargs):
        pass

    def error(self, *_args, **_kwargs):
        pass

    def download_button(self, *_args, **_kwargs):
        pass


class DummyUI(ModuleType):
    def __init__(self, clicked: bool):
        super().__init__("streamlit")
        self.session_state = {}
        self.clicked = clicked
        self.clicked_label = None
        self.rerun_count = 0
        self.buttons = []
        self.button_options = []
        self.panel_keys = []
        self.panel_settings = []
        self.styled_markup = []
        self.selectbox_labels = []
        self.number_inputs = []
        self.component_specs = []
        self.component_values = {}
        self.components = SimpleNamespace(v2=SimpleNamespace(component=self._component))
        self.tab_groups = []

    def set_page_config(self, **kwargs):
        pass

    def rerun(self):
        self.rerun_count += 1

    def markdown(self, html, **_kwargs):
        self.styled_markup.append(html)

    def empty(self):
        return DummySlot()

    def container(self, **kwargs):
        self.panel_keys.append(kwargs.get("key"))
        self.panel_settings.append(kwargs)
        return nullcontext()

    def columns(self, spec, **kwargs):
        count = spec if isinstance(spec, int) else len(spec)
        return tuple(nullcontext() for _ in range(count))

    def tabs(self, names, **kwargs):
        self.tab_groups.append(list(names))
        return tuple(nullcontext() for _ in names)

    def selectbox(self, name, options, *, key, **kwargs):
        self.selectbox_labels.append(name)
        self.session_state.setdefault(key, options[0])
        return self.session_state[key]

    def segmented_control(self, label, options, *, key, default, **kwargs):
        self.session_state.setdefault(key, default)
        return self.session_state[key]

    def _component(self, name, **options):
        self.component_specs.append({"name": name, **options})
        def mount(*, key, data=None, default=None, on_value_change=None):
            self.component_specs.append({
                "key": key, "data": data, "default": default,
                "on_value_change": on_value_change,
            })
            fallback = default.get("value") if isinstance(default, dict) else None
            return SimpleNamespace(value=self.component_values.get(key, fallback))
        return mount

    def text_input(self, label, *, key, **kwargs):
        return self.session_state[key]

    def number_input(self, label, *, key, **kwargs):
        self.number_inputs.append({"label": label, "key": key, **kwargs})
        return self.session_state[key]

    def checkbox(self, label, *, key, **kwargs):
        return self.session_state[key]

    def button(self, label, **kwargs):
        self.buttons.append(label)
        self.button_options.append((label, kwargs))
        clicked = not kwargs.get("disabled", False) and (
            (self.clicked and label in ("Calcular previsão", "Recalcular previsão"))
            or label == self.clicked_label
        )
        if clicked and kwargs.get("on_click"):
            kwargs["on_click"](*kwargs.get("args", ()), **kwargs.get("kwargs", {}))
        return clicked

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
    assert any(item.get("name") == "n3_client_scroll_cues" for item in ui.component_specs)
    assert any(item.get("key") == "n3-client-scroll-cues" for item in ui.component_specs)
    # O Streamlit não deve impor min-height em pixels às colunas empilhadas.
    for panel in ui.panel_settings:
        if panel.get("key") in {"dashboard-client", "dashboard-workspace", "dashboard-client-fields"}:
            assert "height" not in panel
    assert ui.buttons == ["1", "2", "+", "Restaurar perfil", "Excluir perfil", "Calcular previsão"]
    options = {name: settings for name, settings in ui.button_options}
    assert options["1"]["type"] == "primary"
    assert options["2"]["type"] == "secondary"
    assert options["+"]["on_click"] is not None
    assert options["Restaurar perfil"]["icon"] == ":material/history:"
    assert options["Restaurar perfil"]["type"] == "tertiary"
    assert options["Restaurar perfil"]["disabled"] is True
    assert callable(options["Restaurar perfil"]["on_click"])
    assert options["Excluir perfil"]["icon"] == ":material/delete_outline:"
    assert options["Excluir perfil"]["disabled"] is True
    assert options["Excluir perfil"]["type"] == "tertiary"
    assert options["Excluir perfil"]["on_click"] == app._delete_active_example
    assert options["Calcular previsão"]["on_click"] == app._request_prediction
    assert options["Calcular previsão"]["key"] == "run_prediction"
    assert options["Calcular previsão"]["disabled"] is False
    assert ui.rerun_count == int(clicked)
    assert "Características" not in ui.selectbox_labels
    assert "Editar características" not in ui.selectbox_labels
    assert ["Perfil", "Conta", "Serviços", "Extras"] in ui.tab_groups
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
    assert '@import url("https://fonts.googleapis.com' not in style
    assert "app/static/FamiljenGrotesk-Variable.ttf" in (ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    assert '--n3-font-ui:"Familjen Grotesk","Segoe UI",Arial,sans-serif' in style
    assert ".stApp [data-testid=\"stWidgetLabel\"]" in style
    assert ".stApp .churn-console-lines" in style
    assert "--n3-page-pad:12px; --n3-panel-pad:12px" in style
    assert "--n3-page-pad:10px;--n3-panel-pad:10px" in style
    assert "--n3-page-pad:8px;--n3-panel-pad:8px" in style
    assert "padding:var(--n3-page-pad)!important" in style
    assert "top:var(--n3-page-pad)!important;right:var(--n3-page-pad)!important" in style
    assert "bottom:var(--n3-page-pad)!important;left:var(--n3-page-pad)!important" in style
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
    assert "churn-workspace-heading" in style
    assert "grid-template-rows:20px minmax(0,1fr) auto" in style
    assert "grid-template-rows:20px auto minmax(0,1fr)" in style
    assert "color:var(--n3-outline)!important" in style
    assert "text-align:center!important" in style
    assert ".churn-panel-heading::before" not in style
    assert ".churn-panel-heading::after" not in style
    assert "gap:var(--n3-panel-pad)!important" in style
    assert "padding:var(--n3-panel-pad)!important" in style
    assert "position:absolute;right:0;top:0" in style
    assert ".churn-run-check {\n  border:2px" in style
    assert "st-key-dashboard-restore-action" in style
    assert "border-top:0!important" in style
    assert ".st-key-dashboard-client-footer button:disabled" in style
    assert 'button:hover:not(:disabled):not([data-n3-hover-ready="false"])' in style
    assert 'background:var(--n3-outline)!important' in style
    assert '@keyframes n3-calculating-ellipsis' in style
    assert 'data-n3-prediction-state="running"' in style
    assert 'animation:n3-calculating-ellipsis 1.35s' in style
    assert 'prefers-reduced-motion:reduce' in style
    assert 'button[kind="primary"]:disabled' in style
    assert "font-size:var(--n3-field-text-size)!important" in style
    assert "font-size:inherit!important" in style
    assert 'font-size:16px!important;font-weight:600!important;' not in style
    assert "st-key-dashboard-profile-choices" in style
    assert "st-key-dashboard-profile-actions" in style
    assert "st-key-dashboard-delete-action" not in style
    assert "border-radius:50%!important" in style
    assert "border-radius:var(--n3-field-radius)!important" in style
    assert "--n3-profile-button-gap" in style
    assert "button:disabled" in style
    assert "QUICK_FIELD_COLUMNS" not in style
    assert 'icon=":material/restart_alt:"' not in style
    assert "churn-run-spinner" in style
    assert "churn-run-check" in style
    assert "--n3-client-content-inset:10px" in style
    assert ".st-key-dashboard-client-fields,\n.st-key-dashboard-client-footer {" in style
    assert style.count("scrollbar-gutter:stable both-edges!important") == 1
    assert style.count("padding-inline:var(--n3-client-content-inset)!important") == 1
    assert "padding-inline-end:10px!important" not in style
    assert ".st-key-dashboard-client-footer {\n  position:relative!important;height:auto!important;\n  overflow:hidden!important;scrollbar-width:thin!important;" in style
    assert ".st-key-dashboard-client-footer::before {" not in style
    assert 'stLayoutWrapper"]:has(.st-key-dashboard-client-footer)::before' in style
    assert "outline-offset:-4px!important" in style
    assert "--n3-client-shadow-length:52px" in style
    assert "--n3-client-shadow-strong:rgba(0,0,0,.48)" in style
    assert "--n3-client-shadow-soft:rgba(0,0,0,.20)" in style
    assert "height:var(--n3-client-shadow-length)" in style
    assert style.count("var(--n3-client-shadow-strong)") == 2
    assert style.count("var(--n3-client-shadow-soft)") == 2
    assert ".st-key-dashboard-client-fields)::before" in style
    assert "--n3-profile-button-size:32px" in style
    assert "--n3-profile-button-size:28px" in style
    assert "--n3-profile-button-size:26px" in style
    assert "border-radius:50%!important" in style
    assert "width:42px!important;min-width:42px!important" not in style
    assert "--n3-client-shadow-top:0; --n3-client-shadow-bottom:0" in style
    assert "opacity:var(--n3-client-shadow-top,0)" in style
    assert "opacity:var(--n3-client-shadow-bottom,0)" in style
    assert "pointer-events:none" in style
    assert '[role="tab"][data-focus-visible]' in style
    assert 'box-shadow:inset 0 -2px 0 var(--n3-outline)' in style
    assert '[data-baseweb="tab-list"]' not in style
    assert "--n3-field-height:42px" in style
    assert "--n3-field-radius:4px" in style
    assert "--n3-field-fill:#0E1013" in style
    assert "--n3-field-action-fill:#0E1013" in style
    assert "--n3-field-text-size:14px" in style
    assert "--n3-field-text-shift:-1px" in style
    assert "transform:translateY(var(--n3-field-text-shift))!important" in style
    assert "position:absolute!important;left:50%!important;top:50%!important" in style
    assert "background:var(--n3-field-fill)!important" in style
    assert "background:var(--n3-field-action-fill)!important" in style
    assert '[data-testid="stSelectbox"] [role="group"]' in style
    assert '[data-testid="stSelectbox"] input[role="combobox"]' in style
    assert '[data-testid="stSelectbox"] button[aria-label="Open"]:hover' in style
    assert 'background:var(--n3-elevated)!important' in style
    assert '[data-baseweb="select"]' not in style
    assert "color:var(--n3-secondary)!important" in style
    assert "transform:translate(-50%,-50%)!important" in style
    assert "height:calc(var(--n3-field-height) - 2px)!important" in style
    assert "st-key-dashboard-tenure-control" in style
    assert 'st-key-dashboard-client [data-testid="stNumberInput"] button' in style
    assert "line-height:var(--n3-field-text-line)!important" in style
    assert "churn-tenure-label" not in style
    assert "font-size:13px!important;padding:7px 3px!important;" in style
    assert "border:2px solid var(--n3-text);border-radius:50%" in style
    assert ".st-key-dashboard-detail-tabs [role=\"tab\"]" in style
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


def test_streamlit_theme_declares_familjen_font():
    """Fonte oficial e licença ficam disponíveis mesmo sem conexão."""
    import tomllib

    config_path = ROOT / ".streamlit" / "config.toml"
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    assert config["server"]["enableStaticServing"] is True
    face = config["theme"]["fontFaces"][0]
    assert face["family"] == "Familjen Grotesk"
    assert face["url"] == "app/static/FamiljenGrotesk-Variable.ttf"
    assert config["theme"]["font"] == "'Familjen Grotesk', sans-serif"
    assert (ROOT / "static" / "FamiljenGrotesk-Variable.ttf").stat().st_size > 10000
    assert "SIL OPEN FONT LICENSE" in (ROOT / "static" / "OFL.txt").read_text(encoding="utf-8")


def test_client_tabs_cover_each_extra_feature_once(monkeypatch):
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_dashboard_tabs_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)

    from src.data import FEATURE_COLUMNS
    from src.ui_data import QUICK_FEATURES

    features = [feature for group in app.DETAIL_TABS.values() for feature in group]
    assert len(features) == len(set(features)) == 15
    assert set(features).isdisjoint(QUICK_FEATURES)
    assert set(features).union(QUICK_FEATURES) == set(FEATURE_COLUMNS)
    assert app.DETAIL_TABS["Extras"] == (
        "TechSupport", "StreamingTV", "StreamingMovies",
    )


def test_prediction_heading_has_three_visible_states(monkeypatch):
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_dashboard_header_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)

    class Capture:
        def __init__(self):
            self.content = ""
        def markdown(self, content, **kwargs):
            self.content = content

    slot = Capture()
    app._render_workspace_heading("idle", slot=slot)
    assert 'role="heading" aria-level="2">Previsão</div>' in slot.content
    assert "<h2" not in slot.content
    assert "churn-run-icon" not in slot.content
    assert "Pronto" not in slot.content

    app._render_workspace_heading("running", slot=slot)
    assert "churn-run-spinner" in slot.content
    assert 'aria-label="Executando previsão"' in slot.content

    app._render_workspace_heading("complete", slot=slot)
    assert "churn-run-check" in slot.content
    assert 'aria-label="Previsão concluída"' in slot.content

    app._render_workspace_heading("stale", slot=slot)
    assert "churn-run-check" not in slot.content


def test_idle_comparison_has_no_redundant_heading_or_ready_status(monkeypatch):
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_dashboard_idle_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)

    class Capture:
        def __init__(self):
            self.content = ""
        def markdown(self, content, **kwargs):
            self.content = content

    slot = Capture()
    app._render_prediction_comparison(None, "idle", slot=slot)
    assert "Previsão do cliente" not in slot.content
    assert "Pronto" not in slot.content
    assert "churn-state" not in slot.content
    assert "Referência" in slot.content
    assert "Seleção genética" in slot.content


def test_tenure_component_protects_unit_and_preserves_monthly_widget(monkeypatch):
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_tenure_component_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    app.main()
    assert ui.component_specs[0]["name"] == "n3_tenure_control"
    assert 'type="text"' in ui.component_specs[0]["html"]
    assert 'aria-label="Tempo como cliente"' in ui.component_specs[0]["html"]
    assert "beforeinput" in ui.component_specs[0]["js"]
    assert "setStateValue" in ui.component_specs[0]["js"]
    assert ui.component_specs[1]["key"] == "n3-tenure-1"
    assert ui.component_specs[1]["default"] == {"value": 3}
    inputs = {item["key"]: item for item in ui.number_inputs}
    assert "field_tenure" not in inputs
    assert inputs["field_MonthlyCharges"]["format"] == "%.2f"
    assert ui.session_state["field_tenure"] == 3


def test_time_change_and_profile_reset_preserve_state(monkeypatch):
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_native_time_state_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    app._apply_profile("Exemplo 1")
    original = app._current_customer()
    ui.session_state["field_tenure"] = 24
    app._remember_field("tenure")
    assert ui.session_state["customer_values"]["tenure"] == 24
    assert app._is_stale({"customer": original})
    previous_revision = ui.session_state["tenure_revision"]
    app._apply_profile("Exemplo 2")
    assert ui.session_state["tenure_revision"] == previous_revision + 1
    assert ui.session_state["field_tenure"] == app.load_profile(ROOT, "Exemplo 2")["tenure"]


def test_tenure_component_updates_customer_without_exposing_suffix(monkeypatch):
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_tenure_component_state_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    monkeypatch.setattr(app, "DATASET", Path(__file__))
    ui.component_values["n3-tenure-1"] = 24
    app.main()
    assert ui.session_state["field_tenure"] == 24
    assert ui.session_state["customer_values"]["tenure"] == 24
    assert ui.session_state["tenure_revision"] == 1


def test_tenure_component_callback_updates_state_before_rerun(monkeypatch):
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_tenure_callback_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    app._apply_profile("Exemplo 1")
    ui.session_state["n3-tenure-1"] = {"value": 42}
    app._on_tenure_component_change()
    assert ui.session_state["field_tenure"] == 42
    assert ui.session_state["customer_values"]["tenure"] == 42
    # Também é seguro receber uma notificação sem estado inicializado.
    ui.session_state["n3-tenure-1"] = {}
    app._on_tenure_component_change()
    assert ui.session_state["field_tenure"] == 42


def test_tenure_css_matches_shared_field_tokens():
    from src.tenure_control import _COMPONENT_CSS
    assert "var(--n3-field-fill,#0e1013)" in _COMPONENT_CSS
    assert "var(--n3-field-action-fill,#0e1013)" in _COMPONENT_CSS
    assert "var(--n3-field-text-size,14px)" in _COMPONENT_CSS
    assert "color:var(--n3-secondary,#d8d8d8)" in _COMPONENT_CSS
    assert "height:var(--n3-field-height,42px)" in _COMPONENT_CSS
    assert "outline:none;border-color:var(--n3-text,#f5f5f5)" in _COMPONENT_CSS
    assert "box-shadow:inset 0 0 0 1px" in _COMPONENT_CSS
    assert "outline-offset:1px" not in _COMPONENT_CSS
    assert "transform:translateY(var(--n3-field-text-shift,-1px))" in _COMPONENT_CSS


def test_protected_tenure_cursor_uses_shadow_dom_focus():
    js = (ROOT / "src" / "tenure_control.mjs").read_text(encoding="utf-8")
    assert "input.getRootNode().activeElement === input" in js
    assert 'input.addEventListener("click", settleCaret' in js
    assert 'input.addEventListener("select"' in js
    assert "requestAnimationFrame(placeCaret)" in js


def test_client_header_has_accessible_role_without_auto_anchor(monkeypatch):
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_heading_role_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    app.main()
    rendered = "\n".join(ui.styled_markup)
    assert '<div class="churn-panel-heading" role="heading" aria-level="2">Cliente</div>' in rendered
    assert '<div class="churn-panel-heading" role="heading" aria-level="2">Previsão</div>' in rendered
    assert '<h2 class="churn-panel-heading">' not in rendered


def test_scroll_cues_component_is_visual_only(monkeypatch):
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_scroll_cues_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    app.main()
    observers = [item for item in ui.component_specs if item.get("name") == "n3_client_scroll_cues"]
    assert len(observers) == 1
    assert "new ResizeObserver" in observers[0]["js"]
    assert "new MutationObserver" in observers[0]["js"]
    assert "scrollCueStrengths(" in observers[0]["js"]
    mount = [item for item in ui.component_specs if item.get("key") == "n3-client-scroll-cues"]
    assert len(mount) == 1
    assert mount[0]["data"] is None
    assert mount[0]["on_value_change"] is None
    assert ui.buttons == ["1", "2", "+", "Restaurar perfil", "Excluir perfil", "Calcular previsão"]


def test_example_selector_preserves_values_across_switches_and_restores(monkeypatch):
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_example_selector_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    app._apply_profile("Exemplo 1")
    assert app._is_profile_pristine()
    initial = ui.session_state["customer_values"]["MonthlyCharges"]
    ui.session_state["field_MonthlyCharges"] = 90.0
    app._remember_field("MonthlyCharges")
    assert not app._is_profile_pristine()

    app._create_example()
    assert ui.session_state["profile_choice"] == "Exemplo 3"
    assert ui.session_state["customer_values"]["MonthlyCharges"] == 90.0
    assert app._is_profile_pristine()
    ui.session_state["field_MonthlyCharges"] = 100.0
    app._remember_field("MonthlyCharges")
    assert not app._is_profile_pristine()
    app._select_example("Exemplo 1")
    assert ui.session_state["customer_values"]["MonthlyCharges"] == 90.0
    app._select_example("Exemplo 3")
    assert ui.session_state["customer_values"]["MonthlyCharges"] == 100.0
    app._reset_profile()
    assert app._is_profile_pristine()
    assert ui.session_state["customer_values"]["MonthlyCharges"] == 90.0
    app._select_example("Exemplo 1")
    app._reset_profile()
    assert ui.session_state["customer_values"]["MonthlyCharges"] == initial
    assert app._is_profile_pristine()


def test_new_examples_stop_at_five_and_hide_creation_button(monkeypatch):
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_example_limit_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    app._apply_profile("Exemplo 1")
    for name in ("Exemplo 3", "Exemplo 4", "Exemplo 5"):
        app._create_example()
        assert ui.session_state["profile_choice"] == name
    assert len(ui.session_state["example_profiles"]) == 5
    with pytest.raises(ValueError, match="Limite de 5"):
        app._create_example()

    ui.buttons.clear()
    ui.button_options.clear()
    app.main()
    assert ui.buttons[:5] == ["1", "2", "3", "4", "5"]
    assert "+" not in ui.buttons
    assert "Restaurar perfil" in ui.buttons
    assert "Excluir perfil" in ui.buttons
    assert "Calcular previsão" in ui.buttons


def test_quick_fields_share_one_grid_specification(monkeypatch):
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_quick_grid_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    assert app.QUICK_FIELD_COLUMNS == (0.55, 0.45)
    app.main()
    from inspect import getsource
    render = getsource(app._render_client_panel)
    assert render.count("st.columns(QUICK_FIELD_COLUMNS") == 2
    assert 'st.selectbox("Perfil de exemplo"' not in render


def test_example_switch_preserves_dependent_service_state(monkeypatch):
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_example_services_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    app._apply_profile("Exemplo 1")
    original = ui.session_state["customer_values"]["InternetService"]
    ui.session_state["field_InternetService"] = "No"
    app._on_service_change("InternetService")
    assert ui.session_state["customer_values"]["InternetService"] == "No"
    assert all(ui.session_state["customer_values"][key] == "No internet service"
               for key in app.INTERNET_FEATURES)
    app._select_example("Exemplo 2")
    app._select_example("Exemplo 1")
    assert ui.session_state["customer_values"]["InternetService"] == "No"
    assert all(ui.session_state["customer_values"][key] == "No internet service"
               for key in app.INTERNET_FEATURES)
    app._reset_profile()
    assert ui.session_state["customer_values"]["InternetService"] == original


def test_legacy_session_migrates_active_example_without_losing_edits(monkeypatch):
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_example_migration_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    values = app.load_profile(ROOT, "Exemplo 1")
    values["tenure"] = 42
    ui.session_state.update({
        "profile_choice": "Exemplo 1", "customer_values": values.copy(),
        "form_initialized": True,
    })
    app._ensure_examples()
    assert ui.session_state["example_profiles"]["Exemplo 1"]["values"]["tenure"] == 42
    assert ui.session_state["example_profiles"]["Exemplo 1"]["original"]["tenure"] == 3
    app._reset_profile()
    assert ui.session_state["customer_values"]["tenure"] == 3


def test_delete_action_only_enabled_for_added_examples(monkeypatch):
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_delete_action_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    app.main()
    assert dict(ui.button_options)["Excluir perfil"]["disabled"] is True
    app._select_example("Exemplo 2")
    ui.button_options.clear()
    app.main()
    assert dict(ui.button_options)["Excluir perfil"]["disabled"] is True
    app._create_example()
    ui.button_options.clear()
    app.main()
    assert dict(ui.button_options)["Excluir perfil"]["disabled"] is False


def test_delete_active_example_preserves_snapshots_and_invalidates_run(monkeypatch):
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_delete_active_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    app._apply_profile("Exemplo 1")
    for _ in range(3):
        app._create_example()
    examples = ui.session_state["example_profiles"]
    saved_original = examples["Exemplo 5"]["original"]
    app._select_example("Exemplo 4")
    # Trocar de perfil sincroniza o rascunho e pode substituir seu dicionário.
    saved_values = examples["Exemplo 5"]["values"]
    ui.session_state["workflow_run"] = {"previous_prediction": True}
    revision = ui.session_state["tenure_revision"]
    assert app._delete_active_example() == "Exemplo 3"
    assert ui.session_state["profile_choice"] == "Exemplo 3"
    assert ui.session_state["workflow_run"] is None
    assert ui.session_state["tenure_revision"] == revision + 1
    assert list(examples) == [f"Exemplo {i}" for i in range(1, 5)]
    assert examples["Exemplo 4"]["original"] is saved_original
    assert examples["Exemplo 4"]["values"] is saved_values
    assert examples["Exemplo 1"]["original"] == app.load_profile(ROOT, "Exemplo 1")
    for base in ("Exemplo 1", "Exemplo 2"):
        app._select_example(base)
        with pytest.raises(ValueError, match="protegido"):
            app._delete_active_example()
    app._select_example("Exemplo 4")
    app._create_example()
    assert ui.session_state["profile_choice"] == "Exemplo 5"


def test_delete_click_is_immediate_without_confirmation(monkeypatch):
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_delete_immediate_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    app._apply_profile("Exemplo 1")
    app._create_example()
    ui.clicked_label = "Excluir perfil"
    app.main()
    assert "Exemplo 3" not in ui.session_state["example_profiles"]
    assert ui.session_state["profile_choice"] == "Exemplo 2"
    assert ui.rerun_count == 0
    assert "Excluir exemplo" not in "\n".join(ui.styled_markup)
    assert not hasattr(app, "_confirm_delete_example")


def test_prediction_button_has_three_states_and_stable_key(monkeypatch):
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_prediction_button_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    monkeypatch.setattr(app, "DATASET", Path(__file__))
    app._apply_profile("Exemplo 1")
    assert app._prediction_button_label() == "Calcular previsão"
    app._request_prediction()
    assert app._prediction_button_label() == "Calculando"
    assert ui.session_state["prediction_requested"]
    ui.button_options.clear()
    ui.buttons.clear()
    calls = []
    monkeypatch.setattr(app, "_execute_full_workflow",
                        lambda customer, slots: calls.append(customer))
    app.main()
    assert len(calls) == 1
    assert "Calculando" in ui.buttons
    assert dict(ui.button_options)["Calculando"]["disabled"] is True
    assert ui.session_state["prediction_running"] is False
    assert ui.rerun_count == 1
    assert ui.session_state.get("prediction_requested") is None

    ui.session_state["workflow_run"] = {"customer": calls[0]}
    assert app._prediction_button_label() == "Recalcular previsão"
    # Um novo clique registra outra execução sem reutilizar o clique anterior.
    app._request_prediction()
    assert app._prediction_button_label() == "Calculando"
    assert ui.session_state["prediction_requested"] is True


def test_recalculate_does_not_reexecute_without_new_click(monkeypatch):
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_recalculate_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    monkeypatch.setattr(app, "DATASET", Path(__file__))
    app._apply_profile("Exemplo 1")
    ui.session_state["form_initialized"] = True
    original = app._current_customer()
    run = {"customer": original, "predictions": {}, "events": []}
    ui.session_state["workflow_run"] = run
    calls = []
    monkeypatch.setattr(app, "_execute_full_workflow", lambda customer, slots: calls.append(customer))
    monkeypatch.setattr(app, "_render_finished_run", lambda run, slots: None)
    app.main()
    assert "Recalcular previsão" in ui.buttons
    assert calls == []
    ui.buttons.clear()
    ui.button_options.clear()
    ui.clicked_label = "Recalcular previsão"
    app.main()
    assert len(calls) == 1
    assert ui.rerun_count == 1


def test_prediction_failure_resets_state_and_renders_error(monkeypatch):
    ui = DummyUI(False)
    monkeypatch.setitem(sys.modules, "streamlit", ui)
    spec = importlib.util.spec_from_file_location("n3_prediction_failure_test", ROOT / "streamlit_app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    monkeypatch.setattr(app, "DATASET", Path(__file__))
    app._request_prediction()
    monkeypatch.setattr(app, "_current_customer", lambda: None)
    app.main()
    assert ui.session_state["prediction_running"] is False
    assert ui.rerun_count == 1
    assert ui.session_state["workflow_run"] is None
    assert "Dados do cliente inválidos" in ui.session_state["prediction_error"]
    assert app._prediction_button_label() == "Calcular previsão"
