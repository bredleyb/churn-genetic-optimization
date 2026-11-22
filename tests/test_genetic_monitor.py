"""Monitor de avaliações reais, sem mudança nos resultados da seleção."""

import numpy as np
import pandas as pd
import pytest

from src.data import FEATURE_COLUMNS
from src.genetic import GeneticConfig, select_features
from src.ui_data import format_evaluation_line


def test_evaluation_callback_reports_real_unique_subsets_and_preserves_search():
    x = pd.DataFrame(np.zeros((36, len(FEATURE_COLUMNS))), columns=FEATURE_COLUMNS)
    y = pd.Series([0, 1] * 18)
    config = GeneticConfig(population_size=6, generations=3, random_state=42)
    observed = []
    with_events = select_features(x, y, config, on_evaluation=observed.append)
    without_events = select_features(x, y, config)

    assert with_events.selected_features == without_events.selected_features
    assert with_events.chromosome == without_events.chromosome
    assert with_events.history == without_events.history
    assert with_events.best_fitness == without_events.best_fitness
    assert with_events.evaluated_subsets == without_events.evaluated_subsets
    assert len(observed) == 2 * with_events.evaluated_subsets

    chromosomes = set()
    for start, end in zip(observed[::2], observed[1::2]):
        assert (start["etapa"], end["etapa"]) == ("inicio", "fim")
        assert start["cromossomo"] == end["cromossomo"]
        assert len(start["cromossomo"]) == len(FEATURE_COLUMNS)
        assert sum(start["cromossomo"]) == len(start["caracteristicas"]) >= 1
        assert start["dobras"] == config.cv_folds
        assert end["avaliados"] == start["avaliados"] + 1
        assert end["aptidao"] == pytest.approx(
            end["f1_cv"] - config.penalty * len(start["caracteristicas"]) / 19
        )
        assert 1 <= start["geracao"] <= config.generations
        assert 1 <= start["individuo"] <= config.population_size
        chromosomes.add(start["cromossomo"])
    assert len(chromosomes) == with_events.evaluated_subsets


def test_evaluation_logs_are_formatted_without_invented_progress():
    base = {
        "geracao": 2,
        "individuo": 4,
        "populacao": 24,
        "dobras": 3,
        "caracteristicas": ("tenure", "Contract"),
        "cromossomo": (1, 0) + (0,) * 17,
        "avaliados": 5,
    }
    assert format_evaluation_line({**base, "etapa": "inicio"}) == (
        "[G02] indivíduo 04/24 | avaliando 2/19 características | CV: 3 partições"
    )
    assert format_evaluation_line({**base, "etapa": "fim", "f1_cv": .6015,
                                   "aptidao": .599395}) == (
        "[G02] indivíduo 04/24 | F1: 0,6015 | aptidão: 0,5994 | subconjunto 5"
    )
    with pytest.raises(ValueError, match="desconhecida"):
        format_evaluation_line({**base, "etapa": "cache"})
