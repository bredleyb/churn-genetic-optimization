"""Verificação do mapeamento da interface aos modelos já existentes."""

import json
from pathlib import Path

import pytest

from src.data import FEATURE_COLUMNS
from src.prediction import prepare_customer
from src.ui_data import (
    BILLING_FEATURES,
    INTERNET_FEATURES,
    LABELS,
    PHONE_FEATURES,
    PROFILE_FEATURES,
    PROFILE_FILES,
    QUICK_FEATURES,
    align_services,
    experiment_summary,
    label_for,
    load_profile,
    model_input,
    options_for,
)


ROOT = Path(__file__).resolve().parents[1]


def test_all_model_features_have_ui_labels_and_groups():
    grouped = (*QUICK_FEATURES, *PROFILE_FEATURES, *PHONE_FEATURES,
               *INTERNET_FEATURES, *BILLING_FEATURES)
    assert len(grouped) == len(FEATURE_COLUMNS) == 19
    assert len(set(grouped)) == 19
    assert set(LABELS) == set(FEATURE_COLUMNS)
    assert "Sim" == label_for("Yes")
    assert "Sem serviço de internet" == label_for("No internet service")
    assert options_for("Contract") == ("Month-to-month", "One year", "Two year")


@pytest.mark.parametrize("profile", list(PROFILE_FILES))
def test_examples_load_into_valid_19_field_model_input(profile):
    form = load_profile(ROOT, profile)
    assert form["SeniorCitizen"] in {"0", "1"}
    customer = model_input(form)
    assert len(customer) == 19
    assert list(prepare_customer(customer).columns) == list(FEATURE_COLUMNS)


def test_phone_service_conditional_changes_are_consistent():
    form = load_profile(ROOT, next(iter(PROFILE_FILES)))
    form["PhoneService"] = "No"
    aligned = align_services(form, changed="PhoneService")
    assert aligned["MultipleLines"] == "No phone service"
    assert model_input(aligned)["PhoneService"] == "No"
    aligned["PhoneService"] = "Yes"
    assert align_services(aligned, changed="PhoneService")["MultipleLines"] == "No"


def test_internet_dependency_is_adjusted_both_directions():
    form = load_profile(ROOT, next(iter(PROFILE_FILES)))
    form["InternetService"] = "No"
    aligned = align_services(form, changed="InternetService")
    assert all(aligned[k] == "No internet service" for k in INTERNET_FEATURES)
    model_input(aligned)
    aligned["InternetService"] = "DSL"
    restored = align_services(aligned, changed="InternetService")
    assert all(restored[k] == "No" for k in INTERNET_FEATURES)
    model_input(restored)


def test_optional_total_charges_matches_existing_imputation_path():
    form = load_profile(ROOT, next(iter(PROFILE_FILES)))
    form["total_missing"] = True
    assert model_input(form)["TotalCharges"] is None
    form["total_missing"] = False
    assert isinstance(model_input(form)["TotalCharges"], (int, float))


def test_invalid_input_rejected_by_the_same_domain_validation():
    form = load_profile(ROOT, next(iter(PROFILE_FILES)))
    form["tenure"] = -1
    with pytest.raises(ValueError, match="tenure"):
        model_input(form)
    form = load_profile(ROOT, next(iter(PROFILE_FILES)))
    form["PhoneService"] = "No"
    with pytest.raises(ValueError, match="MultipleLines"):
        model_input(form)


def test_experiment_summary_uses_actual_report_fields():
    metrics = {k: 0.5 for k in ("f1", "precision", "recall", "accuracy", "roc_auc")}
    result = experiment_summary({"dados": {"teste": 1409}, "modelos": {
        "baseline": {"teste": metrics, "caracteristicas": list(FEATURE_COLUMNS)},
        "genetico": {"teste": {**metrics, "f1": 0.4},
                     "caracteristicas": list(FEATURE_COLUMNS[:9])},
    }})
    assert result["test_count"] == 1409
    assert result["baseline_count"] == 19
    assert result["genetic_count"] == 9
    assert result["reduction_pct"] == pytest.approx(52.6315789474)
    assert result["baseline"]["f1"] == 0.5
    assert result["genetico"]["f1"] == 0.4
    with pytest.raises(ValueError, match="incompleto"):
        experiment_summary({})
