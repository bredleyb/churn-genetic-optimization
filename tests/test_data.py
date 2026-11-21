import numpy as np
import pandas as pd
import pytest

from src.data import (
    CATEGORICAL_FEATURES,
    FEATURE_COLUMNS,
    NUMERIC_FEATURES,
    features_and_target,
    load_dataset,
    normalize_dataset,
    split_dataset,
)


def test_load_dataset_and_convert_values(tmp_path, sample_raw_data):
    csv = tmp_path / "telco.csv"
    sample_raw_data.to_csv(csv, index=False)
    data = load_dataset(csv)
    assert data.shape == (40, 21)
    assert np.isnan(data.loc[0, "TotalCharges"])
    assert data.loc[1, "TotalCharges"] == 38.0
    assert data["SeniorCitizen"].iloc[0] == "0"
    assert data["SeniorCitizen"].iloc[1] == "1"
    assert data["Churn"].iloc[:5].tolist() == [1, 0, 0, 0, 1]
    assert len(FEATURE_COLUMNS) == 19
    assert len(NUMERIC_FEATURES) == 3
    assert len(CATEGORICAL_FEATURES) == 16


def test_csv_missing(tmp_path):
    with pytest.raises(FileNotFoundError, match="CSV não encontrado"):
        load_dataset(tmp_path / "nao_existe.csv")


def test_missing_column(sample_raw_data):
    with pytest.raises(ValueError, match="Colunas obrigatórias ausentes: TotalCharges"):
        normalize_dataset(sample_raw_data.drop(columns=["TotalCharges"]))


def test_invalid_label(sample_raw_data):
    frame = sample_raw_data.copy()
    frame.loc[0, "Churn"] = "Unknown"
    with pytest.raises(ValueError, match="Churn deve conter"):
        normalize_dataset(frame)


def test_invalid_numeric_value(sample_raw_data):
    frame = sample_raw_data.copy()
    frame.loc[1, "TotalCharges"] = "texto inesperado"
    with pytest.raises(ValueError, match="TotalCharges"):
        normalize_dataset(frame)


def test_duplicate_customer_id_rejected(sample_raw_data):
    data = normalize_dataset(sample_raw_data)
    data.loc[1, "customerID"] = data.loc[0, "customerID"]
    with pytest.raises(ValueError, match="customerID duplicado"):
        split_dataset(data)


def test_stratified_deterministic_split(sample_raw_data):
    data = normalize_dataset(sample_raw_data)
    result_a = split_dataset(data, random_state=42)
    result_b = split_dataset(data, random_state=42)
    x_train, x_test, y_train, y_test = result_a
    assert len(x_train) == 32
    assert len(x_test) == 8
    assert len(y_train) == 32
    assert len(y_test) == 8
    assert not set(x_train.index).intersection(x_test.index)
    assert x_train.index.tolist() == result_b[0].index.tolist()
    assert y_train.sum() == 8
    assert y_test.sum() == 2
    assert "customerID" not in x_train.columns
    assert "Churn" not in x_train.columns
    assert x_train.columns.tolist() == list(FEATURE_COLUMNS)


def test_schema_is_not_changed_by_extraction(sample_raw_data):
    data = normalize_dataset(sample_raw_data)
    x, y = features_and_target(data)
    x.loc[0, "gender"] = "Unknown"
    assert data.loc[0, "gender"] != "Unknown"
    assert set(y.unique()) == {0, 1}
