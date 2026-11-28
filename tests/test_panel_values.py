"""Indicadores da tentativa e probabilidades exibidas no painel."""
import pytest
from src.panel_values import probability_values, status_values


def test_initial_status_has_no_invented_measurements():
    assert status_values(None, now=100) == {
        "generations": 0, "subsets": 0, "selected": None,
        "reduction": None, "elapsed": None,
    }


def test_search_status_uses_real_callbacks_and_clock():
    data = {"history": [{"geracao": 1}], "evaluated_subsets": 3,
            "chromosome": (1,) * 9 + (0,) * 10,
            "search_started_at": 10.0, "elapsed_seconds": 0.0}
    result = status_values(data, now=12.5)
    assert result["generations"] == 1
    assert result["subsets"] == 3
    assert result["selected"] == 9
    assert result["reduction"] == pytest.approx(1000 / 19)
    assert result["elapsed"] == 2.5
    data.update(search_started_at=None, elapsed_seconds=2.7)
    assert status_values(data, now=100)["elapsed"] == 2.7


def test_probability_uses_class_even_at_rounded_threshold():
    value, label, semantic = probability_values({"classe": 0, "probabilidade_cancelamento": 0.5})
    assert value == 50
    assert label == "Permanência"
    assert semantic == "is-positive"
    assert probability_values(None) == (None, "", "")
    assert probability_values({"classe": 1, "probabilidade_cancelamento": 0.49999})[1] == "Cancelamento"


def test_probability_rejects_nonfinite_values():
    with pytest.raises(ValueError):
        probability_values({"classe": 1, "probabilidade_cancelamento": float("nan")})



def test_generation_series_keeps_paired_values_and_observed_generations():
    from src.panel_values import generation_series
    rows = [{"geracao": 1, "melhor_f1_cv": .61, "melhor_aptidao": .59},
            {"geracao": 3, "melhor_f1_cv": .60, "melhor_aptidao": .595}]
    assert generation_series([]) == []
    assert generation_series(rows) == [(1, .61, .59), (3, .60, .595)]


def test_impact_uses_test_metrics_and_confusion_matrix():
    from src.panel_values import impact_values
    assert impact_values(None) == {"f1": None, "recall_pp": None, "fn": None}
    result = impact_values({
        "baseline": {"f1": .604, "recall": .5588, "matriz_confusao": [[926,109],[165,209]]},
        "genetico": {"f1": .5869, "recall": .5374, "matriz_confusao": [[925,110],[173,201]]},
    })
    assert result["f1"] == pytest.approx(-.0171)
    assert result["recall_pp"] == pytest.approx(-2.14)
    assert result["fn"] == 8


def test_metric_sections_unavailable_twenty_cells():
    from src.panel_values import metric_sections
    sections = metric_sections(None)
    assert [len(rows) for _, rows in sections] == [5, 1, 4]
    assert all(a == b == "—" for _, rows in sections for _, a, b in rows)


def test_metric_sections_preserve_units_and_order():
    from src.panel_values import metric_sections
    base = dict(f1=.604, precision=.6572, recall=.5588, accuracy=.8055,
                roc_auc=.8419, matriz_confusao=[[926,109],[165,209]])
    genetic = dict(f1=.5869, precision=.6463, recall=.5374, accuracy=.7991,
                   roc_auc=.8401, matriz_confusao=[[925,110],[173,201]])
    groups = dict(metric_sections({"baseline":base, "genetico":genetic,
                                  "baseline_cv_f1":.5952, "genetic_cv_f1":.6059}))
    assert groups["Conjunto de teste"][0] == ("F1-score", "0,6040", "0,5869")
    assert groups["Conjunto de teste"][2] == ("Recall", "55,88%", "53,74%")
    assert groups["Validação cruzada"][0] == ("F1 médio (CV)", "0,5952", "0,6059")
    assert groups["Matriz de confusão"][2] == ("Falsos negativos", "165", "173")


def test_export_is_exact_utf8_and_empty_without_events():
    from src.panel_values import log_bytes
    events = ["[EXECUÇÃO] Processamento iniciado.", "[ERRO] Não foi possível concluir."]
    assert log_bytes(events).decode("utf-8") == "\n".join(events) + "\n"
    assert log_bytes([]) == b""
