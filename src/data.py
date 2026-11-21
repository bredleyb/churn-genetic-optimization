"""Leitura, validação e divisão dos dados Telco Customer Churn."""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


TARGET_COLUMN = "Churn"
ID_COLUMN = "customerID"

# Ordem das características no CSV original; cada coluna equivale a um gene do AG.
FEATURE_COLUMNS = (
    "gender",
    "SeniorCitizen",
    "Partner",
    "Dependents",
    "tenure",
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
    "MonthlyCharges",
    "TotalCharges",
)

NUMERIC_FEATURES = ("tenure", "MonthlyCharges", "TotalCharges")
CATEGORICAL_FEATURES = tuple(
    column for column in FEATURE_COLUMNS if column not in NUMERIC_FEATURES
)
REQUIRED_COLUMNS = (ID_COLUMN, *FEATURE_COLUMNS, TARGET_COLUMN)


def load_dataset(path: str | Path) -> pd.DataFrame:
    """Carrega o CSV original e devolve um DataFrame com tipos normalizados.

    Mantém todas as observações. Valores ausentes são imputados somente no
    pipeline de treinamento, nunca nesta função.
    """
    csv_path = Path(path)
    if not csv_path.is_file():
        raise FileNotFoundError(
            f"CSV não encontrado: {csv_path}. Baixe o conjunto Telco Customer "
            "Churn no Kaggle e salve-o no caminho indicado em data/README.md."
        )

    try:
        raw = pd.read_csv(csv_path, dtype={ID_COLUMN: "string"})
    except (pd.errors.ParserError, UnicodeError, OSError) as exc:
        raise ValueError(f"Não foi possível ler o CSV {csv_path}: {exc}") from exc

    return normalize_dataset(raw)


def normalize_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    """Verifica o esquema e aplica transformações determinísticas aos tipos.

    A função não aprende parâmetros a partir do conjunto de dados; portanto,
    também não calcula médias, medianas ou categorias frequentes.
    """
    if frame.columns.duplicated().any():
        raise ValueError("O CSV contém nomes de colunas duplicados.")

    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError("Colunas obrigatórias ausentes: " + ", ".join(missing))

    extra = sorted(set(frame.columns) - set(REQUIRED_COLUMNS))
    if extra:
        raise ValueError("Colunas inesperadas no CSV: " + ", ".join(extra))

    data = frame.loc[:, list(REQUIRED_COLUMNS)].copy()

    ids = data[ID_COLUMN].astype("string").str.strip()
    if ids.isna().any() or ids.eq("").fillna(False).any():
        raise ValueError("A coluna customerID contém identificadores ausentes.")
    data[ID_COLUMN] = ids

    for column in NUMERIC_FEATURES:
        raw = data[column].astype("string").str.strip()
        blank = raw.isna() | raw.eq("").fillna(False)
        parsed = pd.to_numeric(raw.mask(blank), errors="coerce")
        invalid = ~blank & parsed.isna()
        if invalid.any():
            raise ValueError(
                f"A coluna {column} contém {int(invalid.sum())} valor(es) "
                "não numérico(s) além dos campos vazios."
            )
        data[column] = parsed.astype(float)

    senior = pd.to_numeric(data["SeniorCitizen"], errors="coerce")
    invalid_senior = data["SeniorCitizen"].notna() & ~senior.isin([0, 1])
    if invalid_senior.any():
        raise ValueError("SeniorCitizen deve conter apenas 0 ou 1.")
    data["SeniorCitizen"] = senior.map({0: "0", 1: "1"}).astype(object)

    for column in CATEGORICAL_FEATURES:
        if column == "SeniorCitizen":
            continue
        values = data[column].astype("string").str.strip()
        data[column] = values.mask(values.eq("").fillna(False)).astype(object)
        # np.nan é interpretado de maneira uniforme pelo SimpleImputer.
        data[column] = data[column].where(data[column].notna(), np.nan)

    labels = data[TARGET_COLUMN].astype("string").str.strip()
    invalid_target = ~labels.isin(["Yes", "No"]).fillna(False)
    if invalid_target.any():
        raise ValueError("Churn deve conter apenas 'Yes' ou 'No', sem valores ausentes.")
    data[TARGET_COLUMN] = labels.map({"No": 0, "Yes": 1}).astype(int)

    return data


def features_and_target(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Extrai 19 variáveis preditoras originais e a classificação binária."""
    return data.loc[:, list(FEATURE_COLUMNS)].copy(), data[TARGET_COLUMN].copy()


def split_dataset(
    data: pd.DataFrame,
    *,
    test_size: float = 0.20,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Produz conjuntos de desenvolvimento e teste estratificados e disjuntos.

    O teste deve permanecer fora de toda validação cruzada, seleção de atributos
    ou ajuste de hiperparâmetros.
    """
    duplicated_ids = int(data[ID_COLUMN].duplicated().sum())
    if duplicated_ids:
        raise ValueError(
            f"Há {duplicated_ids} customerID duplicado(s). Resolva-os antes "
            "da divisão para evitar que um cliente apareça nos dois conjuntos."
        )
    x, y = features_and_target(data)
    if y.nunique() != 2 or int(y.value_counts().min()) < 2:
        raise ValueError("A divisão estratificada exige ao menos dois exemplos por classe.")
    if not (0.0 < test_size < 1.0):
        raise ValueError("test_size deve estar entre 0 e 1.")
    return train_test_split(
        x, y, test_size=test_size, random_state=random_state, stratify=y
    )
