"""Testes da comparação final com dados sintéticos controlados."""

import json
import subprocess
import sys

import numpy as np
import pytest

from src.data import normalize_dataset, split_dataset
from src.evaluation import evaluate_test
from src.genetic import GeneticConfig
from src.model import build_classifier
from scripts.compare_models import make_markdown, run


def test_evaluation_on_heldout_samples(sample_raw_data):
    data = normalize_dataset(sample_raw_data)
    x_development, x_test, y_development, y_test = split_dataset(data)
    model = build_classifier()
    model.fit(x_development, y_development)

    scores = evaluate_test(model, x_test, y_test)
    assert set(scores) == {"f1", "precision", "recall", "accuracy", "roc_auc", "matriz_confusao"}
    for metric in ("f1", "precision", "recall", "accuracy", "roc_auc"):
        assert 0 <= scores[metric] <= 1
    assert np.asarray(scores["matriz_confusao"]).shape == (2, 2)
    assert np.asarray(scores["matriz_confusao"]).sum() == len(x_test)


def test_rejects_empty_and_mismatched_test(sample_raw_data):
    data = normalize_dataset(sample_raw_data)
    x_development, x_test, y_development, y_test = split_dataset(data)
    model = build_classifier()
    model.fit(x_development, y_development)
    with pytest.raises(ValueError, match="vazio"):
        evaluate_test(model, x_test.iloc[:0], y_test.iloc[:0])
    with pytest.raises(ValueError, match="tamanhos diferentes"):
        evaluate_test(model, x_test, y_test.iloc[:-1])


def test_comparison_generates_reports_and_models(tmp_path, sample_raw_data):
    csv_path = tmp_path / "telco.csv"
    sample_raw_data.to_csv(csv_path, index=False)
    output = tmp_path / "results"
    config = GeneticConfig(population_size=4, generations=2, tournament_size=2)
    report = run(csv_path, output, config=config)

    assert report["dados"]["desenvolvimento"] == 32
    assert report["dados"]["teste"] == 8
    assert report["dados"]["cancelamentos_no_teste"] == 2
    assert 1 <= len(report["modelos"]["genetico"]["caracteristicas"]) <= 19
    assert sum(sum(row) for row in report["modelos"]["baseline"]["teste"]["matriz_confusao"]) == 8
    assert (output / "baseline.joblib").is_file()
    assert (output / "genetic.joblib").is_file()
    saved = json.loads((output / "comparacao_modelos.json").read_text(encoding="utf-8"))
    assert saved["busca_genetica"]["subconjuntos_avaliados"] > 0
    markdown = (output / "comparacao_modelos.md").read_text(encoding="utf-8")
    assert markdown == make_markdown(report)
    assert "falsos negativos" in markdown


def test_comparison_cli(tmp_path, sample_raw_data):
    csv_path = tmp_path / "telco.csv"
    output = tmp_path / "results"
    sample_raw_data.to_csv(csv_path, index=False)
    result = subprocess.run(
        [sys.executable, "-m", "scripts.compare_models", "--data", str(csv_path),
         "--output", str(output), "--population", "4", "--generations", "1"],
        capture_output=True, text=True, check=True,
    )
    assert "Comparação no conjunto de teste" in result.stdout
    assert (output / "comparacao_modelos.json").is_file()
