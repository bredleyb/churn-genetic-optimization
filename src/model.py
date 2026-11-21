"""Classificador de referência e avaliação no conjunto de desenvolvimento."""

from collections.abc import Iterable

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline

from src.preprocessing import build_preprocessor

METRICS = {
    "f1": "f1",
    "precision": "precision",
    "recall": "recall",
    "accuracy": "accuracy",
    "roc_auc": "roc_auc",
}


def build_classifier(selected_features: Iterable[str] | None = None) -> Pipeline:
    """Monta regressão logística com pré-processamento ajustado no treinamento.

    O mesmo classificador será usado com todas as características (baseline)
    e com subconjuntos candidatos selecionados pelo algoritmo genético.
    """
    return Pipeline(
        steps=[
            ("preprocessor", build_preprocessor(selected_features)),
            ("classifier", LogisticRegression(max_iter=1000)),
        ]
    )


def evaluate_cv(
    x_development: pd.DataFrame,
    y_development: pd.Series,
    *,
    selected_features: Iterable[str] | None = None,
    n_splits: int = 3,
    random_state: int = 42,
) -> dict[str, dict[str, float | list[float]]]:
    """Avalia no desenvolvimento com validação estratificada reproduzível.

    Cada partição ajusta um pipeline independente, inclusive imputação,
    codificação e padronização. O conjunto de teste não é recebido aqui.
    """
    if n_splits < 2:
        raise ValueError("A validação cruzada exige ao menos duas partições.")
    counts = y_development.value_counts()
    if len(counts) != 2 or counts.min() < n_splits:
        raise ValueError("Cada classe deve ter ao menos n_splits exemplos.")

    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    scores = cross_validate(
        build_classifier(selected_features),
        x_development,
        y_development,
        cv=cv,
        scoring=METRICS,
        n_jobs=1,
        error_score="raise",
    )

    result = {}
    for metric in METRICS:
        values = np.asarray(scores[f"test_{metric}"], dtype=float)
        result[metric] = {
            "por_particao": [round(float(value), 4) for value in values],
            "media": round(float(values.mean()), 4),
            "desvio_padrao": round(float(values.std()), 4),
        }
    return result
