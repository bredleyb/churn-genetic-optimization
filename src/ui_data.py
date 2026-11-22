"""Conversão dos perfis e rótulos para a interface de previsão."""

import json
from pathlib import Path

from src.data import FEATURE_COLUMNS
from src.prediction import VALID_CATEGORIES, prepare_customer


PROFILE_FILES = {
    "Exemplo 1": "cliente_exemplo.json",
    "Exemplo 2": "cliente_exemplo_2.json",
}

LABELS = {
    "gender": "Gênero",
    "SeniorCitizen": "Pessoa idosa",
    "Partner": "Possui parceiro(a)",
    "Dependents": "Possui dependentes",
    "tenure": "Tempo como cliente",
    "PhoneService": "Serviço de telefone",
    "MultipleLines": "Múltiplas linhas telefônicas",
    "InternetService": "Serviço de internet",
    "OnlineSecurity": "Segurança online",
    "OnlineBackup": "Backup online",
    "DeviceProtection": "Proteção de dispositivos",
    "TechSupport": "Suporte técnico",
    "StreamingTV": "Streaming de TV",
    "StreamingMovies": "Streaming de filmes",
    "Contract": "Tipo de contrato",
    "PaperlessBilling": "Fatura digital",
    "PaymentMethod": "Método de pagamento",
    "MonthlyCharges": "Cobrança mensal",
    "TotalCharges": "Total cobrado",
}

OPTION_LABELS = {
    "Yes": "Sim",
    "No": "Não",
    "0": "Não",
    "1": "Sim",
    "Female": "Feminino",
    "Male": "Masculino",
    "No phone service": "Sem serviço telefônico",
    "No internet service": "Sem serviço de internet",
    "DSL": "DSL",
    "Fiber optic": "Fibra óptica",
    "Month-to-month": "Mensal",
    "One year": "Anual",
    "Two year": "Bienal",
    "Electronic check": "Cheque eletrônico",
    "Mailed check": "Cheque enviado pelo correio",
    "Bank transfer (automatic)": "Transferência bancária automática",
    "Credit card (automatic)": "Cartão de crédito automático",
}

INTERNET_FEATURES = (
    "OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport",
    "StreamingTV", "StreamingMovies",
)

QUICK_FEATURES = ("tenure", "Contract", "InternetService", "MonthlyCharges")
PROFILE_FEATURES = ("gender", "SeniorCitizen", "Partner", "Dependents")
PHONE_FEATURES = ("PhoneService", "MultipleLines")
BILLING_FEATURES = ("PaperlessBilling", "PaymentMethod", "TotalCharges")

assert set(LABELS) == set(FEATURE_COLUMNS)


def options_for(feature: str) -> tuple[str, ...]:
    """Retorna categorias aceitas pelo modelo, na ordem definida na base."""
    return VALID_CATEGORIES[feature]


def label_for(value: str) -> str:
    """Exibe categorias em português preservando o código usado no modelo."""
    return OPTION_LABELS.get(value, value)


def load_profile(root: Path, name: str) -> dict:
    """Carrega um cliente fictício, convertido para os tipos dos controles."""
    try:
        path = root / "examples" / PROFILE_FILES[name]
    except KeyError as exc:
        raise ValueError(f"Perfil desconhecido: {name}") from exc
    customer = json.loads(path.read_text(encoding="utf-8"))
    prepare_customer(customer)
    result = dict(customer)
    result["SeniorCitizen"] = str(result["SeniorCitizen"])
    result["total_missing"] = result["TotalCharges"] is None
    if result["TotalCharges"] is None:
        result["TotalCharges"] = 0.0
    return result


def align_services(customer: dict, *, changed: str) -> dict:
    """Ajusta valores dependentes quando o tipo de serviço é alterado."""
    result = customer.copy()
    if changed == "PhoneService":
        if result["PhoneService"] == "No":
            result["MultipleLines"] = "No phone service"
        elif result["MultipleLines"] == "No phone service":
            result["MultipleLines"] = "No"
    if changed == "InternetService":
        if result["InternetService"] == "No":
            for feature in INTERNET_FEATURES:
                result[feature] = "No internet service"
        else:
            for feature in INTERNET_FEATURES:
                if result[feature] == "No internet service":
                    result[feature] = "No"
    return result


def model_input(form_values: dict) -> dict:
    """Monta as 19 entradas do modelo e valida combinações/tipos."""
    missing = set(FEATURE_COLUMNS) - set(form_values)
    if missing:
        raise ValueError("Campos não preenchidos: " + ", ".join(sorted(missing)))
    result = {feature: form_values[feature] for feature in FEATURE_COLUMNS}
    result["TotalCharges"] = None if form_values.get("total_missing") else result["TotalCharges"]
    # A validação da aplicação é a mesma utilizada pela CLI.
    prepare_customer(result)
    return result


def experiment_summary(report: dict) -> dict:
    """Extrai métricas reais do JSON produzido em scripts.compare_models."""
    try:
        base = report["modelos"]["baseline"]
        gen = report["modelos"]["genetico"]
        metrics = ("f1", "precision", "recall", "accuracy", "roc_auc")
        for entry in (base, gen):
            if not all(isinstance(entry["teste"][key], (int, float)) for key in metrics):
                raise ValueError("Métricas experimentais ausentes ou inválidas.")
        total = len(base["caracteristicas"])
        chosen = len(gen["caracteristicas"])
        test_count = int(report["dados"]["teste"])
        if not 0 < chosen <= total or test_count < 1:
            raise ValueError("Quantidades de características ou registros inconsistentes.")
    except (KeyError, TypeError) as exc:
        raise ValueError("Relatório experimental incompleto.") from exc
    return {
        "baseline": {key: base["teste"][key] for key in metrics},
        "genetico": {key: gen["teste"][key] for key in metrics},
        "baseline_count": total,
        "genetic_count": chosen,
        "test_count": test_count,
        "reduction_pct": 100 * (total - chosen) / total,
        "selected_features": list(gen["caracteristicas"]),
    }


def format_generation_line(record: dict) -> str:
    """Formata somente medições reais informadas pelo algoritmo genético."""
    generation = int(record["geracao"])
    f1 = f"{float(record['melhor_f1_cv']):.4f}".replace(".", ",")
    fitness = f"{float(record['melhor_aptidao']):.4f}".replace(".", ",")
    count = int(record["caracteristicas"])
    return (f"Geração {generation:02d} | F1 (CV): {f1} | "
            f"aptidão: {fitness} | características: {count}")


def format_evaluation_line(event: dict[str, object]) -> str:
    """Formata eventos reais de início e conclusão de uma validação cruzada."""
    generation = int(event["geracao"])
    individual = int(event["individuo"])
    population = int(event["populacao"])
    count = len(event["caracteristicas"])
    if event["etapa"] == "inicio":
        folds = int(event["dobras"])
        return (f"[G{generation:02d}] indivíduo {individual:02d}/{population} | "
                f"avaliando {count}/19 características | CV: {folds} partições")
    if event["etapa"] == "fim":
        f1 = f"{float(event['f1_cv']):.4f}".replace(".", ",")
        fitness = f"{float(event['aptidao']):.4f}".replace(".", ",")
        evaluated = int(event["avaliados"])
        return (f"[G{generation:02d}] indivíduo {individual:02d}/{population} | "
                f"F1: {f1} | aptidão: {fitness} | subconjunto {evaluated}")
    raise ValueError("Etapa de avaliação desconhecida.")
