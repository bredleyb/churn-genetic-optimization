"""Compara o modelo de referência e a seleção genética no mesmo teste reservado.

Execução: python -m scripts.compare_models
"""

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from joblib import dump

from src.data import FEATURE_COLUMNS, load_dataset, split_dataset
from src.evaluation import evaluate_test
from src.genetic import GeneticConfig, select_features
from src.model import build_classifier, evaluate_cv

DEFAULT_DATA = Path("data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv")


def make_markdown(report: dict) -> str:
    """Formata os resultados do experimento para leitura e apresentação."""
    base = report["modelos"]["baseline"]["teste"]
    gen = report["modelos"]["genetico"]["teste"]
    names = report["modelos"]["genetico"]["caracteristicas"]
    search = report["busca_genetica"]
    lines = [
        "# Resultados — Previsão de cancelamento de clientes", "",
        "Os dois modelos foram treinados com os 80% reservados ao desenvolvimento e "
        "avaliados no mesmo conjunto de teste (20%).", "",
        "## Comparação no teste", "",
        "| Métrica | Regressão logística | Seleção genética |",
        "|---|---:|---:|",
    ]
    for key, label in [("f1", "F1-score"), ("precision", "Precisão"),
                       ("recall", "Revocação"), ("accuracy", "Acurácia"),
                       ("roc_auc", "ROC-AUC")]:
        b, g = base[key], gen[key]
        lines.append(f"| {label} | {b:.4f} | {g:.4f} |" if b is not None and g is not None
                     else f"| {label} | n.d. | n.d. |")
    lines += [
        "", "## Erros de classificação", "",
        "Matrizes de confusão: [[verdadeiros negativos, falsos positivos], "
        "[falsos negativos, verdadeiros positivos]].", "",
        f"- Referência: {base['matriz_confusao']}",
        f"- Genético: {gen['matriz_confusao']}", "",
        "## Características selecionadas", "",
        f"- Referência: {len(FEATURE_COLUMNS)} atributos originais.",
        f"- Seleção genética: {len(names)} atributos "
        f"(redução de {len(FEATURE_COLUMNS) - len(names)}).",
        "- Selecionados: " + ", ".join(names) + ".",
        f"- F1 médio da referência em validação: "
        f"{report['modelos']['baseline']['f1_cv_media']:.4f}.",
        f"- F1 escolhido pelo algoritmo genético em validação: {search['melhor_f1_cv']:.4f}.",
        f"- Subconjuntos avaliados: {search['subconjuntos_avaliados']}.",
        f"- Tempo de busca: {search['tempo_busca_segundos']:.3f} segundos.",
        "", "## Interpretação e limitações", "",
        "Falsos negativos são cancelamentos não identificados; falsos positivos "
        "são clientes que permaneceram apesar da previsão de cancelamento. "
        "O F1-score da busca pode estar otimista, pois foi maximizado repetidamente "
        "na validação cruzada. O teste separado permite uma comparação independente. "
        "O experimento usa uma única divisão de dados e uma execução genética, "
        "sujeitas à variabilidade. Os resultados não estabelecem causalidade.", "",
    ]
    return "\n".join(lines)


def run(data_path: Path, output_path: Path, *, config: GeneticConfig) -> dict:
    """Usa os dados de teste somente depois da seleção e do treinamento."""
    data = load_dataset(data_path)
    x_dev, x_test, y_dev, y_test = split_dataset(data, random_state=config.random_state)

    print("Validação cruzada do classificador de referência...", flush=True)
    baseline_cv = evaluate_cv(x_dev, y_dev, n_splits=config.cv_folds,
                              random_state=config.random_state)
    print("Busca genética...", flush=True)

    def progress(generation: dict) -> None:
        print(f"Geração {generation['geracao']}: "
              f"F1={generation['melhor_f1_cv']:.4f} | "
              f"atributos={generation['caracteristicas']}", flush=True)

    search = select_features(x_dev, y_dev, config, on_generation=progress)

    baseline = build_classifier()
    genetic = build_classifier(search.selected_features)
    baseline.fit(x_dev, y_dev)
    genetic.fit(x_dev, y_dev)

    # Avaliação final, após a busca, em ambos os modelos e na mesma amostra.
    base_test = evaluate_test(baseline, x_test, y_test)
    gen_test = evaluate_test(genetic, x_test, y_test)
    report = {
        "dados": {"registros": len(data), "desenvolvimento": len(x_dev),
                  "teste": len(x_test), "cancelamentos_no_teste": int(y_test.sum())},
        "configuracao": asdict(config),
        "modelos": {
            "baseline": {"caracteristicas": list(FEATURE_COLUMNS),
                         "f1_cv_media": baseline_cv["f1"]["media"],
                         "metricas_cv": baseline_cv, "teste": base_test},
            "genetico": {"caracteristicas": list(search.selected_features),
                        "teste": gen_test},
        },
        "busca_genetica": {"melhor_f1_cv": search.best_cv_f1,
                          "melhor_aptidao": search.best_fitness,
                          "subconjuntos_avaliados": search.evaluated_subsets,
                          "tempo_busca_segundos": search.elapsed_seconds,
                          "historico": search.history},
    }
    output_path.mkdir(parents=True, exist_ok=True)
    (output_path / "comparacao_modelos.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_path / "comparacao_modelos.md").write_text(make_markdown(report), encoding="utf-8")
    dump(baseline, output_path / "baseline.joblib")
    dump(genetic, output_path / "genetic.joblib")
    print("\nComparação no conjunto de teste:")
    print(f"Referência: F1={base_test['f1']:.4f} | 19 atributos")
    print(f"Genético: F1={gen_test['f1']:.4f} | {len(search.selected_features)} atributos")
    print(f"Relatório: {output_path / 'comparacao_modelos.md'}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Avalia os modelos de previsão de churn.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output", type=Path, default=Path("results"))
    parser.add_argument("--population", type=int, default=24)
    parser.add_argument("--generations", type=int, default=15)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    config = GeneticConfig(population_size=args.population,
                           generations=args.generations, random_state=args.seed)
    config.validate()
    run(args.data, args.output, config=config)


if __name__ == "__main__":
    main()
