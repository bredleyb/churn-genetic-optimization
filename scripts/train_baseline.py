"""Treina regressão logística de referência e registra validação cruzada.

Uso: python -m scripts.train_baseline
"""

import argparse
import json
from pathlib import Path

from joblib import dump

from src.data import FEATURE_COLUMNS, load_dataset, split_dataset
from src.model import build_classifier, evaluate_cv

DEFAULT_PATH = Path("data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv")


def main() -> None:
    parser = argparse.ArgumentParser(description="Treina o classificador de referência.")
    parser.add_argument("--data", type=Path, default=DEFAULT_PATH, help="Caminho do CSV original")
    parser.add_argument("--output", type=Path, default=Path("results"), help="Pasta de saída")
    args = parser.parse_args()

    data = load_dataset(args.data)
    x_development, x_test, y_development, y_test = split_dataset(data, random_state=42)

    # Todas as métricas abaixo utilizam somente o conjunto de desenvolvimento.
    metrics = evaluate_cv(x_development, y_development, n_splits=3, random_state=42)

    model = build_classifier()
    model.fit(x_development, y_development)

    args.output.mkdir(parents=True, exist_ok=True)
    model_path = args.output / "baseline.joblib"
    report_path = args.output / "baseline_cv.json"
    dump(model, model_path)

    report = {
        "modelo": "Regressão logística",
        "caracteristicas": len(FEATURE_COLUMNS),
        "semente": 42,
        "particoes_validacao": 3,
        "registros_desenvolvimento": len(x_development),
        "registros_teste_reservado": len(x_test),
        "distribuicao_desenvolvimento": {
            "cancelaram": int(y_development.sum()),
            "permaneceram": int((y_development == 0).sum()),
        },
        "metricas_validacao": metrics,
        "observacao": "Conjunto de teste reservado para a comparação final entre modelos.",
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Registros de desenvolvimento: {len(x_development)}")
    print(f"Registros de teste reservados: {len(x_test)}")
    print("Regressão logística — validação cruzada estratificada (3 partições):")
    for name, score in metrics.items():
        print(f"  {name}: {score['media']:.4f} ± {score['desvio_padrao']:.4f}")
    print(f"Modelo treinado: {model_path}")
    print(f"Relatório: {report_path}")


if __name__ == "__main__":
    main()
