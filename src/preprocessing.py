"""Pré-processamento ajustável por característica original selecionada."""

from collections.abc import Iterable

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.data import CATEGORICAL_FEATURES, FEATURE_COLUMNS, NUMERIC_FEATURES


def build_preprocessor(
    selected_features: Iterable[str] | None = None,
) -> ColumnTransformer:
    """Cria um transformador novo, ainda não ajustado aos dados.

    A escolha de uma coluna categórica preserva todas as suas colunas one-hot.
    Para avaliar subconjuntos em CV, instancie e ajuste este transformador
    dentro de cada pipeline/dobra de treinamento.
    """
    if selected_features is None:
        selected = list(FEATURE_COLUMNS)
    else:
        selected = list(selected_features)
        if not selected:
            raise ValueError("É necessário selecionar ao menos uma característica.")
        unknown = sorted(set(selected) - set(FEATURE_COLUMNS))
        if unknown:
            raise ValueError("Características desconhecidas: " + ", ".join(unknown))
        if len(set(selected)) != len(selected):
            raise ValueError("Uma característica foi selecionada mais de uma vez.")

    numerical = [col for col in selected if col in NUMERIC_FEATURES]
    categorical = [col for col in selected if col in CATEGORICAL_FEATURES]
    transformers = []

    if numerical:
        numerical_pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]
        )
        transformers.append(("num", numerical_pipeline, numerical))

    if categorical:
        categorical_pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OneHotEncoder(handle_unknown="ignore")),
            ]
        )
        transformers.append(("cat", categorical_pipeline, categorical))

    return ColumnTransformer(transformers=transformers, remainder="drop")
