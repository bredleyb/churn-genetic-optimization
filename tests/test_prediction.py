"""Verificações da demonstração de previsão para novos clientes."""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from joblib import dump

from scripts.predict import run
from src.data import normalize_dataset, split_dataset
from src.model import build_classifier
from src.prediction import predict_customer, prepare_customer

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


@pytest.fixture
def customer():
    return json.loads((EXAMPLES / "cliente_exemplo.json").read_text(encoding="utf-8"))


@pytest.fixture
def model_files(tmp_path, sample_raw_data):
    data = normalize_dataset(sample_raw_data)
    x_train, _, y_train, _ = split_dataset(data)
    baseline = build_classifier()
    genetic = build_classifier(["tenure", "Contract", "InternetService"])
    baseline.fit(x_train, y_train)
    genetic.fit(x_train, y_train)
    dump(baseline, tmp_path / "baseline.joblib")
    dump(genetic, tmp_path / "genetic.joblib")
    return tmp_path, baseline, genetic


def test_examples_have_all_features_and_valid_types():
    for file in EXAMPLES.glob("*.json"):
        frame = prepare_customer(json.loads(file.read_text(encoding="utf-8")))
        assert frame.shape == (1, 19)
        assert frame["SeniorCitizen"].iloc[0] in ("0", "1")


def test_prediction_reuses_saved_pipelines(customer, model_files):
    output, baseline, genetic = model_files
    predictions = run(EXAMPLES / "cliente_exemplo.json", output, "ambos")
    assert set(predictions) == {"baseline", "genetico"}
    frame = prepare_customer(customer)
    for key, model in (("baseline", baseline), ("genetico", genetic)):
        result = predictions[key]
        assert result["classe"] in (0, 1)
        assert result["previsao"] in ("Permanência", "Cancelamento")
        assert 0 <= result["probabilidade_cancelamento"] <= 1
        assert result["probabilidade_cancelamento"] == pytest.approx(
            float(model.predict_proba(frame)[0, list(model.classes_).index(1)])
        )
    assert set(run(EXAMPLES / "cliente_exemplo.json", output, "genetico")) == {"genetico"}


def test_missing_extra_and_bad_values_are_rejected(customer):
    missing = dict(customer)
    missing.pop("Contract")
    with pytest.raises(ValueError, match="Características ausentes: Contract"):
        prepare_customer(missing)
    unexpected = dict(customer, customerID="0000-TESTE")
    with pytest.raises(ValueError, match="Características desconhecidas: customerID"):
        prepare_customer(unexpected)
    for name, value in (
        ("Contract", "Plano anual"),
        ("OnlineSecurity", ""),
        ("tenure", -1),
        ("tenure", 1.5),
        ("MonthlyCharges", True),
        ("MonthlyCharges", float("inf")),
        ("TotalCharges", "286.5"),
        ("SeniorCitizen", 2),
    ):
        invalid = dict(customer, **{name: value})
        with pytest.raises(ValueError):
            prepare_customer(invalid)


def test_services_must_be_consistent(customer):
    for changes in (
        {"PhoneService": "No"},
        {"InternetService": "No"},
        {"OnlineBackup": "No internet service"},
    ):
        with pytest.raises(ValueError, match="incompatível|No phone service"):
            prepare_customer(dict(customer, **changes))


def test_null_totalcharges_can_be_imputed(customer, model_files):
    _, model, _ = model_files
    customer["TotalCharges"] = None
    frame = prepare_customer(customer)
    assert np.isnan(frame["TotalCharges"].iloc[0])
    assert 0 <= predict_customer(model, customer)["probabilidade_cancelamento"] <= 1


def test_cli_outputs_readable_result(tmp_path, customer, model_files):
    models, _, _ = model_files
    file = tmp_path / "cliente.json"
    file.write_text(json.dumps(customer), encoding="utf-8")
    process = subprocess.run(
        [sys.executable, "-m", "scripts.predict", "--cliente", str(file),
         "--resultados", str(models), "--modelo", "ambos"],
        capture_output=True, text=True, check=True,
    )
    assert "Regressão logística de referência" in process.stdout
    assert "Regressão logística com seleção genética" in process.stdout
    assert process.stdout.count("Probabilidade estimada de cancelamento:") == 2
    assert "Previsão:" in process.stdout


def test_clear_errors_for_missing_model_or_bad_json(tmp_path, customer):
    file = tmp_path / "cliente.json"
    file.write_text(json.dumps(customer), encoding="utf-8")
    with pytest.raises(ValueError, match="Modelo não encontrado"):
        run(file, tmp_path, "ambos")
    file.write_text("{broken", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON inválido"):
        run(file, tmp_path, "ambos")
    with pytest.raises(ValueError, match="não encontrado"):
        run(tmp_path / "nao_existe.json", tmp_path, "baseline")
