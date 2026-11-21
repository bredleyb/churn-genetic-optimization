"""Métricas de classificação para comparar os modelos no mesmo conjunto de teste."""

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def evaluate_test(model, x_test, y_test) -> dict:
    """Calcula as métricas após o treinamento, sem ajustar o modelo no teste.

    A classe positiva é 1 (cancelamento). A matriz de confusão segue a
    ordem [[VN, FP], [FN, VP]].
    """
    if len(x_test) != len(y_test):
        raise ValueError("Características e respostas do teste têm tamanhos diferentes.")
    if len(y_test) == 0:
        raise ValueError("O conjunto de teste está vazio.")

    predictions = model.predict(x_test)
    matrix = confusion_matrix(y_test, predictions, labels=[0, 1])
    results = {
        "f1": float(f1_score(y_test, predictions, pos_label=1, zero_division=0)),
        "precision": float(precision_score(y_test, predictions, pos_label=1, zero_division=0)),
        "recall": float(recall_score(y_test, predictions, pos_label=1, zero_division=0)),
        "accuracy": float(accuracy_score(y_test, predictions)),
        "matriz_confusao": matrix.astype(int).tolist(),
    }
    if len(np.unique(y_test)) == 2 and hasattr(model, "predict_proba"):
        positive_column = list(model.classes_).index(1)
        probabilities = model.predict_proba(x_test)[:, positive_column]
        results["roc_auc"] = float(roc_auc_score(y_test, probabilities))
    else:
        results["roc_auc"] = None
    return results
