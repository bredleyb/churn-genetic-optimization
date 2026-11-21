"""Prevê o cancelamento de um novo cliente usando modelos já treinados.

Exemplo: python -m scripts.predict --cliente examples/cliente_exemplo.json --modelo ambos
"""

import argparse
import json
from pathlib import Path

from joblib import load

from src.prediction import predict_customer, prepare_customer


MODELS = {
    "baseline": ("Regressão logística de referência", "baseline.joblib"),
    "genetico": ("Regressão logística com seleção genética", "genetic.joblib"),
}


def run(client_path: Path, results_path: Path, model_name: str) -> dict:
    """Lê um novo perfil e aplica um ou ambos os modelos salvos em disco."""
    try:
        client = json.loads(client_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Arquivo do cliente não encontrado: {client_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON inválido em {client_path}: {exc.msg}") from exc

    prepare_customer(client)  # Verifica a entrada antes de carregar os modelos.
    if model_name not in (*MODELS, "ambos"):
        raise ValueError(f"Modelo desconhecido: {model_name}")
    selected = list(MODELS) if model_name == "ambos" else [model_name]
    for name in selected:
        model_path = results_path / MODELS[name][1]
        if not model_path.is_file():
            raise ValueError(
                f"Modelo não encontrado: {model_path}. "
                "Execute primeiro 'python -m scripts.compare_models' "
                "para treinar e salvar ambos os modelos."
            )

    results = {}
    for name in selected:
        description, filename = MODELS[name]
        # Arquivos joblib devem ser carregados apenas quando gerados pelo próprio projeto.
        model = load(results_path / filename)
        prediction = predict_customer(model, client)
        results[name] = prediction
        print(f"\nModelo: {description}")
        print(f"Previsão: {prediction['previsao']}")
        print(f"Probabilidade estimada de cancelamento: "
              f"{prediction['probabilidade_cancelamento'] * 100:.2f}%")

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Prevê cancelamento para um novo cliente.")
    parser.add_argument(
        "--cliente", type=Path, default=Path("examples/cliente_exemplo.json"),
        help="Arquivo JSON com os dados de um novo cliente",
    )
    parser.add_argument(
        "--modelo", choices=["baseline", "genetico", "ambos"], default="ambos",
        help="Modelo a utilizar (padrão: ambos)",
    )
    parser.add_argument(
        "--resultados", type=Path, default=Path("results"),
        help="Diretório onde foram salvos os classificadores",
    )
    args = parser.parse_args()
    try:
        run(args.cliente, args.resultados, args.modelo)
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Erro: {exc}\n")


if __name__ == "__main__":
    main()
