"""Contrato da navegação única de Previsão, sem disparar o experimento."""
from pathlib import Path

def test_prediction_has_four_persistent_tabs(client_app):
    app, ui = client_app
    app.main()
    assert ui.tab_sets.count(("Painel", "Terminal", "Métricas", "Metodologia")) == 1
    assert ("Análise", "Execução") not in ui.tab_sets
    keys = [entry.get("key") for entry in ui.containers]
    assert keys.count("dashboard-prediction-tabs") == 1
    assert "dashboard-mobile-detail" not in keys
    assert "dashboard-desktop-detail" not in keys
    assert ui.session_state["workflow_run"] is None


def test_terminal_and_monitor_share_events_but_keep_order(client_app):
    app, _ = client_app
    class Slot:
        def __init__(self): self.markup = ""
        def markdown(self, content, **kwargs): self.markup = content
    slots = {"console": Slot(), "terminal": Slot()}
    events = ["primeiro", "último"]
    app._render_logs(events, slots, historical=True, message="Execução anterior")
    assert slots["console"].markup.index("último") < slots["console"].markup.index("primeiro")
    assert slots["terminal"].markup.index("primeiro") < slots["terminal"].markup.index("último")
    assert "Última execução" in slots["terminal"].markup
    assert events == ["primeiro", "último"]
