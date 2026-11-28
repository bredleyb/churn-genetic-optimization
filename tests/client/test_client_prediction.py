"""Ciclo do botão Calcular/Calculando/Recalcular e estados de previsão."""
from pathlib import Path


def _dataset_available(app, monkeypatch):
    monkeypatch.setattr(app, "DATASET", Path(__file__))


def test_initial_action_and_missing_dataset(client_app, monkeypatch, tmp_path):
    app, ui = client_app
    monkeypatch.setattr(app, "DATASET", tmp_path / "missing.csv")
    app.main()
    assert ui.button_options("Calcular previsão")["disabled"] is False
    assert app._prediction_button_label() == "Calcular previsão"
    assert ui.button_options("Calcular previsão")["key"] == "run_prediction"
    assert ui.button_options("Calcular previsão")["type"] == "primary"
    assert ui.button_options("Calcular previsão")["use_container_width"] is True
    _dataset_available(app, monkeypatch)
    ui.reset_render()
    app.main()
    assert ui.button_options("Calcular previsão")["disabled"] is False


def test_execution_runs_once_and_ends_at_recalculate(client_app, monkeypatch):
    app, ui = client_app
    _dataset_available(app, monkeypatch)
    original = []
    def simulated_run(customer, slots):
        original.append(customer)
        ui.session_state["workflow_run"] = {"customer": customer}
        ui.session_state["prediction_error"] = None

    monkeypatch.setattr(app, "_execute_full_workflow", simulated_run)
    monkeypatch.setattr(app, "_render_finished_run", lambda run, slots: None)
    app.main()
    ui.reset_render()
    ui.click_next = "Calcular previsão"
    app.main()
    assert len(original) == 1
    assert len(original[0]) == 19
    assert ui.reruns == 1
    assert ui.button_options("Calcular previsão")["on_click"] == app._request_prediction
    assert ui.session_state["prediction_running"] is False
    assert "prediction_requested" not in ui.session_state

    ui.reset_render()
    app.main()
    assert app._prediction_button_label() == "Recalcular previsão"
    assert ui.button_options("Recalcular previsão")["disabled"] is False
    assert len(original) == 1
    ui.reset_render()
    ui.click_next = "Recalcular previsão"
    app.main()
    assert len(original) == 2
    assert ui.reruns == 2


def test_running_state_disables_clicks_and_uses_same_button_key(client_app, monkeypatch):
    app, ui = client_app
    _dataset_available(app, monkeypatch)
    app.main()
    app._request_prediction()
    assert app._prediction_button_label() == "Calculando"
    ui.reset_render()
    ui.session_state["prediction_requested"] = False  # inspect rendering only
    app.main()
    button = ui.button_options("Calculando")
    assert button["disabled"] is True
    assert button["key"] == "run_prediction"
    assert button["type"] == "primary"


def test_invalid_client_clears_busy_state_and_reports_error(client_app, monkeypatch):
    app, ui = client_app
    _dataset_available(app, monkeypatch)
    app.main()
    # Defesa contra entrada inválida entre o clique e o processamento.
    app._request_prediction()
    monkeypatch.setattr(app, "_current_customer", lambda: None)
    ui.reset_render()
    app.main()
    assert ui.reruns == 1
    assert ui.session_state["prediction_running"] is False
    assert ui.session_state["workflow_run"] is None
    assert "Dados do cliente inválidos" in ui.session_state["prediction_error"]
    assert app._prediction_button_label() == "Calcular previsão"


def test_changes_mark_completed_run_stale_until_next_calculation(client_app):
    app, ui = client_app
    app._apply_profile("Exemplo 1")
    original = app._current_customer()
    ui.session_state["workflow_run"] = {"customer": original}
    assert app._prediction_button_label() == "Recalcular previsão"
    assert not app._is_stale(ui.session_state["workflow_run"])
    ui.session_state["field_tenure"] += 1
    app._remember_field("tenure")
    assert app._is_stale(ui.session_state["workflow_run"])
    assert app._prediction_button_label() == "Recalcular previsão"
    app._select_example("Exemplo 2")
    assert ui.session_state["workflow_run"] is None
    assert app._prediction_button_label() == "Calcular previsão"


def test_running_indicator_is_independent_from_form_button(client_app):
    app, ui = client_app
    class Slot:
        def __init__(self): self.markup = ""
        def markdown(self, content, **kwargs): self.markup = content
    slot = Slot()
    app._render_workspace_heading("running", slot=slot)
    assert "churn-run-spinner" in slot.markup
    assert "Executando previsão" in slot.markup
    app._render_workspace_heading("complete", slot=slot)
    assert "churn-run-check" in slot.markup
    assert "Previsão concluída" in slot.markup
    app._render_workspace_heading("error", slot=slot)
    assert "Execução interrompida" in slot.markup


def test_client_scroll_observer_is_visual_only(client_app):
    app, ui = client_app
    app.main()
    names = [name for name, _ in ui.component_defs]
    assert names.count("n3_client_scroll_cues") == 1
    opts = next(opts for name, opts in ui.component_defs if name == "n3_client_scroll_cues")
    assert "ResizeObserver" in opts["js"] and "MutationObserver" in opts["js"]
    mount = next(row for row in ui.component_mounts if row[0] == "n3-client-scroll-cues")
    assert mount[1] is None
    assert mount[3] is None


def test_client_execution_lock_is_visual_and_prevents_keyboard_input(client_app):
    app, ui = client_app
    app.main()
    css = ui.markup[0]
    observer = next(opts["js"] for name, opts in ui.component_defs
                    if name == "n3_client_scroll_cues")
    assert '.st-key-dashboard-client[data-n3-interaction-locked="true"]::after' in css
    assert "background:var(--n3-client-shadow-strong)" in css
    assert "z-index:20" in css and "pointer-events:auto" in css
    assert 'next.dataset.n3InteractionLocked = "true"' in observer
    assert "next.inert = true" in observer
    assert "next.inert = false" in observer
    assert 'next.setAttribute("aria-busy", "true")' in observer
    assert 'document.addEventListener("click", onPredictionClick' in observer
    assert 'state === "running" || phase === "running"' in observer
    assert "busy.observedRunning" in observer
    assert "setStateValue(" not in observer
