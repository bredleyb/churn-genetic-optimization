"""Seleção de características originais por algoritmo genético.

Cada cromossomo representa as 19 características. A aptidão combina o
F1-score da regressão logística em validação cruzada e uma penalização
pela quantidade de atributos selecionados.
"""

from dataclasses import dataclass
from time import perf_counter
from typing import Callable

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_val_score

from src.data import FEATURE_COLUMNS
from src.model import build_classifier


@dataclass(frozen=True)
class GeneticConfig:
    """Configuração inicial da busca, conforme a metodologia do artigo."""

    population_size: int = 24
    generations: int = 15
    tournament_size: int = 3
    crossover_rate: float = 0.8
    mutation_rate: float = 0.2
    elite_count: int = 1
    penalty: float = 0.02
    cv_folds: int = 3
    random_state: int = 42

    def validate(self) -> None:
        if self.population_size < 2:
            raise ValueError("A população deve ter pelo menos dois indivíduos.")
        if self.generations < 1:
            raise ValueError("O número de gerações deve ser positivo.")
        if not 2 <= self.tournament_size <= self.population_size:
            raise ValueError("O torneio deve ter de dois indivíduos até o tamanho da população.")
        if not 1 <= self.elite_count < self.population_size:
            raise ValueError("O elitismo deve preservar pelo menos um indivíduo sem ocupar toda a população.")
        if not 0 <= self.crossover_rate <= 1:
            raise ValueError("A probabilidade de cruzamento deve estar entre 0 e 1.")
        if not 0 <= self.mutation_rate <= 1:
            raise ValueError("A probabilidade de mutação deve estar entre 0 e 1.")
        if self.penalty < 0:
            raise ValueError("A penalização não pode ser negativa.")
        if self.cv_folds < 2:
            raise ValueError("A validação cruzada exige pelo menos duas partições.")


@dataclass(frozen=True)
class GeneticResult:
    """Resumo da busca realizada no conjunto de desenvolvimento."""

    selected_features: tuple[str, ...]
    chromosome: tuple[int, ...]
    best_cv_f1: float
    best_fitness: float
    history: list[dict[str, int | float]]
    evaluated_subsets: int
    elapsed_seconds: float


def _ensure_nonempty(chromosome: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Impede indivíduos sem características selecionadas."""
    if not chromosome.any():
        chromosome[int(rng.integers(len(chromosome)))] = 1
    return chromosome


def _crossover(
    first: np.ndarray,
    second: np.ndarray,
    rng: np.random.Generator,
    probability: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Cruzamento de um ponto entre dois indivíduos."""
    if len(first) > 1 and rng.random() < probability:
        point = int(rng.integers(1, len(first)))
        return (
            np.concatenate((first[:point], second[point:])),
            np.concatenate((second[:point], first[point:])),
        )
    return first.copy(), second.copy()


def _mutate(
    chromosome: np.ndarray,
    rng: np.random.Generator,
    probability: float,
) -> np.ndarray:
    """Em indivíduos mutados, inverte cada bit com probabilidade 1/d."""
    if rng.random() < probability:
        flips = rng.random(len(chromosome)) < (1.0 / len(chromosome))
        chromosome[flips] = 1 - chromosome[flips]
    return _ensure_nonempty(chromosome, rng)


def select_features(
    x_development: pd.DataFrame,
    y_development: pd.Series,
    config: GeneticConfig | None = None,
    *,
    on_generation: Callable[[dict[str, int | float]], None] | None = None,
    on_evaluation: Callable[[dict[str, object]], None] | None = None,
) -> GeneticResult:
    """Seleciona atributos somente com os dados de desenvolvimento.

    O callback opcional on_evaluation informa o início e o fim da avaliação
    real de cada subconjunto não encontrado no cache, sem alterar a busca.
    Cada subconjunto é avaliado por pipelines ajustados dentro das partições
    de validação. As partições são fixadas para comparar os candidatos e o
    conjunto de teste permanece fora desta função.
    """
    config = config or GeneticConfig()
    config.validate()
    missing = [col for col in FEATURE_COLUMNS if col not in x_development.columns]
    if missing:
        raise ValueError("Características ausentes: " + ", ".join(missing))
    if len(x_development) != len(y_development):
        raise ValueError("Características e respostas devem ter a mesma quantidade de registros.")
    counts = y_development.value_counts()
    if len(counts) != 2 or counts.min() < config.cv_folds:
        raise ValueError("Cada classe deve ter ao menos cv_folds exemplos.")

    start = perf_counter()
    rng = np.random.default_rng(config.random_state)
    size = len(FEATURE_COLUMNS)
    cv = StratifiedKFold(n_splits=config.cv_folds, shuffle=True, random_state=config.random_state)
    folds = list(cv.split(x_development, y_development))
    cache: dict[tuple[int, ...], tuple[float, float]] = {}

    def evaluate(chromosome: np.ndarray, generation: int, individual: int) -> tuple[float, float]:
        key = tuple(int(bit) for bit in chromosome)
        if key not in cache:
            chosen = [name for name, bit in zip(FEATURE_COLUMNS, key) if bit]
            event = {
                "geracao": generation,
                "individuo": individual,
                "populacao": config.population_size,
                "cromossomo": key,
                "caracteristicas": tuple(chosen),
                "dobras": config.cv_folds,
            }
            if on_evaluation is not None:
                on_evaluation({**event, "etapa": "inicio", "avaliados": len(cache)})
            f1_scores = cross_val_score(
                build_classifier(chosen),
                x_development,
                y_development,
                cv=folds,
                scoring="f1",
                n_jobs=1,
                error_score="raise",
            )
            f1 = float(np.mean(f1_scores))
            cache[key] = (f1 - config.penalty * len(chosen) / size, f1)
            if on_evaluation is not None:
                on_evaluation({
                    **event, "etapa": "fim", "avaliados": len(cache),
                    "f1_cv": f1, "aptidao": cache[key][0],
                })
        return cache[key]

    population = [np.ones(size, dtype=np.int8)]
    for _ in range(config.population_size - 1):
        chromosome = rng.integers(0, 2, size, dtype=np.int8)
        population.append(_ensure_nonempty(chromosome, rng))

    history: list[dict[str, int | float]] = []
    best: np.ndarray | None = None
    best_values = (float("-inf"), float("-inf"))

    for generation in range(1, config.generations + 1):
        values = [
            evaluate(chromosome, generation, index)
            for index, chromosome in enumerate(population, start=1)
        ]
        order = sorted(range(len(population)), key=lambda i: values[i], reverse=True)
        winner = order[0]
        if values[winner] > best_values:
            best_values = values[winner]
            best = population[winner].copy()

        record = {
            "geracao": generation,
            "melhor_aptidao": round(float(best_values[0]), 6),
            "melhor_f1_cv": round(float(best_values[1]), 6),
            "caracteristicas": int(best.sum()),
        }
        history.append(record)
        if on_generation is not None:
            on_generation(record)
        if generation == config.generations:
            break

        next_population = [population[i].copy() for i in order[: config.elite_count]]

        def tournament() -> np.ndarray:
            candidates = rng.choice(len(population), size=config.tournament_size, replace=False)
            winner_index = max(candidates, key=lambda i: values[int(i)])
            return population[int(winner_index)].copy()

        while len(next_population) < config.population_size:
            first, second = _crossover(tournament(), tournament(), rng, config.crossover_rate)
            next_population.append(_mutate(first, rng, config.mutation_rate))
            if len(next_population) < config.population_size:
                next_population.append(_mutate(second, rng, config.mutation_rate))
        population = next_population

    assert best is not None
    chosen = tuple(name for name, bit in zip(FEATURE_COLUMNS, best) if bit)
    return GeneticResult(
        selected_features=chosen,
        chromosome=tuple(int(bit) for bit in best),
        best_cv_f1=round(float(best_values[1]), 6),
        best_fitness=round(float(best_values[0]), 6),
        history=history,
        evaluated_subsets=len(cache),
        elapsed_seconds=round(perf_counter() - start, 3),
    )
