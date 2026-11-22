"""Interface local para comparar previsões de cancelamento de clientes.

Execute a partir da raiz: python -m streamlit run streamlit_app.py
"""

import pandas as pd
from html import escape
from pathlib import Path
from time import perf_counter

import streamlit as st

from src.data import FEATURE_COLUMNS, load_dataset, split_dataset
from src.evaluation import evaluate_test
from src.genetic import GeneticConfig, select_features
from src.model import build_classifier, evaluate_cv
from src.prediction import predict_customer
from src.ui_data import (
    BILLING_FEATURES,
    INTERNET_FEATURES,
    LABELS,
    PROFILE_FEATURES,
    PROFILE_FILES,
    align_services,
    format_generation_line,
    format_evaluation_line,
    label_for,
    load_profile,
    model_input,
    options_for,
)

ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "data" / "raw" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"
MODEL_LABELS = {
    "baseline": "Regressão logística",
    "genetico": "Seleção genética",
}
METRIC_LABELS = {
    "f1": "F1-score",
    "precision": "Precisão",
    "recall": "Revocação",
    "accuracy": "Acurácia",
    "roc_auc": "ROC-AUC",
}

st.set_page_config(
    page_title="Previsão de cancelamento | Projeto N3",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Estilos limitados aos elementos HTML próprios e a um contêiner com chave pública.
st.markdown(
    """
<style>
.st-key-churn-shell {margin-inline: auto;}
.churn-header {margin: 0 0 20px;}
.churn-title {font-family: inherit; font-size: clamp(27px, 2.7vw, 34px);
  line-height: 1.17; font-weight: 680; letter-spacing: -.033em; color: #0F172A;
  margin: 0 0 8px;}
.churn-subtitle {font-family: inherit; font-size: 14px; line-height: 1.5;
  color: #516071; margin: 0; max-width: 680px;}
.churn-heading {font-family: inherit; font-size: 18px; line-height: 1.35;
  font-weight: 650; color: #0F172A; margin: 0 0 10px;}
.churn-help {font-family: inherit; font-size: 13px; line-height: 1.45;
  color: #516071; margin: -4px 0 12px;}
.churn-result {border: 1px solid #E2E8F0; background: #FFFFFF; border-radius: 10px;
  padding: 18px 20px 16px; margin: 10px 0;}
.churn-result-top {display: flex; gap: 12px; align-items: flex-start;
  justify-content: space-between;}
.churn-model {font-family: inherit; font-size: 14px; font-weight: 650;
  line-height: 1.4; color: #0F172A;}
.churn-detail {font-family: inherit; font-size: 12px; line-height: 1.4;
  color: #516071; margin-top: 3px;}
.churn-value {font-family: inherit; font-size: clamp(25px, 2.6vw, 34px);
  font-weight: 700; line-height: 1.1; letter-spacing: -.035em;
  font-variant-numeric: tabular-nums; white-space: nowrap;}
.churn-meter {width: 100%; height: 7px; border-radius: 20px;
  background: #E2E8F0; overflow: hidden; margin: 16px 0 10px;}
.churn-meter > span {display: block; height: 100%; border-radius: 20px;}
.churn-status {font-family: inherit; font-size: 12px; font-weight: 650; line-height: 1.4;}
.churn-comparison {margin: 26px 0 0;}
.churn-compare-grid {display: grid; grid-template-columns: repeat(auto-fit, minmax(165px, 1fr));
  gap: 12px; margin: 12px 0;}
.churn-compare-item {background: #F1F5F9; border-radius: 9px; padding: 15px 17px;}
.churn-compare-label {font-family: inherit; font-size: 12px; line-height: 1.4;
  color: #516071; margin-bottom: 6px;}
.churn-compare-value {font-family: inherit; font-size: 25px; line-height: 1.2;
  font-weight: 680; letter-spacing: -.025em; font-variant-numeric: tabular-nums;
  color: #0F172A;}
.churn-compare-detail {font-family: inherit; font-size: 12px;
  line-height: 1.45; color: #516071; margin-top: 6px;}
.churn-note {font-family: inherit; font-size: 12px; line-height: 1.5;
  color: #516071; margin: 8px 0 16px;}
.churn-metrics {width: 100%; border-collapse: collapse; font-family: inherit;
  font-size: 13px; line-height: 1.4; font-variant-numeric: tabular-nums;}
.churn-metrics th {font-size: 12px; font-weight: 650; text-align: right;
  color: #516071; padding: 10px 7px; border-bottom: 1px solid #E2E8F0;}
.churn-metrics td {text-align: right; padding: 10px 7px;
  color: #0F172A; border-bottom: 1px solid #E2E8F0;}
.churn-metrics th:first-child, .churn-metrics td:first-child {text-align: left;}
.churn-metrics tr:last-child td {border-bottom: none;}
@media (max-width: 768px) {
  .churn-header {margin-bottom: 14px;}
  .churn-result {padding: 15px;}
  .churn-comparison {margin-top: 18px;}
}
@media (max-width: 430px) {
  .churn-result-top {gap: 9px;}
  .churn-value {font-size: 25px;}
  .churn-model {font-size: 13px;}
  .churn-compare-grid {grid-template-columns: 1fr;}
  .churn-metrics {font-size: 12px;}
  .churn-metrics th, .churn-metrics td {padding: 9px 4px;}
}

/* Monitor do algoritmo: classes próprias, sem dependências do DOM do Streamlit. */
.churn-console {border:1px solid #334155; border-radius:10px; background:#111827;
  color:#CBD5E1; margin:12px 0 14px; overflow:hidden;}
.churn-console-head {display:flex; justify-content:space-between; align-items:center;
  border-bottom:1px solid #334155; padding:11px 15px; font:600 12px/1.4 ui-monospace,monospace;}
.churn-console-head small {font:400 11px/1.4 ui-monospace,monospace; color:#94A3B8;}
.churn-console-lines {padding:12px 15px; max-height:215px; min-height:84px;
  overflow-y:auto; overflow-wrap:anywhere; font:12px/1.65 ui-monospace,monospace;}
.churn-log-line {display:block; white-space:pre-wrap;}
.churn-log-line.is-step {color:#5EEAD4;}
.churn-log-line.is-result {color:#FFFFFF;}
.churn-chromosome {border:1px solid #E2E8F0; border-radius:9px; padding:13px 15px;
  margin:12px 0; background:#FFFFFF;}
.churn-chromosome-head {display:flex; justify-content:space-between; gap:8px;
  align-items:baseline; margin:0 0 11px; font-size:12px; color:#516071;}
.churn-bits {display:grid; grid-template-columns:repeat(19,minmax(0,22px)); gap:3px; max-width:472px;}
.churn-bit {display:flex; height:29px; border-radius:4px; align-items:center;
  justify-content:center; font:600 11px/1 ui-monospace,monospace;
  background:#E2E8F0; color:#516071;}
.churn-bit.is-on {background:#0F766E; color:#FFFFFF;}
.churn-legend {font:11px/1.4 inherit; color:#516071; margin-top:10px;}
@media (max-width:430px) {
  .churn-console-lines {padding:10px 11px; font-size:11px; max-height:175px;}
  .churn-chromosome {padding:12px 10px;}
  .churn-bits {grid-template-columns:repeat(19,minmax(0,1fr)); gap:2px;}
  .churn-bit {height:25px; font-size:10px;}
}
</style>
""",
    unsafe_allow_html=True,
)


def _apply_profile(profile_name: str) -> None:
    example = load_profile(ROOT, profile_name)
    for feature in FEATURE_COLUMNS:
        st.session_state[f"field_{feature}"] = example[feature]
    st.session_state["field_total_missing"] = example["total_missing"]
    st.session_state["workflow_run"] = None


def _choose_profile() -> None:
    _apply_profile(st.session_state["profile_choice"])


def _reset_profile() -> None:
    _apply_profile(st.session_state["profile_choice"])


def _on_service_change(feature: str) -> None:
    snapshot = {name: st.session_state[f"field_{name}"] for name in FEATURE_COLUMNS}
    revised = align_services(snapshot, changed=feature)
    for name in (("MultipleLines",) if feature == "PhoneService" else INTERNET_FEATURES):
        st.session_state[f"field_{name}"] = revised[name]


def _form_data() -> dict:
    data = {name: st.session_state[f"field_{name}"] for name in FEATURE_COLUMNS}
    data["total_missing"] = st.session_state["field_total_missing"]
    return data


def _select_field(feature: str, *, disabled: bool = False, help_text: str | None = None) -> None:
    callback = _on_service_change if feature in ("InternetService", "PhoneService") else None
    st.selectbox(
        LABELS[feature],
        options_for(feature),
        format_func=label_for,
        key=f"field_{feature}",
        on_change=callback,
        args=(feature,),
        disabled=disabled,
        help=help_text,
    )


def _render_result(title: str, entry: dict, *, feature_count: int | None) -> None:
    probability = max(0.0, min(100.0, float(entry["probabilidade_cancelamento"]) * 100))
    cancellation = entry["classe"] == 1
    color = "#B42318" if cancellation else "#0F766E"
    status = "Cancelamento previsto" if cancellation else "Permanência prevista"
    detail = f"{feature_count} características" if feature_count is not None else "Modelo treinado"
    formatted = f"{probability:.2f}".replace(".", ",")
    st.markdown(
        f"""<section class="churn-result" aria-label="{escape(title)}">
<div class="churn-result-top"><div><div class="churn-model">{escape(title)}</div>
<div class="churn-detail">{escape(detail)}</div></div>
<div class="churn-value" style="color:{color}">{formatted}%</div></div>
<div class="churn-meter" role="progressbar" aria-label="Probabilidade estimada de cancelamento"
  aria-valuemin="0" aria-valuemax="100" aria-valuenow="{probability:.2f}">
<span style="width:{probability:.2f}%;background:{color}"></span></div>
<div class="churn-status" style="color:{color}">{status}</div></section>""",
        unsafe_allow_html=True,
    )


def _render_metrics(summary: dict) -> None:
    base = summary["baseline"]
    genetic = summary["genetico"]
    baseline_f1 = f"{base['f1']:.4f}".replace(".", ",")
    genetic_f1 = f"{genetic['f1']:.4f}".replace(".", ",")
    reduction = f"{summary['reduction_pct']:.2f}".replace(".", ",")
    difference = abs(base["f1"] - genetic["f1"])
    difference_label = f"{difference:.4f}".replace(".", ",")
    direction = "redução" if genetic["f1"] < base["f1"] else "aumento"
    if genetic["f1"] == base["f1"]:
        change = "F1-score equivalente no conjunto de teste."
    else:
        change = f"{direction} de {difference_label} no F1-score."

    st.markdown(
        "<section class='churn-comparison' aria-label='Comparação dos modelos'>"
        "<h2 class='churn-heading'>Comparação dos modelos</h2>"
        "<div class='churn-compare-grid'>"
        f"<div class='churn-compare-item'><div class='churn-compare-label'>Referência</div>"
        f"<div class='churn-compare-value'>{baseline_f1}</div>"
        f"<div class='churn-compare-detail'>F1-score · {summary['baseline_count']} características</div></div>"
        f"<div class='churn-compare-item'><div class='churn-compare-label'>Seleção genética</div>"
        f"<div class='churn-compare-value'>{genetic_f1}</div>"
        f"<div class='churn-compare-detail'>F1-score · {summary['genetic_count']} características</div></div>"
        "</div>"
        f"<p class='churn-note'>{reduction}% menos características; {change}</p>"
        "</section>",
        unsafe_allow_html=True,
    )

    with st.expander("Ver todas as métricas"):
        rows = "".join(
            "<tr><td>" + name + "</td>"
            f"<td>{base[key]:.4f}</td><td>{genetic[key]:.4f}</td></tr>"
            for key, name in METRIC_LABELS.items()
        ).replace(".", ",")
        st.markdown(
            "<table class='churn-metrics'><thead><tr><th scope='col'>Métrica</th>"
            "<th scope='col'>Referência</th><th scope='col'>Genético</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>",
            unsafe_allow_html=True,
        )
        test_count = f"{summary['test_count']:,}".replace(",", ".")
        st.caption(f"Conjunto de teste reservado: {test_count} clientes. "
                   "As probabilidades individuais utilizam limiar de classificação de 50%.")



def _history_chart(history: list[dict], *, slot=None) -> None:
    """Exibe F1 do indivíduo com melhor aptidão, por geração real."""
    chart_data = pd.DataFrame({
        "Geração": [int(item["geracao"]) for item in history],
        "F1 em validação cruzada": [float(item["melhor_f1_cv"]) for item in history],
    })
    target = slot if slot is not None else st
    target.line_chart(
        chart_data, x="Geração", y="F1 em validação cruzada",
        color="#0F766E", height=230,
    )


def _render_console(lines: list[str], *, slot=None, complete: bool = False) -> None:
    """Exibe apenas eventos recebidos da execução, com saída monoespaçada."""
    # Mostra os eventos mais recentes enquanto executa; o registro inteiro fica disponível ao terminar.
    visible = lines if complete else lines[-8:]
    rows = []
    for line in visible:
        if " | F1" in line or line.startswith("[FIM]"):
            kind = "is-result"
        elif "avaliando" in line or line.startswith("[GERAÇÃO]"):
            kind = "is-step"
        else:
            kind = ""
        rows.append(f'<span class="churn-log-line {kind}">{escape(line)}</span>')
    markup = (
        '<section class="churn-console" aria-label="Eventos da busca genética">'
        '<div class="churn-console-head"><span>Monitor de execução</span>'
        '<small>Eventos reais</small></div>'
        '<div class="churn-console-lines" role="log" aria-live="polite">'
        + "".join(rows) + '</div></section>'
    )
    (slot or st).markdown(markup, unsafe_allow_html=True)


def _render_chromosome(chromosome: tuple[int, ...], title: str, *, slot=None) -> None:
    """Mostra os 19 genes referentes às características originais."""
    bits = "".join(
        f'<span class="churn-bit {"is-on" if bit else ""}" '
        f'title="{escape(LABELS[feature])} — {"incluída" if bit else "excluída"}"'
        f'>{int(bit)}</span>'
        for feature, bit in zip(FEATURE_COLUMNS, chromosome)
    )
    markup = (
        '<section class="churn-chromosome" aria-label="Cromossomo de 19 características">'
        f'<div class="churn-chromosome-head"><strong>{escape(title)}</strong>'
        f'<span>{sum(chromosome)} de {len(FEATURE_COLUMNS)} características</span></div>'
        f'<div class="churn-bits">{bits}</div>'
        '<div class="churn-legend">1 = incluída &nbsp;·&nbsp; 0 = excluída</div>'
        '</section>'
    )
    (slot or st).markdown(markup, unsafe_allow_html=True)


def _render_finished_run(run: dict) -> None:
    """Mantém na coluna direita o processamento e a previsão da última execução."""
    _render_console(run["events"], complete=True)
    _render_chromosome(run["chromosome"], "Melhor cromossomo encontrado")
    st.markdown("**F1-score durante a seleção genética**")
    _history_chart(run["history"])
    elapsed = f"{run['elapsed_seconds']:.1f}".replace(".", ",")
    st.caption(
        f"Execução concluída · {run['evaluated_subsets']} subconjuntos avaliados · "
        f"{len(run['history'])} gerações · {elapsed} s"
    )
    current = None
    try:
        current = model_input(_form_data())
    except ValueError:
        pass
    if current != run["customer"]:
        st.info("Os dados do cliente foram alterados. Clique em Calcular previsão "
                "para executar novamente com os valores atuais.")
        return
    st.markdown("<h2 class='churn-heading'>Previsão</h2>", unsafe_allow_html=True)
    st.caption("Probabilidade estimada de cancelamento para o cliente informado.")
    for name, title in MODEL_LABELS.items():
        feature_count = run["summary"]["baseline_count" if name == "baseline" else "genetic_count"]
        _render_result(title, run["predictions"][name], feature_count=feature_count)
    _render_metrics(run["summary"])


def _execute_full_workflow(customer: dict) -> None:
    """Treina, seleciona, avalia e prevê em um único clique, com eventos reais."""
    config = GeneticConfig()
    start = perf_counter()
    events: list[str] = []
    history: list[dict] = []
    stage_slot = st.empty()
    progress_slot = st.empty()
    console_slot = st.empty()
    chromosome_slot = st.empty()
    st.markdown("**F1-score durante a seleção genética**")
    chart_slot = st.empty()

    def log(message: str) -> None:
        events.append(message)
        _render_console(events, slot=console_slot)

    def phase(label: str, message: str) -> None:
        stage_slot.caption(label)
        log(message)

    def on_evaluation(record: dict[str, object]) -> None:
        if record["etapa"] == "inicio":
            chromosome = tuple(int(bit) for bit in record["cromossomo"])
            _render_chromosome(
                chromosome,
                f"Geração {record['geracao']} · indivíduo {record['individuo']}",
                slot=chromosome_slot,
            )
        log(format_evaluation_line(record))

    def on_generation(record: dict[str, int | float]) -> None:
        history.append(dict(record))
        number = int(record["geracao"])
        stage_slot.caption(f"Seleção genética · geração {number} de {config.generations}")
        progress_slot.progress(number / config.generations,
                               text=f"Geração {number}/{config.generations}")
        log("[GERAÇÃO] " + format_generation_line(record))
        _history_chart(history, slot=chart_slot)

    progress_slot.progress(0.0, text=f"Geração 0/{config.generations}")
    try:
        phase("Preparando o experimento...", "[DADOS] Lendo o conjunto Telco Customer Churn")
        dataset = load_dataset(DATASET)
        x_dev, x_test, y_dev, y_test = split_dataset(
            dataset, random_state=config.random_state
        )
        log(f"[DIVISÃO] {len(dataset)} clientes · {len(x_dev)} desenvolvimento · "
            f"{len(x_test)} teste reservado")
        phase("Validando o classificador de referência...",
              f"[CV] Regressão logística · {config.cv_folds} partições")
        baseline_cv = evaluate_cv(x_dev, y_dev, n_splits=config.cv_folds,
                                  random_state=config.random_state)
        log(f"[CV] F1 médio de referência: {baseline_cv['f1']['media']:.4f}")
        phase("Avaliando subconjuntos com algoritmo genético...",
              f"[AG] {config.population_size} indivíduos · "
              f"{config.generations} gerações · {len(FEATURE_COLUMNS)} genes")
        genetic_result = select_features(
            x_dev, y_dev, config,
            on_generation=on_generation,
            on_evaluation=on_evaluation,
        )
        phase("Treinando os dois classificadores...",
              "[TREINO] Ajustando os modelos com os dados de desenvolvimento")
        baseline = build_classifier()
        selected = build_classifier(genetic_result.selected_features)
        baseline.fit(x_dev, y_dev)
        selected.fit(x_dev, y_dev)
        phase("Avaliando no conjunto de teste reservado...",
              f"[TESTE] Calculando métricas nos mesmos {len(x_test)} casos reservados")
        base_metrics = evaluate_test(baseline, x_test, y_test)
        genetic_metrics = evaluate_test(selected, x_test, y_test)
        phase("Calculando previsão do cliente...",
              "[PREVISÃO] Aplicando os dois modelos treinados ao cliente informado")
        predictions = {
            "baseline": predict_customer(baseline, customer),
            "genetico": predict_customer(selected, customer),
        }
        log(f"[FIM] Referência F1={base_metrics['f1']:.4f} · "
            f"Genético F1={genetic_metrics['f1']:.4f} · "
            f"{genetic_result.evaluated_subsets} subconjuntos distintos")
    except (OSError, ValueError, RuntimeError, ImportError) as exc:
        st.session_state["workflow_run"] = None
        stage_slot.error("Execução interrompida")
        st.error(f"Não foi possível concluir o processamento: {exc}")
        return

    progress_slot.progress(1.0, text=f"{config.generations} gerações concluídas")
    stage_slot.success("Execução concluída")
    summary = {
        "baseline": base_metrics,
        "genetico": genetic_metrics,
        "baseline_count": len(FEATURE_COLUMNS),
        "genetic_count": len(genetic_result.selected_features),
        "test_count": len(x_test),
        "reduction_pct": 100 * (len(FEATURE_COLUMNS) - len(genetic_result.selected_features))
                         / len(FEATURE_COLUMNS),
    }
    result = {
        "customer": customer,
        "predictions": predictions,
        "summary": summary,
        "history": history,
        "chromosome": genetic_result.chromosome,
        "events": events,
        "evaluated_subsets": genetic_result.evaluated_subsets,
        "elapsed_seconds": perf_counter() - start,
    }
    st.session_state["workflow_run"] = result
    st.caption(f"{genetic_result.evaluated_subsets} subconjuntos distintos avaliados.")
    st.markdown("<h2 class='churn-heading'>Previsão</h2>", unsafe_allow_html=True)
    st.caption("Probabilidade estimada de cancelamento para o cliente informado.")
    for name, title in MODEL_LABELS.items():
        count = summary["baseline_count" if name == "baseline" else "genetic_count"]
        _render_result(title, predictions[name], feature_count=count)
    _render_metrics(summary)


def main() -> None:
    with st.container(key="churn-shell", width=1240):
        st.markdown(
            "<header class='churn-header'><h1 class='churn-title'>Previsão de cancelamento</h1>"
            "<p class='churn-subtitle'>Configure o cliente e acompanhe o treinamento, "
            "a seleção genética e a previsão em tempo real.</p></header>",
            unsafe_allow_html=True,
        )

        if "form_initialized" not in st.session_state:
            st.session_state["profile_choice"] = next(iter(PROFILE_FILES))
            _apply_profile(st.session_state["profile_choice"])
            st.session_state["form_initialized"] = True

        layout = st.grid(2, min_column_width=440, gap=20, wrap=True)
        panel_form = layout.cell()
        panel_result = layout.cell()

        with panel_form:
            with st.container(border=True):
                st.markdown("<h2 class='churn-heading'>Cliente</h2>", unsafe_allow_html=True)
                st.selectbox(
                    "Perfil de exemplo", list(PROFILE_FILES), key="profile_choice",
                    on_change=_choose_profile,
                )
                st.button("Restaurar exemplo", on_click=_reset_profile, type="tertiary")

                quick_a, quick_b = st.columns(2, gap="small", wrap=True)
                with quick_a:
                    st.number_input(LABELS["tenure"], min_value=0, step=1, key="field_tenure")
                    _select_field("InternetService")
                with quick_b:
                    _select_field("Contract")
                    st.number_input(LABELS["MonthlyCharges"], min_value=0.0,
                                    step=1.0, format="%.2f", key="field_MonthlyCharges")

                with st.expander("Perfil"):
                    a, b = st.columns(2, gap="small", wrap=True)
                    with a:
                        _select_field(PROFILE_FEATURES[0])
                        _select_field(PROFILE_FEATURES[1])
                    with b:
                        _select_field(PROFILE_FEATURES[2])
                        _select_field(PROFILE_FEATURES[3])

                with st.expander("Telefonia"):
                    _select_field("PhoneService")
                    _select_field("MultipleLines", disabled=st.session_state["field_PhoneService"] == "No",
                                  help_text="Indisponível quando o cliente não possui telefone.")

                with st.expander("Serviços de internet"):
                    inactive = st.session_state["field_InternetService"] == "No"
                    ia, ib = st.columns(2, gap="small", wrap=True)
                    for i, feature in enumerate(INTERNET_FEATURES):
                        with (ia if i % 2 == 0 else ib):
                            _select_field(feature, disabled=inactive,
                                          help_text="Indisponível sem serviço de internet.")

                with st.expander("Cobrança e pagamento"):
                    _select_field(BILLING_FEATURES[0])
                    _select_field(BILLING_FEATURES[1])
                    st.checkbox("Total cobrado indisponível", key="field_total_missing")
                    st.number_input(
                        LABELS["TotalCharges"], min_value=0.0, step=1.0, format="%.2f",
                        key="field_TotalCharges", disabled=st.session_state["field_total_missing"],
                    )
                    st.caption("Valores monetários na unidade utilizada pelo conjunto de dados.")

                clicked = st.button("Calcular previsão", type="primary",
                                    use_container_width=True, disabled=not DATASET.is_file())
                st.caption("O cálculo executa novamente o treinamento e a busca genética.")
                if not DATASET.is_file():
                    st.info("CSV não encontrado em `data/raw/`. Coloque o dataset original "
                            "nessa pasta para executar a previsão.")

        with panel_result:
            st.markdown("<h2 class='churn-heading'>Execução e previsão</h2>",
                        unsafe_allow_html=True)
            if clicked:
                st.session_state["workflow_run"] = None
                try:
                    customer = model_input(_form_data())
                except ValueError as exc:
                    st.error(f"Dados do cliente inválidos: {exc}")
                else:
                    _execute_full_workflow(customer)
            elif st.session_state.get("workflow_run") is not None:
                _render_finished_run(st.session_state["workflow_run"])
            else:
                st.caption("Clique em Calcular previsão para iniciar. "
                           "O processamento será acompanhado nesta coluna.")
                _render_console(["[PRONTO] Aguardando execução do experimento"])


if __name__ == "__main__":
    main()
