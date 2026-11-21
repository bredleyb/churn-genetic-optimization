"""Seleciona atributos por algoritmo genético e treina o classificador.

Uso: python -m scripts.run_genetic
"""

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from joblib import dump

from src.data import load_dataset, split_dataset
from src.genetic import GeneticConfig, select_features
from src.model import build_classifier

DEFAULT_PATH = Path("data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seleciona atributos por algoritmo genético.")
    parser.add_argument("--data", type=Path, default=DEFAULT_PATH, help="Caminho do CSV")
    parser.add_argument("--output", type=Path, default=Path("results"), help="Pasta de saída")
    parser.add_argument("--population", type=int, default=24, help="Tamanho da população")
    parser.add_argument("--generations", type=int, default=15, help="Número de gerações")
    parser.add_argument("--seed", type=int, default=42, help="Semente da divisão e da busca")
    args = parser.parse_args()

    data = load_dataset(args.data)
    x_dev, x_test, y_dev, _ = split_dataset(data, random_state=args.seed)
    config = GeneticConfig(
        population_size=args.population,
        generations=args.generations,
        random_state=args.seed,
    )
    print("Algoritmo genético — F1-score em validação cruzada (3 partições)", flush=True)

    def progress(record: dict[str, int | float]) -> None:
        print(
            f"Geração {int(record['geracao']):2d}: "
            f"F1={record['melhor_f1_cv']:.4f} | "
            f"aptidão={record['melhor_aptidao']:.4f} | "
            f"atributos={int(record['caracteristicas'])}",
            flush=True,
        )

    result = select_features(x_dev, y_dev, config, on_generation=progress)
    model = build_classifier(result.selected_features)
    model.fit(x_dev, y_dev)

    args.output.mkdir(parents=True, exist_ok=True)
    model_path = args.output / "genetic.joblib"
    report_path = args.output / "genetic_selection.json"
    dump(model, model_path)
    report = {
        "metodo": "Seleção de características por algoritmo genético com regressão logística",
        "parametros": asdict(config),
        "registros_desenvolvimento": len(x_dev),
        "registros_teste_reservado": len(x_test),
        "atributos_selecionados": list(result.selected_features),
        "quantidade_atributos": len(result.selected_features),
        "cromossomo": list(result.chromosome),
        "melhor_f1_cv": result.best_cv_f1,
        "melhor_aptidao": result.best_fitness,
        "subconjuntos_avaliados": result.evaluated_subsets,
        "tempo_busca_segundos": result.elapsed_seconds,
        "historico": result.history,
        "observacao": "Conjunto de teste reservado para comparação final.",
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Atributos selecionados: " + ", ".join(result.selected_features))
    print(f"Subconjuntos avaliados: {result.evaluated_subsets}")
    print(f"Tempo de busca: {result.elapsed_seconds:.1f} s")
    print(f"Modelo treinado: {model_path}")
    print(f"Relatório: {report_path}")


if __name__ == "__main__":
    main()
