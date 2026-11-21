"""Testes de seleção de características e dos operadores genéticos."""

import json
import subprocess
import sys

import numpy as np
import pytest
from joblib import load

from src.data import FEATURE_COLUMNS, normalize_dataset, split_dataset
from src.genetic import GeneticConfig, _crossover, _mutate, select_features


def test_crossover_preserves_parents_and_creates_valid_children():
    rng = np.random.default_rng(12)
    first = np.ones(5, dtype=np.int8)
    second = np.zeros(5, dtype=np.int8)
    child_a, child_b = _crossover(first, second, rng, probability=1.0)
    assert child_a.shape == child_b.shape == first.shape
    assert set(child_a).issubset({0, 1})
    assert np.array_equal(child_a + child_b, np.ones(5, dtype=np.int8))
    assert np.array_equal(first, np.ones(5, dtype=np.int8))
    assert np.array_equal(second, np.zeros(5, dtype=np.int8))


def test_mutation_always_keeps_at_least_one_feature():
    rng = np.random.default_rng(7)
    for _ in range(20):
        candidate = np.zeros(19, dtype=np.int8)
        mutated = _mutate(candidate, rng, probability=1.0)
        assert mutated.any()
        assert set(mutated).issubset({0, 1})


def test_configuration_rejects_invalid_parameters():
    for config in [
        GeneticConfig(population_size=1),
        GeneticConfig(generations=0),
        GeneticConfig(population_size=2, tournament_size=3),
        GeneticConfig(elite_count=24),
        GeneticConfig(crossover_rate=1.2),
        GeneticConfig(mutation_rate=-0.1),
        GeneticConfig(penalty=-1),
        GeneticConfig(cv_folds=1),
    ]:
        with pytest.raises(ValueError):
            config.validate()


def test_genetic_selection_is_reproducible_and_respects_fitness(sample_raw_data):
    data = normalize_dataset(sample_raw_data)
    x_dev, x_test, y_dev, y_test = split_dataset(data)
    config = GeneticConfig(population_size=6, generations=3, random_state=42)
    result = select_features(x_dev, y_dev, config)
    again = select_features(x_dev, y_dev, config)
    assert result.selected_features == again.selected_features
    assert result.chromosome == again.chromosome
    assert result.history == again.history
    assert result.best_fitness == again.best_fitness
    assert len(result.chromosome) == len(FEATURE_COLUMNS) == 19
    assert set(result.chromosome).issubset({0, 1})
    assert set(result.selected_features).issubset(set(FEATURE_COLUMNS))
    assert len(result.selected_features) == sum(result.chromosome) >= 1
    assert result.selected_features == tuple(
        name for name, bit in zip(FEATURE_COLUMNS, result.chromosome) if bit
    )
    assert result.best_fitness == pytest.approx(
        result.best_cv_f1 - config.penalty * len(result.selected_features) / 19,
        abs=0.000002,
    )
    assert len(result.history) == config.generations
    assert [row["geracao"] for row in result.history] == [1, 2, 3]
    assert all(
        newer["melhor_aptidao"] >= old["melhor_aptidao"]
        for old, newer in zip(result.history, result.history[1:])
    )
    assert 1 <= result.evaluated_subsets <= config.population_size * config.generations
    assert len(x_test) == len(y_test) == 8


def test_genetic_selection_checks_inputs(sample_raw_data):
    data = normalize_dataset(sample_raw_data)
    x_dev, _, y_dev, _ = split_dataset(data)
    config = GeneticConfig(population_size=4, tournament_size=2, generations=1)
    with pytest.raises(ValueError, match="Características ausentes"):
        select_features(x_dev.drop(columns=["Contract"]), y_dev, config)
    with pytest.raises(ValueError, match="mesma quantidade"):
        select_features(x_dev, y_dev.iloc[:-1], config)
    with pytest.raises(ValueError, match="ao menos cv_folds"):
        select_features(x_dev, y_dev, GeneticConfig(cv_folds=9))


def test_genetic_cli_creates_report_and_trained_model(tmp_path, sample_raw_data):
    csv_path = tmp_path / "telco.csv"
    output = tmp_path / "results"
    sample_raw_data.to_csv(csv_path, index=False)
    cmd = [
        sys.executable, "-m", "scripts.run_genetic",
        "--data", str(csv_path), "--output", str(output),
        "--population", "6", "--generations", "2",
    ]
    completed = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert "Geração  1" in completed.stdout
    report = json.loads((output / "genetic_selection.json").read_text(encoding="utf-8"))
    assert len(report["cromossomo"]) == len(FEATURE_COLUMNS)
    assert report["registros_desenvolvimento"] == 32
    assert report["registros_teste_reservado"] == 8
    assert report["parametros"]["generations"] == 2
    assert len(report["historico"]) == 2
    assert len(report["atributos_selecionados"]) > 0

    model = load(output / "genetic.joblib")
    data = normalize_dataset(sample_raw_data)
    _, x_test, _, _ = split_dataset(data)
    assert model.predict(x_test).shape == (8,)
