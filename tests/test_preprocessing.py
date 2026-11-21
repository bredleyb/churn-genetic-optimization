import numpy as np
import pytest
from sklearn.exceptions import NotFittedError

from src.data import FEATURE_COLUMNS, normalize_dataset, split_dataset
from src.preprocessing import build_preprocessor


def test_preprocessing_is_created_unfitted(sample_raw_data):
    data = normalize_dataset(sample_raw_data)
    x_train, x_test, *_ = split_dataset(data)
    processor = build_preprocessor()
    with pytest.raises(NotFittedError):
        processor.transform(x_test)

    train_array = processor.fit_transform(x_train)
    test_array = processor.transform(x_test)
    assert train_array.shape[0] == 32
    assert test_array.shape[0] == 8
    assert train_array.shape[1] == test_array.shape[1]
    assert np.isfinite(train_array).all()
    assert np.isfinite(test_array).all()
    assert not set(processor.get_feature_names_out()).intersection({"customerID", "Churn"})


def test_selected_categorical_feature_keeps_onehot_group(sample_raw_data):
    data = normalize_dataset(sample_raw_data)
    x_train, x_test, *_ = split_dataset(data)
    processor = build_preprocessor(["Contract", "tenure"])
    transformed = processor.fit_transform(x_train)
    names = processor.get_feature_names_out().tolist()
    assert transformed.shape[1] == 3  # 1 tenure + 2 categorias observadas de Contract
    assert "num__tenure" in names
    assert "cat__Contract_One year" in names
    assert "cat__Contract_Month-to-month" in names
    assert processor.transform(x_test).shape[1] == 3


def test_missing_numeric_imputation_is_fit_on_train_only(sample_raw_data):
    data = normalize_dataset(sample_raw_data)
    x_train, x_test, *_ = split_dataset(data)
    processor = build_preprocessor(["TotalCharges"])
    processor.fit(x_train)
    expected_median = x_train["TotalCharges"].median()
    observed_median = processor.named_transformers_["num"].named_steps["imputer"].statistics_[0]
    assert observed_median == expected_median
    assert processor.transform(x_test).shape == (8, 1)


def test_unknown_categories_are_accepted(sample_raw_data):
    data = normalize_dataset(sample_raw_data)
    x_train, *_ = split_dataset(data)
    processor = build_preprocessor(["Contract"])
    processor.fit(x_train)
    unseen = x_train.iloc[[0]].copy()
    unseen["Contract"] = "Outro contrato"
    arr = processor.transform(unseen)
    assert arr.shape == (1, 2)
    assert np.asarray(arr).sum() == 0  # handle_unknown='ignore'


def test_invalid_selected_feature_sets():
    with pytest.raises(ValueError, match="ao menos uma"):
        build_preprocessor([])
    with pytest.raises(ValueError, match="desconhecidas"):
        build_preprocessor(["customerID"])
    with pytest.raises(ValueError, match="mais de uma vez"):
        build_preprocessor(["Contract", "Contract"])
    assert len(FEATURE_COLUMNS) == 19
