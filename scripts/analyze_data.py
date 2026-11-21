"""Gera os perfis JSON e Markdown a partir do CSV Telco Customer Churn.

Uso: python -m scripts.analyze_data --data data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv
"""

import argparse
import json
from pathlib import Path

from src.analysis import profile_as_markdown, profile_dataset
from src.data import load_dataset, split_dataset

DEFAULT_PATH = Path("data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analisa a base Telco Customer Churn.")
    parser.add_argument("--data", type=Path, default=DEFAULT_PATH, help="Caminho do CSV original")
    parser.add_argument(
        "--output", type=Path, default=Path("results"), help="Diretório para relatórios"
    )
    args = parser.parse_args()

    data = load_dataset(args.data)
    profile = profile_dataset(data)
    # A mesma divisão será usada pelos modelos; o script apenas confere os tamanhos.
    x_train, x_test, y_train, y_test = split_dataset(data)
    profile["divisao"] = {
        "semente": 42,
        "teste_percentual": 20,
        "desenvolvimento_registros": len(x_train),
        "teste_registros": len(x_test),
        "desenvolvimento_churn": int(y_train.sum()),
        "teste_churn": int(y_test.sum()),
    }

    args.output.mkdir(parents=True, exist_ok=True)
    json_path = args.output / "analise_dados.json"
    md_path = args.output / "analise_dados.md"
    json_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(profile_as_markdown(profile), encoding="utf-8")
    print(f"Dados: {profile['registros']} registros, {profile['colunas']} colunas")
    print(f"Churn: {profile['classes']['Yes']['clientes']} clientes ({profile['classes']['Yes']['percentual']}%)")
    print(f"Desenvolvimento: {len(x_train)} | Teste: {len(x_test)}")
    print(f"Relatórios: {json_path} e {md_path}")


if __name__ == "__main__":
    main()
