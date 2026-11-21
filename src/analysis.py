"""Indicadores descritivos e controles de qualidade dos dados de churn."""

import pandas as pd

from src.data import CATEGORICAL_FEATURES, FEATURE_COLUMNS, NUMERIC_FEATURES


def _numeric_summary(series: pd.Series) -> dict[str, int | float | None]:
    valid = series.dropna()
    if valid.empty:
        return {"validos": 0, "minimo": None, "mediana": None, "media": None, "maximo": None}
    return {
        "validos": len(valid),
        "minimo": float(valid.min()),
        "mediana": float(valid.median()),
        "media": round(float(valid.mean()), 4),
        "maximo": float(valid.max()),
    }


def _churn_by_category(data: pd.DataFrame, column: str) -> list[dict]:
    grouped = data.groupby(column, dropna=False)["Churn"].agg(["size", "sum"])
    rows = []
    for label, row in grouped.iterrows():
        count = int(row["size"])
        cancellations = int(row["sum"])
        rows.append(
            {
                "categoria": str(label) if pd.notna(label) else "(ausente)",
                "clientes": count,
                "cancelamentos": cancellations,
                "taxa_cancelamento_pct": round(100.0 * cancellations / count, 2),
            }
        )
    return sorted(rows, key=lambda value: (-value["clientes"], value["categoria"]))


def profile_dataset(data: pd.DataFrame) -> dict:
    """Resume os dados em estatísticas agregadas, sem incluir identificadores."""
    missing = {col: int(data[col].isna().sum()) for col in data.columns}
    counts = data["Churn"].value_counts().to_dict()
    n = len(data)
    blank_total = data["TotalCharges"].isna()
    numeric = {col: _numeric_summary(data[col]) for col in NUMERIC_FEATURES}
    cardinality = {col: int(data[col].nunique(dropna=True)) for col in CATEGORICAL_FEATURES}

    return {
        "registros": n,
        "colunas": len(data.columns),
        "caracteristicas_candidatas": len(FEATURE_COLUMNS),
        "qualidade": {
            "registros_duplicados": int(data.duplicated().sum()),
            "identificadores_duplicados": int(data["customerID"].duplicated().sum()),
            "ausentes_por_coluna": missing,
            "totalcharges_ausentes_com_tenure_zero": int((blank_total & data["tenure"].eq(0)).sum()),
        },
        "classes": {
            label: {
                "clientes": int(counts.get(value, 0)),
                "percentual": round(100.0 * int(counts.get(value, 0)) / n, 2),
            }
            for label, value in [("No", 0), ("Yes", 1)]
        },
        "variaveis_numericas": numeric,
        "cardinalidade_categoricas": cardinality,
        "cancelamentos_por_contrato": _churn_by_category(data, "Contract"),
        "cancelamentos_por_internet": _churn_by_category(data, "InternetService"),
    }


def profile_as_markdown(profile: dict) -> str:
    """Produz resumo interpretável a partir do mesmo perfil JSON."""
    classes = profile["classes"]
    quality = profile["qualidade"]
    lines = [
        "# Análise exploratória — Telco Customer Churn",
        "",
        "## Dimensões e qualidade dos dados",
        "",
        f"- Registros: **{profile['registros']}**",
        f"- Colunas: **{profile['colunas']}** (19 características candidatas)",
        f"- Registros duplicados: **{quality['registros_duplicados']}**",
        f"- Identificadores duplicados: **{quality['identificadores_duplicados']}**",
        f"- Valores ausentes em `TotalCharges`: **{quality['ausentes_por_coluna']['TotalCharges']}**",
        f"- Desses, com `tenure = 0`: **{quality['totalcharges_ausentes_com_tenure_zero']}**",
        "",
        "## Distribuição da variável Churn",
        "",
        "| Situação | Clientes | Proporção |",
        "|---|---:|---:|",
    ]
    for label, name in [("No", "Permaneceram"), ("Yes", "Cancelaram")]:
        v = classes[label]
        lines.append(f"| {name} | {v['clientes']} | {v['percentual']:.2f}% |")

    for title, key in [
        ("Cancelamentos por tipo de contrato", "cancelamentos_por_contrato"),
        ("Cancelamentos por tipo de internet", "cancelamentos_por_internet"),
    ]:
        lines.extend(
            ["", f"## {title}", "", "| Categoria | Clientes | Cancelamentos | Taxa |", "|---|---:|---:|---:|"]
        )
        for row in profile[key]:
            lines.append(
                f"| {row['categoria']} | {row['clientes']} | {row['cancelamentos']} "
                f"| {row['taxa_cancelamento_pct']:.2f}% |"
            )

    lines.extend(
        [
            "",
            "## Preparação para modelagem",
            "",
            "`customerID` será excluído das características e `Churn` será codificado "
            "como 1 (Yes) ou 0 (No). A coluna `TotalCharges` será convertida "
            "para número, preservando campos vazios como valores ausentes.",
            "",
            "As imputações (mediana numérica e categoria mais frequente), "
            "a codificação one-hot e a padronização serão ajustadas apenas "
            "nos dados de treinamento em cada partição de validação. "
            "O conjunto de teste estratificado (20%) permanecerá reservado.",
            "",
            "As taxas apresentadas são descritivas e não implicam causalidade.",
            "",
        ]
    )
    return "\n".join(lines)
