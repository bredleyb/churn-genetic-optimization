"""Regressões da tentativa parcial e da separação do último sucesso."""
from pathlib import Path

from src.ui_data import model_input


def test_snapshot_normalizes_equivalent_fields_and_missing_total(client_app):
    app, _ = client_app
    app._apply_profile("Exemplo 1")
    form = app._form_data()
    form["total_missing"] = True
    first = model_input(form)
    form["SeniorCitizen"] = int(form["SeniorCitizen"])
    form["tenure"] = float(form["tenure"])
    form["TotalCharges"] = 999999
    assert model_input(form) == first
    assert first["TotalCharges"] is None
    assert isinstance(first["SeniorCitizen"], str)
    assert isinstance(first["tenure"], int)


def test_failed_attempt_preserves_previous_snapshot_and_releases_lock(client_app, monkeypatch):
    app, ui = client_app
    monkeypatch.setattr(app, "DATASET", Path(__file__))
    app.main()
    snapshot = {"customer": app._current_customer()}
    ui.session_state["workflow_run"] = snapshot

    def fail_read(path):
        raise OSError("detalhe interno privado")

    monkeypatch.setattr(app, "load_dataset", fail_read)
    app._request_prediction()
    ui.reset_render()
    app.main()
    attempt = ui.session_state["workflow_attempt"]
    assert attempt["phase"] == "failed"
    assert attempt["elapsed_seconds"] is None
    assert attempt["chromosome"] is None
    assert attempt["events"][0] == "[EXECUÇÃO] Processamento iniciado."
    assert "detalhe interno privado" not in "\n".join(attempt["events"])
    assert "detalhe interno privado" not in ui.session_state["prediction_error"]
    assert ui.session_state["workflow_run"] is snapshot
    assert ui.session_state["prediction_running"] is False
    assert app._prediction_button_label() == "Tentar novamente"
    ui.reset_render()
    app.main()
    assert ui.button_options("Tentar novamente")["disabled"] is False
    assert ui.session_state["workflow_attempt"] is attempt


def test_failed_search_keeps_observed_candidate_and_generation(client_app, monkeypatch):
    app, ui = client_app
    monkeypatch.setattr(app, "DATASET", Path(__file__))
    monkeypatch.setattr(app, "load_dataset", lambda path: [1, 2, 3])
    monkeypatch.setattr(app, "split_dataset", lambda *args, **kwargs: ([1, 2], [3], [0, 1], [1]))
    monkeypatch.setattr(app, "evaluate_cv", lambda *args, **kwargs: {"f1": {"media": 0.5}})
    chromosome = (1,) + (0,) * 18

    def fail_search(*args, on_evaluation, on_generation, **kwargs):
        event = {"geracao": 1, "individuo": 1, "populacao": 24,
                 "cromossomo": chromosome, "caracteristicas": ("gender",),
                 "dobras": 3, "etapa": "inicio", "avaliados": 0}
        on_evaluation(event)
        on_evaluation({**event, "etapa": "fim", "avaliados": 1,
                       "f1_cv": 0.5, "aptidao": 0.49})
        on_generation({"geracao": 1, "melhor_f1_cv": 0.5,
                       "melhor_aptidao": 0.49, "caracteristicas": 1})
        raise RuntimeError("falha controlada")

    monkeypatch.setattr(app, "select_features", fail_search)
    app.main()
    app._request_prediction()
    ui.reset_render()
    app.main()
    attempt = ui.session_state["workflow_attempt"]
    assert attempt["phase"] == "failed"
    assert attempt["chromosome"] == chromosome
    assert attempt["evaluated_subsets"] == 1
    assert len(attempt["history"]) == 1
    assert attempt["elapsed_seconds"] >= 0
    assert attempt["search_started_at"] is None
    assert ui.session_state["workflow_run"] is None
    assert ui.session_state["prediction_running"] is False
