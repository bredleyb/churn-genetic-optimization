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


def metric_sections(summary: dict | None) -> list[tuple[str, list[tuple[str, str, str]]]]:
    """Dez pares numéricos; ausência é explicitamente representada."""
    def format_value(value, kind):
        if value is None:
            return "—"
        if kind == "integer":
            return f"{int(value):,}".replace(",", ".")
        if kind == "percent":
            return f"{100 * float(value):.2f}".replace(".", ",") + "%"
        return f"{float(value):.4f}".replace(".", ",")

    source = summary or {}
    base, genetic = source.get("baseline", {}), source.get("genetico", {})
    tests = [
        (label, format_value(base.get(key), kind), format_value(genetic.get(key), kind))
        for key, label, kind in (
            ("f1", "F1-score", "decimal"), ("precision", "Precisão", "percent"),
            ("recall", "Recall", "percent"), ("accuracy", "Acurácia", "percent"),
            ("roc_auc", "ROC-AUC", "decimal"),
        )
    ]
    cv = [("F1 médio (CV)", format_value(source.get("baseline_cv_f1"), "decimal"),
           format_value(source.get("genetic_cv_f1"), "decimal"))]
    matrix = []
    for label, row, col in (("Verdadeiros negativos", 0, 0), ("Falsos positivos", 0, 1),
                            ("Falsos negativos", 1, 0), ("Verdadeiros positivos", 1, 1)):
        matrix.append((label, format_value(base["matriz_confusao"][row][col] if "matriz_confusao" in base else None, "integer"),
                       format_value(genetic["matriz_confusao"][row][col] if "matriz_confusao" in genetic else None, "integer")))
    return [("Conjunto de teste", tests), ("Validação cruzada", cv), ("Matriz de confusão", matrix)]


def log_bytes(events: list[str]) -> bytes:
    return ("\n".join(events) + "\n").encode("utf-8") if events else b""
