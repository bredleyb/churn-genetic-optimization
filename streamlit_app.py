"""Interface local para comparar previsões de cancelamento de clientes.

Execute a partir da raiz: python -m streamlit run streamlit_app.py
"""

import json

import pandas as pd
from html import escape
from pathlib import Path

import streamlit as st
from joblib import load

from src.data import FEATURE_COLUMNS, load_dataset, split_dataset
from src.genetic import GeneticConfig, select_features
from src.prediction import predict_customer
from src.ui_data import (
    BILLING_FEATURES,
    INTERNET_FEATURES,
    LABELS,
    PROFILE_FEATURES,
    PROFILE_FILES,
    align_services,
    experiment_summary,
    format_generation_line,
    format_evaluation_line,
    label_for,
    load_profile,
    model_input,
    options_for,
)

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
DATASET = ROOT / "data" / "raw" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"
MODEL_NAMES = {
    "baseline": ("Regressão logística", "baseline.joblib"),
    "genetico": ("Seleção genética", "genetic.joblib"),
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


@st.cache_resource(show_spinner=False)
def cached_model(file_path: str, modified_ns: int, file_size: int):
    """Recarrega o modelo quando o arquivo local é substituído."""
    return load(file_path)


@st.cache_data(show_spinner=False)
def cached_report(file_path: str, modified_ns: int, file_size: int):
    return json.loads(Path(file_path).read_text(encoding="utf-8"))


def _file_version(path: Path) -> tuple[str, int, int]:
    info = path.stat()
    return str(path), info.st_mtime_ns, info.st_size


def _apply_profile(profile_name: str) -> None:
    example = load_profile(ROOT, profile_name)
    for feature in FEATURE_COLUMNS:
        st.session_state[f"field_{feature}"] = example[feature]
    st.session_state["field_total_missing"] = example["total_missing"]
    st.session_state["last_prediction"] = None
    st.session_state["preview_requested"] = True


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


def _calculate_prediction() -> None:
    """Atualiza a previsão usando o mesmo caminho de validação da CLI."""
    try:
        customer = model_input(_form_data())
        predictions = {}
        for name, (_, filename) in MODEL_NAMES.items():
            path = RESULTS / filename
            model = cached_model(*_file_version(path))
            predictions[name] = predict_customer(model, customer)
        st.session_state["last_prediction"] = {
            "customer": customer,
            "predictions": predictions,
        }
    except (ValueError, OSError, ImportError, KeyError) as exc:
        st.session_state["last_prediction"] = None
        st.error(f"Não foi possível calcular a previsão: {exc}")


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


def _render_console(lines: list[str], *, slot=None) -> None:
    """Exibe apenas eventos recebidos da execução, com saída monoespaçada."""
    visible = lines[-12:]
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


def _render_search_result(run: dict) -> None:
    """Exibe a execução real concluída, antes do gráfico de evolução."""
    result = run["result"]
    elapsed = f"{result.elapsed_seconds:.1f}".replace(".", ",")
    st.caption(
        f"Última execução nesta sessão · {result.evaluated_subsets} subconjuntos distintos · "
        f"{elapsed} s"
    )
    _render_console(run["events"])
    _render_chromosome(result.chromosome, "Melhor cromossomo encontrado")
    _history_chart(run["history"])
    chosen = ", ".join(LABELS[name] for name in result.selected_features)
    st.caption(f"Características selecionadas: {chosen}.")
    if st.toggle("Mostrar registro completo da execução", key="full_search_log"):
        st.code("\n".join(run["events"]), language=None, height=230, wrap_lines=True)


def _render_saved_history() -> None:
    """Histórico do treinamento principal já salvo; não executa nova busca."""
    path = RESULTS / "comparacao_modelos.json"
    if not path.is_file():
        st.caption("O histórico estará disponível após executar o experimento principal.")
        return
    try:
        report = cached_report(*_file_version(path))
        history = report["busca_genetica"]["historico"]
        selected = report["modelos"]["genetico"]["caracteristicas"]
        if not isinstance(history, list) or not history:
            raise ValueError("Histórico vazio")
        st.caption("Histórico registrado no experimento principal — sem processamento em andamento.")
        _history_chart(history)
        st.caption(
            f"{len(history)} gerações · {len(selected)} características selecionadas · "
            f"{report['busca_genetica']['subconjuntos_avaliados']} subconjuntos distintos"
        )
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError):
        st.warning("O histórico experimental não pôde ser carregado.")


def _run_search() -> None:
    """Monitora avaliações reais sem treinar novamente os modelos salvos."""
    config = GeneticConfig()
    history: list[dict] = []
    events = ["[INÍCIO] Preparando execução da seleção genética"]
    with st.status("Preparando os dados...", expanded=True) as status:
        progress = st.progress(0, text=f"0 de {config.generations} gerações")
        console_slot = st.empty()
        chromosome_slot = st.empty()
        chart_slot = st.empty()
        _render_console(events, slot=console_slot)

        def on_evaluation(record: dict[str, object]) -> None:
            # 'inicio' ocorre imediatamente antes da CV, 'fim' depois do cálculo.
            chromosome = tuple(record["cromossomo"])
            if record["etapa"] == "inicio":
                _render_chromosome(
                    chromosome,
                    f"Geração {record['geracao']} · indivíduo {record['individuo']}",
                    slot=chromosome_slot,
                )
            events.append(format_evaluation_line(record))
            _render_console(events, slot=console_slot)

        def on_generation(record: dict) -> None:
            history.append(dict(record))
            number = int(record["geracao"])
            progress.progress(number / config.generations,
                              text=f"{number} de {config.generations} gerações")
            status.update(label=f"Busca genética — geração {number}/{config.generations}")
            events.append("[GERAÇÃO] " + format_generation_line(record))
            _render_console(events, slot=console_slot)
            _history_chart(history, slot=chart_slot)

        try:
            dataset = load_dataset(DATASET)
            x_dev, x_test, y_dev, _ = split_dataset(
                dataset, random_state=config.random_state
            )
            events.extend([
                f"[DADOS] {len(dataset)} registros carregados; {len(x_dev)} para desenvolvimento",
                f"[TESTE] {len(x_test)} registros reservados, fora da seleção",
                f"[CONFIG] {config.population_size} indivíduos · {config.generations} gerações · "
                f"CV com {config.cv_folds} partições",
            ])
            _render_console(events, slot=console_slot)
            status.update(label="Avaliando subconjuntos de características...")
            result = select_features(
                x_dev, y_dev, config,
                on_generation=on_generation, on_evaluation=on_evaluation,
            )
            events.append(
                f"[FIM] {result.evaluated_subsets} subconjuntos distintos · "
                f"{len(result.selected_features)} características selecionadas"
            )
            _render_console(events, slot=console_slot)
            status.update(label="Busca genética concluída", state="complete", expanded=False)
        except (OSError, ValueError) as exc:
            status.update(label="Erro na busca genética", state="error", expanded=True)
            st.error(f"Não foi possível executar a busca: {exc}")
            return

    st.session_state["genetic_run"] = {
        "history": history, "events": events, "result": result,
    }
    _render_search_result(st.session_state["genetic_run"])


def _render_search_monitor() -> None:
    """Detalhes técnicos recolhidos, com histórico e reexecução opcionais."""
    with st.expander("Evolução do algoritmo genético", expanded=False):
        st.caption("15 gerações · 24 indivíduos · validação cruzada em 3 partições.")
        if not DATASET.is_file():
            st.info("Para executar novamente, coloque o CSV original em "
                    "`data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv`.")
        clicked = st.button(
            "Executar novamente a busca", type="secondary",
            disabled=not DATASET.is_file(),
        )
        if clicked:
            st.session_state.pop("genetic_run", None)
            _run_search()
        elif st.session_state.get("genetic_run"):
            _render_search_result(st.session_state["genetic_run"])
        else:
            _render_saved_history()


def main() -> None:
    with st.container(key="churn-shell", width=1240):
        st.markdown(
            "<header class='churn-header'><h1 class='churn-title'>Previsão de cancelamento</h1>"
            "<p class='churn-subtitle'>Compare as previsões de dois modelos a partir "
            "dos dados de um cliente.</p></header>",
            unsafe_allow_html=True,
        )

        if "form_initialized" not in st.session_state:
            st.session_state["profile_choice"] = next(iter(PROFILE_FILES))
            _apply_profile(st.session_state["profile_choice"])
            st.session_state["form_initialized"] = True

        model_ready = all((RESULTS / filename).is_file() for _, filename in MODEL_NAMES.values())
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

                clicked = st.button("Atualizar previsão", type="primary",
                                    use_container_width=True, disabled=not model_ready)
                if not model_ready:
                    st.info("Modelos não encontrados. Execute `python -m scripts.compare_models` no terminal.")
                elif clicked or st.session_state.get("preview_requested", False):
                    st.session_state["preview_requested"] = False
                    _calculate_prediction()

        with panel_result:
            st.markdown(
                "<h2 class='churn-heading'>Previsão</h2>"
                "<p class='churn-help'>Probabilidade estimada de cancelamento</p>",
                unsafe_allow_html=True,
            )
            last = st.session_state.get("last_prediction")
            try:
                current = model_input(_form_data())
            except ValueError:
                current = None
            if last is not None and current != last["customer"]:
                st.caption("Dados alterados — atualize a previsão.")
            elif last is not None:
                summary_for_counts = None
                path = RESULTS / "comparacao_modelos.json"
                if path.is_file():
                    try:
                        summary_for_counts = experiment_summary(cached_report(*_file_version(path)))
                    except (ValueError, json.JSONDecodeError, OSError):
                        pass
                for name, (label, _) in MODEL_NAMES.items():
                    count = None
                    if summary_for_counts:
                        count = summary_for_counts["baseline_count" if name == "baseline" else "genetic_count"]
                    _render_result(label, last["predictions"][name], feature_count=count)
            elif model_ready:
                st.caption("Atualize a previsão para visualizar os resultados.")
            else:
                st.caption("Os resultados aparecerão após o treinamento dos modelos.")

            report_path = RESULTS / "comparacao_modelos.json"
            if report_path.is_file():
                try:
                    _render_metrics(experiment_summary(cached_report(*_file_version(report_path))))
                except (ValueError, OSError, json.JSONDecodeError):
                    st.warning("Relatório experimental incompleto. "
                               "Execute `python -m scripts.compare_models` novamente.")
            else:
                st.markdown("<h2 class='churn-heading'>Comparação dos modelos</h2>",
                            unsafe_allow_html=True)
                st.caption("As métricas serão exibidas após o treinamento.")

        st.divider()
        _render_search_monitor()


if __name__ == "__main__":
    main()
