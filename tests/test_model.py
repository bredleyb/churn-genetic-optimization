"""Verificações do classificador e da validação de referência."""

import json
import subprocess
import sys

import numpy as np
import pytest
from joblib import load

from src.data import FEATURE_COLUMNS, normalize_dataset, split_dataset
from src.model import build_classifier, evaluate_cv


def test_baseline_predicts_using_original_features(sample_raw_data):
    data = normalize_dataset(sample_raw_data)
    x_development, x_test, y_development, _ = split_dataset(data)
    model = build_classifier()
    model.fit(x_development, y_development)

    probabilities = model.predict_proba(x_test)
    assert probabilities.shape == (len(x_test), 2)
    assert np.all((probabilities >= 0) & (probabilities <= 1))
    assert np.allclose(probabilities.sum(axis=1), 1.0)
    assert set(model.predict(x_test)).issubset({0, 1})
    assert len(FEATURE_COLUMNS) == 19


def test_classifier_accepts_selected_original_features(sample_raw_data):
    data = normalize_dataset(sample_raw_data)
    x_development, x_test, y_development, _ = split_dataset(data)
    model = build_classifier(["tenure", "Contract"])
    model.fit(x_development, y_development)

    assert model.predict(x_test).shape == (len(x_test),)
    assert len(model.named_steps["preprocessor"].get_feature_names_out()) == 3
    with pytest.raises(ValueError, match="desconhecidas"):
        build_classifier(["customerID"])


def test_cv_returns_reproducible_scores_without_test_data(sample_raw_data):
    data = normalize_dataset(sample_raw_data)
    x_development, x_test, y_development, y_test = split_dataset(data)
    first = evaluate_cv(x_development, y_development)
    second = evaluate_cv(x_development, y_development)

    assert first == second
    assert set(first) == {"f1", "precision", "recall", "accuracy", "roc_auc"}
    for result in first.values():
        assert len(result["por_particao"]) == 3
        assert 0 <= result["media"] <= 1
        assert result["desvio_padrao"] >= 0
    # Os dados reservados ficam íntegros durante a avaliação.
    assert len(x_test) == len(y_test) == 8


def test_cv_rejects_too_few_positive_examples(sample_raw_data):
    data = normalize_dataset(sample_raw_data)
    x_development, _, y_development, _ = split_dataset(data)
    with pytest.raises(ValueError, match="ao menos n_splits"):
        evaluate_cv(x_development, y_development, n_splits=9)


def test_training_script_creates_report_and_reusable_model(tmp_path, sample_raw_data):
    csv = tmp_path / "telco.csv"
    output = tmp_path / "results"
    sample_raw_data.to_csv(csv, index=False)

    command = [
        sys.executable,
        "-m",
        "scripts.train_baseline",
        "--data",
        str(csv),
        "--output",
        str(output),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    assert "validação cruzada estratificada" in result.stdout

    report = json.loads((output / "baseline_cv.json").read_text(encoding="utf-8"))
    assert report["registros_desenvolvimento"] == 32
    assert report["registros_teste_reservado"] == 8
    assert report["caracteristicas"] == 19
    assert report["distribuicao_desenvolvimento"]["cancelaram"] == 8
    assert len(report["metricas_validacao"]["f1"]["por_particao"]) == 3

    model = load(output / "baseline.joblib")
    data = normalize_dataset(sample_raw_data)
    _, x_test, _, _ = split_dataset(data)
    assert model.predict(x_test).shape == (8,)
