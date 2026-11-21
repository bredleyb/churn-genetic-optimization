"""Amostra sintética para exercitar a leitura e as transformações."""

import pandas as pd
import pytest

from src.data import FEATURE_COLUMNS


@pytest.fixture
def sample_raw_data() -> pd.DataFrame:
    rows = []
    for i in range(40):
        row = {column: "No" for column in FEATURE_COLUMNS}
        row.update(
            {
                "customerID": f"TESTE-{i:04d}",
                "gender": "Female" if i % 2 else "Male",
                "SeniorCitizen": i % 2,
                "Partner": "Yes" if i % 3 else "No",
                "Dependents": "No",
                "tenure": i % 36,
                "PhoneService": "Yes",
                "MultipleLines": "No",
                "InternetService": "DSL" if i % 2 else "Fiber optic",
                "OnlineSecurity": "Yes",
                "OnlineBackup": "No",
                "DeviceProtection": "No",
                "TechSupport": "Yes",
                "StreamingTV": "No",
                "StreamingMovies": "Yes",
                "Contract": "One year" if i % 2 else "Month-to-month",
                "PaperlessBilling": "Yes",
                "PaymentMethod": "Electronic check",
                "MonthlyCharges": 30 + (i % 8) * 2,
                "TotalCharges": "  " if i == 0 else f"{35 + i * 3:.2f}",
                "Churn": "Yes" if i % 4 == 0 else "No",
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)
