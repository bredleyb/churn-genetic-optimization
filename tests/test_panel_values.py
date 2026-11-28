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
