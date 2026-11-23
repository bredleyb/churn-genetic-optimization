"""Estados persistentes, segurança dos perfis e dependências dos serviços."""
import pytest

from src.example_profiles import (
    MAX_EXAMPLES, append_example, can_delete_example,
    delete_example, initial_examples, is_original,
)
from src.ui_data import INTERNET_FEATURES, load_profile, model_input


def test_initial_examples_are_independent(client_app):
    app, _ = client_app
    examples = initial_examples(app.ROOT)
    assert list(examples) == ["Exemplo 1", "Exemplo 2"]
    for entry in examples.values():
        assert entry["original"] == entry["values"]
        assert entry["original"] is not entry["values"]
        assert len(model_input(entry["values"])) == 19


def test_creation_copies_current_client_and_stops_at_five(client_app):
    app, ui = client_app
    app._apply_profile("Exemplo 1")
    ui.session_state["field_tenure"] = 36
    app._remember_field("tenure")
    for i in range(3, MAX_EXAMPLES + 1):
        app._create_example()
        assert ui.session_state["profile_choice"] == f"Exemplo {i}"
        entry = ui.session_state["example_profiles"][f"Exemplo {i}"]
        assert entry["original"]["tenure"] == 36
        assert is_original(ui.session_state["example_profiles"], f"Exemplo {i}", entry["values"])
    assert len(ui.session_state["example_profiles"]) == 5
    with pytest.raises(ValueError, match="Limite de 5"):
        app._create_example()
    ui.reset_render()
    app.main()
    labels = [label for label, _ in ui.buttons]
    assert labels[:5] == ["1", "2", "3", "4", "5"]
    assert "+" not in labels


def test_edit_switch_restore_preserves_each_snapshot(client_app):
    app, ui = client_app
    app._apply_profile("Exemplo 1")
    original = ui.session_state["customer_values"]["MonthlyCharges"]
    edited = original + 10.0
    ui.session_state["field_MonthlyCharges"] = edited
    app._remember_field("MonthlyCharges")
    assert not app._is_profile_pristine()
    app._create_example()
    assert app._is_profile_pristine()
    ui.session_state["field_MonthlyCharges"] = 115.0
    app._remember_field("MonthlyCharges")
    app._select_example("Exemplo 2")
    app._select_example("Exemplo 1")
    assert ui.session_state["customer_values"]["MonthlyCharges"] == edited
    app._select_example("Exemplo 3")
    assert ui.session_state["customer_values"]["MonthlyCharges"] == 115.0
    app._reset_profile()
    assert app._is_profile_pristine()
    assert ui.session_state["customer_values"]["MonthlyCharges"] == edited
    app._select_example("Exemplo 1")
    app._reset_profile()
    assert ui.session_state["customer_values"]["MonthlyCharges"] == original


def test_delete_protects_first_two_and_renumbers_without_data_loss(client_app):
    app, ui = client_app
    app._apply_profile("Exemplo 1")
    examples = ui.session_state["example_profiles"]
    assert not can_delete_example(examples, "Exemplo 1")
    assert not can_delete_example(examples, "Exemplo 2")
    for name in ("Exemplo 1", "Exemplo 2"):
        with pytest.raises(ValueError, match="protegido"):
            delete_example(examples, name)

    for months in (30, 40, 50):
        ui.session_state["field_tenure"] = months
        app._remember_field("tenure")
        app._create_example()
    app._select_example("Exemplo 4")
    original5 = examples["Exemplo 5"]["original"]
    app._delete_active_example()
    assert ui.session_state["profile_choice"] == "Exemplo 3"
    assert list(examples) == ["Exemplo 1", "Exemplo 2", "Exemplo 3", "Exemplo 4"]
    assert examples["Exemplo 4"]["original"] is original5
    assert ui.session_state["workflow_run"] is None
    app._create_example()
    assert "Exemplo 5" in examples


def test_buttons_enablement_and_immediate_deletion(client_app):
    app, ui = client_app
    app.main()
    assert ui.button_options("Restaurar perfil")["disabled"]
    assert ui.button_options("Excluir perfil")["disabled"]
    assert ui.button_options("+")["on_click"] == app._create_example
    assert ui.button_options("Excluir perfil")["on_click"] == app._delete_active_example

    app._create_example()
    ui.reset_render()
    app.main()
    assert ui.button_options("Excluir perfil")["disabled"] is False
    assert ui.button_options("Restaurar perfil")["disabled"] is True
    ui.click_next = "Excluir perfil"
    ui.reset_render()
    app.main()
    assert "Exemplo 3" not in ui.session_state["example_profiles"]
    assert ui.session_state["profile_choice"] == "Exemplo 2"
    assert ui.reruns == 0


def test_services_are_saved_across_tabs_and_profiles(client_app):
    app, ui = client_app
    app._apply_profile("Exemplo 1")
    original = ui.session_state["customer_values"]["InternetService"]
    ui.session_state["field_InternetService"] = "No"
    app._on_service_change("InternetService")
    assert all(ui.session_state["customer_values"][key] == "No internet service" for key in INTERNET_FEATURES)
    app._select_example("Exemplo 2")
    app._select_example("Exemplo 1")
    assert ui.session_state["field_InternetService"] == "No"
    assert all(ui.session_state["field_" + key] == "No internet service" for key in INTERNET_FEATURES)
    app._reset_profile()
    assert ui.session_state["field_InternetService"] == original

    ui.session_state["field_PhoneService"] = "No"
    app._on_service_change("PhoneService")
    assert ui.session_state["field_MultipleLines"] == "No phone service"
    ui.session_state["field_PhoneService"] = "Yes"
    app._on_service_change("PhoneService")
    assert ui.session_state["field_MultipleLines"] == "No"


def test_tenure_component_callback_clamps_and_changes_revision_on_switch(client_app):
    app, ui = client_app
    app._apply_profile("Exemplo 1")
    old_revision = ui.session_state["tenure_revision"]
    ui.session_state[f"n3-tenure-{old_revision}"] = {"value": 1500}
    app._on_tenure_component_change()
    assert ui.session_state["field_tenure"] == 999
    assert ui.session_state["customer_values"]["tenure"] == 999
    ui.session_state[f"n3-tenure-{old_revision}"] = {"value": -30}
    app._on_tenure_component_change()
    assert ui.session_state["field_tenure"] == 0
    app._select_example("Exemplo 2")
    assert ui.session_state["tenure_revision"] == old_revision + 1


def test_legacy_session_migration_preserves_draft_and_pristine_reference(client_app):
    app, ui = client_app
    original = load_profile(app.ROOT, "Exemplo 1")
    draft = {**original, "tenure": 42}
    ui.session_state.update({"profile_choice": "Exemplo 1", "customer_values": draft})
    app._ensure_examples()
    examples = ui.session_state["example_profiles"]
    assert examples["Exemplo 1"]["values"]["tenure"] == 42
    assert examples["Exemplo 1"]["original"]["tenure"] == original["tenure"]
