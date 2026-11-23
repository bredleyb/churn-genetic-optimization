"""Contratos de apresentação, campos e valores do painel Cliente."""
from inspect import getsource
from pathlib import Path

import pytest

from src.data import FEATURE_COLUMNS
from src.prediction import prepare_customer
from src.tenure_control import _COMPONENT_CSS, _COMPONENT_HTML
from src.ui_data import (
    BILLING_FEATURES, INTERNET_FEATURES, LABELS, PHONE_FEATURES,
    PROFILE_FEATURES, QUICK_FEATURES, PROFILE_FILES,
    align_services, label_for, load_profile, model_input, options_for,
)


def test_client_uses_all_19_dataset_features_once():
    groups = QUICK_FEATURES + PROFILE_FEATURES + PHONE_FEATURES + INTERNET_FEATURES + BILLING_FEATURES
    assert len(groups) == len(set(groups)) == len(FEATURE_COLUMNS) == 19
    assert set(groups) == set(LABELS) == set(FEATURE_COLUMNS)
    assert QUICK_FEATURES == ("tenure", "Contract", "InternetService", "MonthlyCharges")
    assert PROFILE_FEATURES == ("gender", "SeniorCitizen", "Partner", "Dependents")
    assert set(PROFILE_FILES) == {"Exemplo 1", "Exemplo 2"}
    assert options_for("gender") == ("Female", "Male")
    assert {label_for(value) for value in options_for("gender")} == {"Feminino", "Masculino"}


@pytest.mark.parametrize("name", list(PROFILE_FILES))
def test_original_examples_are_valid_model_inputs(name, client_app):
    app, _ = client_app
    original = load_profile(app.ROOT, name)
    customer = model_input(original)
    assert len(customer) == 19
    assert list(prepare_customer(customer).columns) == list(FEATURE_COLUMNS)


def test_form_emits_the_required_client_controls(client_app, monkeypatch):
    app, ui = client_app
    monkeypatch.setattr(app, "DATASET", Path(__file__))
    app.main()
    assert ui.page_config["layout"] == "wide"
    keys = [row.get("key") for row in ui.containers]
    for required in (
        "dashboard-shell", "dashboard-client", "dashboard-client-fields",
        "dashboard-profile-picker", "dashboard-profile-choices",
        "dashboard-profile-actions", "dashboard-quick-fields",
        "dashboard-detail-tabs", "dashboard-client-footer",
    ):
        assert keys.count(required) == 1, required

    assert ("Perfil", "Conta", "Serviços", "Extras") in ui.tab_sets
    shown_keys = {key for kind, label, key, opts in ui.inputs}
    expected = {"field_" + name for name in FEATURE_COLUMNS if name != "tenure"}
    expected.add("field_total_missing")
    assert expected <= shown_keys
    assert not any(key == "field_tenure" for kind, label, key, opts in ui.inputs)
    assert len([item for item in ui.component_defs if item[0] == "n3_tenure_control"]) == 1
    assert len([item for item in ui.component_defs if item[0] == "n3_client_scroll_cues"]) == 1


def test_form_grids_share_one_column_proportion(client_app):
    app, _ = client_app
    source = getsource(app._render_client_panel)
    assert app.QUICK_FIELD_COLUMNS == (0.55, 0.45)
    assert source.count("st.columns(QUICK_FIELD_COLUMNS") == 2
    assert 'st.selectbox("Perfil de exemplo"' not in source
    assert "_render_client_details()" in source


def test_category_translation_and_service_dependencies(client_app):
    app, _ = client_app
    source = load_profile(app.ROOT, "Exemplo 1")
    source["PhoneService"] = "No"
    changed = align_services(source, changed="PhoneService")
    assert changed["MultipleLines"] == "No phone service"
    changed["PhoneService"] = "Yes"
    assert align_services(changed, changed="PhoneService")["MultipleLines"] == "No"

    source = load_profile(app.ROOT, "Exemplo 1")
    source["InternetService"] = "No"
    changed = align_services(source, changed="InternetService")
    assert all(changed[name] == "No internet service" for name in INTERNET_FEATURES)
    assert len(model_input(changed)) == 19
    changed["InternetService"] = "DSL"
    restored = align_services(changed, changed="InternetService")
    assert all(restored[name] == "No" for name in INTERNET_FEATURES)


def test_missing_total_and_invalid_data_use_the_same_model_validator(client_app):
    app, _ = client_app
    form = load_profile(app.ROOT, "Exemplo 1")
    form["total_missing"] = True
    assert model_input(form)["TotalCharges"] is None
    form["total_missing"] = False
    assert isinstance(model_input(form)["TotalCharges"], (int, float))
    form["tenure"] = -1
    with pytest.raises(ValueError, match="tenure"):
        model_input(form)
    form = load_profile(app.ROOT, "Exemplo 1")
    form["PhoneService"] = "No"
    with pytest.raises(ValueError, match="MultipleLines"):
        model_input(form)


def test_tenure_component_contract_has_one_input_and_protected_suffix(client_app):
    app, ui = client_app
    app.main()
    html = next(spec["html"] for name, spec in ui.component_defs if name == "n3_tenure_control")
    js = next(spec["js"] for name, spec in ui.component_defs if name == "n3_tenure_control")
    assert html == _COMPONENT_HTML
    assert html.count('<input ') == 1
    assert 'aria-label="Tempo como cliente"' in html
    assert 'data-step="-1"' in html and 'data-step="1"' in html
    assert "beforeinput" in js and "paste" in js and "placeCaret" in js
    assert "setStateValue" in js
    assert "requestAnimationFrame(placeCaret)" not in js
    for token in ("--n3-field-height", "--n3-field-fill", "--n3-field-radius",
                  "--n3-field-text-size", "--n3-field-text-shift"):
        assert token in _COMPONENT_CSS


def test_shared_css_tokens_and_scroll_contract(client_app):
    _, ui = client_app
    css = ui.markup[0]
    for token in (
        "--n3-bg:#000000", "--n3-surface:#0E1013",
        "--n3-outline:#55585D", "--n3-text:#F5F5F5",
        "--n3-secondary:#D8D8D8", "--n3-field-height:42px",
        "--n3-field-radius:4px", "--n3-field-text-size:14px",
        "--n3-client-content-inset:10px", "--n3-client-action-height:48px",
        "--n3-client-action-height:44px", "--n3-profile-button-size:32px",
        "--n3-profile-button-size:28px", "--n3-profile-button-size:26px",
        "scrollbar-gutter:stable both-edges",
        "padding-inline:var(--n3-client-content-inset)",
        "var(--n3-client-shadow-top,0)", "var(--n3-client-shadow-bottom,0)",
    ):
        assert token in css, token
    assert ".st-key-dashboard-client-fields,\n.st-key-dashboard-client-footer {" in css
    assert 'stLayoutWrapper"]:has(.st-key-dashboard-client-footer)::before' in css
    assert ".st-key-dashboard-client-footer::before {" not in css
    assert "border-top:0!important" in css
    assert "border-radius:50%!important" in css
    assert "border-radius:var(--n3-field-radius)!important" in css
    assert "container-name:n3-client;container-type:inline-size" in css
    assert "@container n3-client (max-width:335px)" in css
    assert '[data-testid="stNumberInputContainer"]' in css
    assert "height:var(--n3-client-action-height)!important" in css
    assert "@keyframes n3-calculating-ellipsis" in css
    assert "prefers-reduced-motion:reduce" in css


def test_profile_actions_have_expected_icons_and_are_not_confusable(client_app):
    app, ui = client_app
    app.main()
    restore = ui.button_options("Restaurar perfil")
    delete = ui.button_options("Excluir perfil")
    assert restore["icon"] == ":material/history:"
    assert delete["icon"] == ":material/delete_outline:"
    assert restore["type"] == delete["type"] == "tertiary"
    assert restore["disabled"] is True
    assert delete["disabled"] is True
    assert restore["on_click"] == app._reset_profile
    assert delete["on_click"] == app._delete_active_example
