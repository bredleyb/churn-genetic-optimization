"""A tentativa registra cada widget de download só uma vez por execução."""
from types import SimpleNamespace

import pytest


@pytest.mark.parametrize("fail", [False, True])
def test_downloads_are_registered_once_and_enabled_only_after_rerun(client_app, monkeypatch, fail):
    app, ui = client_app
    from src.panel_values import log_bytes

    class DownloadSlot:
        def download_button(self, label, data, **kwargs):
            key = kwargs["key"]
            assert key not in registered, f"Widget duplicado no mesmo ciclo: {key}"
            registered[key] = (data, kwargs["disabled"])

    registered = {}
    original_slots = app._workspace_slots

    def slots():
        result = original_slots()
        result["log"] = DownloadSlot()
        result["terminal_download"] = DownloadSlot()
        return result

    monkeypatch.setattr(app, "_workspace_slots", slots)
    monkeypatch.setattr(app, "load_dataset", lambda path: [1, 2, 3])
    monkeypatch.setattr(app, "split_dataset", lambda *a, **k: ([1, 2], [3], [0, 1], [1]))
    monkeypatch.setattr(app, "evaluate_cv", lambda *a, **k: {"f1": {"media": .5}})
    chromosome = (1,) + (0,) * 18

    def select(*args, on_evaluation, on_generation, **kwargs):
        if fail:
            raise RuntimeError("falha controlada")
        record = {"geracao": 1, "melhor_f1_cv": .5, "melhor_aptidao": .49, "caracteristicas": 1}
        on_generation(record)
        return SimpleNamespace(chromosome=chromosome, selected_features=("gender",),
                               evaluated_subsets=1, elapsed_seconds=.1, best_cv_f1=.5)

    monkeypatch.setattr(app, "select_features", select)
    monkeypatch.setattr(app, "build_classifier", lambda *a, **k: SimpleNamespace(fit=lambda *a: None))
    monkeypatch.setattr(app, "evaluate_test", lambda *a: {
        "f1": .5, "precision": .5, "recall": .5, "accuracy": .5, "roc_auc": .5,
        "matriz_confusao": [[1, 1], [1, 1]],
    })
    monkeypatch.setattr(app, "predict_customer", lambda *a: {"classe": 1, "probabilidade_cancelamento": .6})
    app.main()
    assert len(registered) == 2 and all(disabled for _, disabled in registered.values())
    registered.clear()
    ui.reset_render()

    app._request_prediction()
    app.main()
    assert len(registered) == 2 and all(disabled for _, disabled in registered.values())
    assert ui.session_state["prediction_running"] is False
    assert ui.reruns == 1
    attempt = ui.session_state["workflow_attempt"]
    assert attempt["phase"] == ("failed" if fail else "complete")
    registered.clear()
    ui.reset_render()

    app.main()
    assert len(registered) == 2
    expected = log_bytes(attempt["events"])
    assert expected
    assert all(data == expected and not disabled for data, disabled in registered.values())
