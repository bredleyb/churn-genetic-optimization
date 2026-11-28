"""Validação agregada de todas as características e recuperação do formulário."""
from pathlib import Path

from src.ui_data import form_errors, load_profile, model_input
from src.prediction import prepare_customer

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_aggregated_errors_include_hidden_fields():
    form = load_profile(ROOT, "Exemplo 1")
    form.update(MonthlyCharges=-10, PaymentMethod="inválido", StreamingTV="inválido")
    errors = form_errors(form)
    assert set(errors) == {"MonthlyCharges", "PaymentMethod", "StreamingTV"}
    with pytest.raises(ValueError):
        model_input(form)


def test_ui_limit_does_not_change_cli_domain():
    form = load_profile(ROOT, "Exemplo 1")
    form["tenure"] = 1000
    assert "tenure" in form_errors(form)
    assert prepare_customer(model_input(form))["tenure"].iloc[0] == 1000


def test_hidden_total_value_is_ignored_when_unavailable():
    form = load_profile(ROOT, "Exemplo 1")
    form.update(total_missing=True, TotalCharges=-100)
    assert form_errors(form) == {}
    assert model_input(form)["TotalCharges"] is None


def test_dependency_errors_are_aggregated():
    form = load_profile(ROOT, "Exemplo 1")
    form.update(PhoneService="No", MultipleLines="Yes",
                InternetService="No", OnlineBackup="Yes", StreamingTV="Yes")
    assert {"MultipleLines", "OnlineBackup", "StreamingTV"} <= set(form_errors(form))


def test_invalid_hidden_field_disables_cta_and_recovers(client_app, monkeypatch):
    app, ui = client_app
    monkeypatch.setattr(app, "DATASET", Path(__file__))
    app.main()
    original = ui.session_state["field_PaymentMethod"]
    ui.session_state["field_PaymentMethod"] = "inválido"
    app._remember_field("PaymentMethod")
    ui.reset_render()
    app.main()
    assert ui.button_options("Calcular previsão")["disabled"] is True
    assert app._current_customer() is None
    feedback = next(text for text in ui.markup if "Método de pagamento (Conta)" in text)
    assert 'data-n3-error-label="Método de pagamento"' in feedback
    assert 'data-n3-error-tab="Conta"' in feedback
    assert 'class="n3-validation-jump"' in feedback
    assert 'id="n3-validation-PaymentMethod"' in feedback
    ui.session_state["field_PaymentMethod"] = original
    app._remember_field("PaymentMethod")
    ui.reset_render()
    app.main()
    assert ui.button_options("Calcular previsão")["disabled"] is False
    assert app._current_customer() is not None


def test_missing_csv_is_retryable(client_app, monkeypatch, tmp_path):
    app, ui = client_app
    monkeypatch.setattr(app, "DATASET", tmp_path / "missing.csv")
    app.main()
    app._request_prediction()
    ui.reset_render()
    app.main()
    assert ui.session_state["prediction_running"] is False
    assert ui.session_state["workflow_attempt"]["phase"] == "failed"
    assert "CSV não encontrado" in ui.session_state["prediction_error"]
    ui.reset_render()
    app.main()
    assert ui.button_options("Tentar novamente")["disabled"] is False
