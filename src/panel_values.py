"""Indicadores derivados exclusivamente dos dados de uma tentativa real."""
import math

from src.data import FEATURE_COLUMNS


def status_values(data: dict | None, *, now: float) -> dict:
    source = data or {}
    elapsed = source.get("elapsed_seconds")
    started = source.get("search_started_at")
    if started is not None:
        elapsed = max(0.0, now - started)
    chromosome = source.get("chromosome")
    selected = sum(chromosome) if chromosome is not None else None
    return {
        "generations": len(source.get("history", [])),
        "subsets": source.get("evaluated_subsets", 0),
        "selected": selected,
        "reduction": (100 * (len(FEATURE_COLUMNS) - selected) / len(FEATURE_COLUMNS)
                      if selected is not None else None),
        "elapsed": elapsed,
    }


def probability_values(entry: dict | None) -> tuple[float | None, str, str]:
    if entry is None:
        return None, "", ""
    probability = float(entry["probabilidade_cancelamento"])
    if not math.isfinite(probability) or not 0 <= probability <= 1:
        raise ValueError("Probabilidade inválida.")
    label = "Cancelamento" if entry["classe"] == 1 else "Permanência"
    semantic = "is-negative" if entry["classe"] == 1 else "is-positive"
    return probability * 100, label, semantic



def generation_series(history: list[dict]) -> list[tuple[int, float, float]]:
    """F1 e fitness correspondem ao mesmo melhor indivíduo de cada geração."""
    return [(int(row["geracao"]), float(row["melhor_f1_cv"]),
             float(row["melhor_aptidao"])) for row in history]


def impact_values(summary: dict | None) -> dict:
    if summary is None:
        return {"f1": None, "recall_pp": None, "fn": None}
    base, genetic = summary["baseline"], summary["genetico"]
    return {
        "f1": genetic["f1"] - base["f1"],
        "recall_pp": 100 * (genetic["recall"] - base["recall"]),
        "fn": genetic["matriz_confusao"][1][0] - base["matriz_confusao"][1][0],
    }
