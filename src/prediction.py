"""Validação de novos clientes e previsão de cancelamento."""

import math

import pandas as pd

from src.data import FEATURE_COLUMNS

# Categorias utilizadas pela base Telco Customer Churn.
VALID_CATEGORIES = {
    "gender": ("Female", "Male"),
    "SeniorCitizen": ("0", "1"),
    "Partner": ("No", "Yes"),
    "Dependents": ("No", "Yes"),
    "PhoneService": ("No", "Yes"),
    "MultipleLines": ("No", "No phone service", "Yes"),
    "InternetService": ("DSL", "Fiber optic", "No"),
    "OnlineSecurity": ("No", "No internet service", "Yes"),
    "OnlineBackup": ("No", "No internet service", "Yes"),
    "DeviceProtection": ("No", "No internet service", "Yes"),
    "TechSupport": ("No", "No internet service", "Yes"),
    "StreamingTV": ("No", "No internet service", "Yes"),
    "StreamingMovies": ("No", "No internet service", "Yes"),
    "Contract": ("Month-to-month", "One year", "Two year"),
    "PaperlessBilling": ("No", "Yes"),
    "PaymentMethod": (
        "Bank transfer (automatic)",
        "Credit card (automatic)",
        "Electronic check",
        "Mailed check",
    ),
}


def prepare_customer(customer: dict) -> pd.DataFrame:
    """Valida 19 características originais e cria uma linha para o modelo.

    TotalCharges pode ser nulo, pois o pré-processador já prevê imputação.
    Os nomes das demais categorias seguem os valores originais do dataset.
    """
    if not isinstance(customer, dict):
        raise ValueError("O cliente deve ser um objeto JSON com as 19 características.")

    missing = [name for name in FEATURE_COLUMNS if name not in customer]
    extra = sorted(set(customer) - set(FEATURE_COLUMNS))
    if missing:
        raise ValueError("Características ausentes: " + ", ".join(missing))
    if extra:
        raise ValueError("Características desconhecidas: " + ", ".join(extra))

    validated, errors = validate_customer_values(customer)
    if errors:
        raise ValueError(next(iter(errors.values())))
    return pd.DataFrame([validated], columns=FEATURE_COLUMNS)


def validate_customer_values(customer: dict) -> tuple[dict, dict[str, str]]:
    """Valida valores e dependências, acumulando erros por característica.

    O chamador de domínio verifica o esquema completo. O formulário pode
    apresentar todos os erros da mesma validação, inclusive de abas ocultas.
    """
    validated = {}
    errors = {}
    for name in FEATURE_COLUMNS:
        if name not in customer:
            errors[name] = f"Característica ausente: {name}."
            continue
        value = customer[name]
        if name in VALID_CATEGORIES:
            if name == "SeniorCitizen" and type(value) is int and value in (0, 1):
                value = str(value)
            if not isinstance(value, str) or value not in VALID_CATEGORIES[name]:
                expected = ", ".join(repr(item) for item in VALID_CATEGORIES[name])
                errors[name] = f"Valor inválido para {name}: {value!r}. Aceitos: {expected}"
                continue
        elif name == "TotalCharges" and value is None:
            value = float("nan")
        else:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                errors[name] = f"{name} deve ser um número não negativo."
                continue
            if not math.isfinite(value) or value < 0:
                errors[name] = f"{name} deve ser um número não negativo e finito."
                continue
            if name == "tenure" and not float(value).is_integer():
                errors[name] = "tenure deve representar uma quantidade inteira de meses."
                continue
        validated[name] = value

    if "PhoneService" in validated and "MultipleLines" in validated:
        if validated["PhoneService"] == "No" and validated["MultipleLines"] != "No phone service":
            errors["MultipleLines"] = "MultipleLines deve ser 'No phone service' quando não há telefone."
        if validated["PhoneService"] == "Yes" and validated["MultipleLines"] == "No phone service":
            errors["MultipleLines"] = "MultipleLines é incompatível com PhoneService='Yes'."

    internet_dependent = (
        "OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport",
        "StreamingTV", "StreamingMovies",
    )
    if "InternetService" in validated:
        without_internet = validated["InternetService"] == "No"
        for name in internet_dependent:
            if name in validated:
                is_unavailable = validated[name] == "No internet service"
                if without_internet != is_unavailable:
                    errors[name] = f"{name} é incompatível com InternetService."

    return validated, errors


def predict_customer(model, customer: dict) -> dict:
    """Obtém classificação e probabilidade da classe 1 (cancelamento)."""
    x_customer = prepare_customer(customer)
    classes = list(model.classes_)
    if 1 not in classes:
        raise ValueError("O classificador não contém a classe de cancelamento (1).")
    prediction = int(model.predict(x_customer)[0])
    probability = float(model.predict_proba(x_customer)[0, classes.index(1)])
    return {
        "classe": prediction,
        "previsao": "Cancelamento" if prediction == 1 else "Permanência",
        "probabilidade_cancelamento": probability,
    }
