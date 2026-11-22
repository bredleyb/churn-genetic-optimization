"""Dashboard local da previsão de churn e da execução genética reproduzível.

Execute: python -m streamlit run streamlit_app.py
"""

from html import escape
from pathlib import Path
from time import perf_counter

import pandas as pd
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
    format_evaluation_line,
    format_generation_line,
    label_for,
    load_profile,
    model_input,
    options_for,
)

ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "data" / "raw" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"

st.set_page_config(
    page_title="Previsão de cancelamento | Projeto N3",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
/* Estrutura do dashboard, antes da identidade visual escura. */
html, body, #root {overflow:hidden!important;}
[data-testid="stHeader"] {display:none!important;}
[data-testid="stMain"] {height:100dvh!important;overflow:hidden!important;}
[data-testid="stMainBlockContainer"] {max-width:none!important;height:100dvh!important;padding:10px 18px 0!important;overflow:hidden!important;}
.st-key-dashboard-shell {height:calc(100dvh - 20px);max-width:1640px;margin:auto;overflow:hidden;}
.churn-topbar {height:52px;display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;}
.churn-topbar h1 {font-size:20px;line-height:1.2;font-weight:650;margin:0;}
.churn-top-meta {font-size:12px;}
.st-key-dashboard-client, .st-key-dashboard-workspace {height:calc(100dvh - 88px)!important;min-height:0!important;overflow:hidden!important;}
.st-key-dashboard-client-fields {height:calc(100dvh - 248px)!important;min-height:0!important;overflow-y:auto!important;}
.st-key-dashboard-client-footer {padding-top:10px;}
.churn-kpis {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;}
.churn-kpi {border:1px solid #94A3B8;padding:10px;border-radius:8px;min-width:0;}
.churn-kpi-label,.churn-kpi-foot {font-size:11px;}
.churn-kpi-value {font-size:20px;font-weight:700;}
.churn-console {border:1px solid #334155;min-width:0;}
.churn-console-head {font-size:11px;padding:8px;display:flex;justify-content:space-between;}
.churn-console-lines {height:192px;overflow-y:auto;overflow-wrap:anywhere;padding:9px;font:11px/1.5 monospace;}
.churn-log-line {display:block;white-space:pre-wrap;}
.churn-chromosome {border:1px solid #94A3B8;padding:10px;margin-top:5px;}
.churn-chromosome-head {display:flex;justify-content:space-between;font-size:11px;}
.churn-bits {display:grid;grid-template-columns:repeat(19,minmax(0,1fr));gap:2px;}
.churn-bit {height:22px;min-width:0;text-align:center;background:#CBD5E1;}
.churn-bit.is-on {background:#0F766E;color:white;}
.churn-mini-heading {font-size:11px;margin-bottom:5px;}
.churn-chart-fallback {height:175px;display:grid;place-items:center;}
.churn-tech {display:grid;grid-template-columns:1fr 1fr;gap:6px;}
.churn-tech-item {padding:10px;border:1px solid #94A3B8;}
.churn-tech-item span {display:block;font-size:11px;}
.churn-tech-item strong {font-size:17px;}
@media(max-width:900px) {
 [data-testid="stMainBlockContainer"] {padding:7px 10px 0!important;}
 .churn-topbar {height:44px;margin-bottom:6px;}
 .st-key-dashboard-client,.st-key-dashboard-workspace {height:calc(100dvh - 68px)!important;}
 .st-key-dashboard-client-fields {height:calc(100dvh - 228px)!important;}
 .churn-kpis {grid-template-columns:repeat(2,minmax(0,1fr));}
 .churn-bits {grid-template-columns:repeat(10,minmax(0,1fr));}
}
@media(max-width:620px) {
 .st-key-dashboard-client {height:calc(43dvh - 27px)!important;}
 .st-key-dashboard-client-fields {height:calc(43dvh - 142px)!important;}
 .st-key-dashboard-workspace {height:calc(57dvh - 62px)!important;overflow-y:auto!important;}
 .churn-kpis {grid-template-columns:repeat(4,minmax(0,1fr));}
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
        LABELS[feature], options_for(feature), format_func=label_for,
        key=f"field_{feature}", on_change=callback, args=(feature,),
        disabled=disabled, help=help_text,
    )


def _render_client_details() -> None:
    tab = st.segmented_control(
        "Características adicionais",
        ["Perfil", "Telefonia", "Internet", "Cobrança"],
        default="Perfil", key="detail_tab", required=True,
        label_visibility="collapsed", width="stretch",
    )
    if tab == "Perfil":
        a, b = st.columns(2, gap="small", wrap=True)
        with a:
            _select_field(PROFILE_FEATURES[0])
            _select_field(PROFILE_FEATURES[1])
        with b:
            _select_field(PROFILE_FEATURES[2])
            _select_field(PROFILE_FEATURES[3])
    elif tab == "Telefonia":
        _select_field("PhoneService")
        _select_field(
            "MultipleLines", disabled=st.session_state["field_PhoneService"] == "No",
            help_text="Indisponível quando o cliente não possui telefone.",
        )
    elif tab == "Internet":
        inactive = st.session_state["field_InternetService"] == "No"
        a, b = st.columns(2, gap="small", wrap=True)
        for i, feature in enumerate(INTERNET_FEATURES):
            with (a if i % 2 == 0 else b):
                _select_field(feature, disabled=inactive,
                              help_text="Indisponível sem serviço de internet.")
    else:
        _select_field(BILLING_FEATURES[0])
        _select_field(BILLING_FEATURES[1])
        st.checkbox("Total cobrado indisponível", key="field_total_missing")
        st.number_input(
            LABELS["TotalCharges"], min_value=0.0, step=1.0,
            format="%.2f", key="field_TotalCharges",
            disabled=st.session_state["field_total_missing"],
        )


def _current_customer() -> dict | None:
    try:
        return model_input(_form_data())
    except ValueError:
        return None


def _is_stale(run: dict) -> bool:
    return _current_customer() != run["customer"]


def _format_probability(entry: dict) -> tuple[str, str, str]:
    probability = max(0, min(100, float(entry["probabilidade_cancelamento"]) * 100))
    label = "Cancelamento" if entry["classe"] == 1 else "Permanência"
    style = "is-high" if entry["classe"] == 1 else "is-low"
    return f"{probability:.2f}".replace(".", ",") + "%", label, style


def _render_kpis(run: dict | None, status: str, *, slot) -> None:
    if run is not None and status == "complete":
        bval, bfoot, bstyle = _format_probability(run["predictions"]["baseline"])
        gval, gfoot, gstyle = _format_probability(run["predictions"]["genetico"])
        count = str(run["summary"]["genetic_count"]) + "/19"
    else:
        bval = gval = "—"
        bfoot = gfoot = "Aguardando previsão"
        bstyle = gstyle = ""
        count = "—/19"
    states = {
        "idle": ("Pronto", "Inicie pelo painel Cliente"),
        "running": ("Em execução", "Busca genética em andamento"),
        "complete": ("Concluído", "Modelos avaliados"),
        "stale": ("Alterado", "Previsão desatualizada"),
        "error": ("Erro", "Verifique o registro"),
    }
    state_label, state_detail = states[status]
    def card(label: str, value: str, foot: str, style: str = "") -> str:
        return (f'<div class="churn-kpi"><div class="churn-kpi-label">{escape(label)}</div>'
                f'<div class="churn-kpi-value {style}">{escape(value)}</div>'
                f'<div class="churn-kpi-foot">{escape(foot)}</div></div>')
    html = ('<section class="churn-kpis" aria-label="Indicadores principais">'
            + card("Referência", bval, bfoot, bstyle)
            + card("Seleção genética", gval, gfoot, gstyle)
            + card("Características", count, "Atributos selecionados")
            + card("Processamento", state_label, state_detail)
            + '</section>')
    slot.markdown(html, unsafe_allow_html=True)


def _render_console(events: list[str], *, slot, complete: bool = False) -> None:
    # Registro integral permanece em memória; o monitor mostra as últimas linhas.
    visible = events[-22:] if complete else events[-9:]
    rows = []
    for line in visible:
        kind = ("is-result" if " | F1" in line or line.startswith("[FIM]")
                else "is-step" if "avaliando" in line or line.startswith("[GERAÇÃO]")
                else "")
        rows.append(f'<span class="churn-log-line {kind}">{escape(line)}</span>')
    markup = ('<section class="churn-console" aria-label="Eventos da busca genética">'
              '<div class="churn-console-head"><span>Monitor de execução</span>'
              '<small>EVENTOS REAIS</small></div>'
              '<div class="churn-console-lines" role="log" aria-live="polite">'
              + "".join(rows) + '</div></section>')
    slot.markdown(markup, unsafe_allow_html=True)


def _render_chromosome(chromosome: tuple[int, ...], title: str, *, slot) -> None:
    bits = "".join(
        f'<span class="churn-bit {"is-on" if bit else ""}" '
        f'title="{escape(LABELS[name])} — {"incluída" if bit else "excluída"}">'
        f'{int(bit)}</span>'
        for name, bit in zip(FEATURE_COLUMNS, chromosome)
    )
    markup = ('<section class="churn-chromosome" aria-label="Cromossomo de 19 características">'
              f'<div class="churn-chromosome-head"><strong>{escape(title)}</strong>'
              f'<span>{sum(chromosome)}/19</span></div>'
              f'<div class="churn-bits">{bits}</div>'
              '<div class="churn-legend">1 incluída · 0 excluída</div></section>')
    slot.markdown(markup, unsafe_allow_html=True)


def _history_chart(history: list[dict], *, slot) -> None:
    if not history:
        slot.markdown('<div class="churn-chart-fallback">Aguardando a primeira geração</div>',
                      unsafe_allow_html=True)
        return
    chart_data = pd.DataFrame({
        "Geração": [int(item["geracao"]) for item in history],
        "F1 (CV)": [float(item["melhor_f1_cv"]) for item in history],
    })
    slot.line_chart(chart_data, x="Geração", y="F1 (CV)",
                    color="#30B6A7", height=175)


def _render_technical(run: dict | None, *, slot, stale: bool = False) -> None:
    if run is None:
        metrics = (("F1 referência", "—"), ("F1 genético", "—"),
                   ("Subconjuntos", "—"), ("Tempo", "—"))
    else:
        s = run["summary"]
        metrics = (("F1 referência", f'{s["baseline"]["f1"]:.4f}'.replace(".", ",")),
                   ("F1 genético", f'{s["genetico"]["f1"]:.4f}'.replace(".", ",")),
                   ("Subconjuntos", str(run["evaluated_subsets"])),
                   ("Tempo", f'{run["elapsed_seconds"]:.1f}'.replace(".", ",") + " s"))
    cells = "".join(
        f'<div class="churn-tech-item"><span>{escape(name)}</span><strong>{escape(value)}</strong></div>'
        for name, value in metrics
    )
    foot = '<div class="churn-tech-foot">F1 calculado no teste reservado · 20% dos dados</div>'
    warning = ('<div class="churn-stale">Os dados do cliente foram alterados. '
               'Clique em Calcular previsão para atualizar.</div>') if stale else ""
    slot.markdown(f'<section aria-label="Resumo técnico"><div class="churn-tech">{cells}'
                  f'</div>{foot}{warning}</section>', unsafe_allow_html=True)


def _render_idle(slots: dict) -> None:
    _render_kpis(None, "idle", slot=slots["kpis"])
    slots["phase"].markdown('<div class="churn-ready">Aguardando cálculo do cliente</div>', unsafe_allow_html=True)
    slots["progress"].progress(0.0, text="Geração 0/15")
    _render_console(["[PRONTO] Aguardando execução do experimento"], slot=slots["console"])
    _render_chromosome(tuple(0 for _ in FEATURE_COLUMNS), "Aguardando avaliação", slot=slots["chromosome"])
    _history_chart([], slot=slots["chart"])
    _render_technical(None, slot=slots["technical"])


def _render_finished_run(run: dict, slots: dict) -> None:
    stale = _is_stale(run)
    _render_kpis(run, "stale" if stale else "complete", slot=slots["kpis"])
    slots["phase"].markdown('<div class="churn-phase">Execução concluída · '
                            f'{len(run["history"])} gerações</div>', unsafe_allow_html=True)
    slots["progress"].progress(1.0, text="Geração 15/15")
    _render_console(run["events"], slot=slots["console"], complete=True)
    _render_chromosome(run["chromosome"], "Melhor cromossomo", slot=slots["chromosome"])
    _history_chart(run["history"], slot=slots["chart"])
    _render_technical(run, slot=slots["technical"], stale=stale)


def _execute_full_workflow(customer: dict, slots: dict) -> None:
    """Execução completa ao clicar em Calcular previsão; não altera arquivos salvos."""
    config = GeneticConfig()
    started = perf_counter()
    events: list[str] = []
    history: list[dict] = []
    _render_kpis(None, "running", slot=slots["kpis"])
    slots["progress"].progress(0.0, text=f"Geração 0/{config.generations}")
    _render_chromosome(tuple(0 for _ in FEATURE_COLUMNS), "Aguardando avaliação",
                       slot=slots["chromosome"])
    _history_chart([], slot=slots["chart"])
    _render_technical(None, slot=slots["technical"])

    def log(message: str) -> None:
        events.append(message)
        _render_console(events, slot=slots["console"])

    def phase(label: str, message: str) -> None:
        slots["phase"].markdown(f'<div class="churn-phase">{escape(label)}</div>',
                                unsafe_allow_html=True)
        log(message)

    def on_evaluation(record: dict[str, object]) -> None:
        if record["etapa"] == "inicio":
            chromosome = tuple(int(bit) for bit in record["cromossomo"])
            _render_chromosome(
                chromosome,
                f"Geração {record['geracao']} · indivíduo {record['individuo']}",
                slot=slots["chromosome"],
            )
        log(format_evaluation_line(record))

    def on_generation(record: dict[str, int | float]) -> None:
        history.append(dict(record))
        number = int(record["geracao"])
        slots["phase"].markdown(
            f'<div class="churn-phase">Seleção genética · geração {number} de '
            f'{config.generations}</div>', unsafe_allow_html=True,
        )
        slots["progress"].progress(number / config.generations,
                                   text=f"Geração {number}/{config.generations}")
        log("[GERAÇÃO] " + format_generation_line(record))
        _history_chart(history, slot=slots["chart"])

    try:
        phase("Preparando os dados", "[DADOS] Lendo o conjunto Telco Customer Churn")
        dataset = load_dataset(DATASET)
        x_dev, x_test, y_dev, y_test = split_dataset(
            dataset, random_state=config.random_state,
        )
        log(f"[DIVISÃO] {len(dataset)} clientes · {len(x_dev)} desenvolvimento · "
            f"{len(x_test)} teste reservado")
        phase("Validando a referência",
              f"[CV] Regressão logística · {config.cv_folds} partições")
        baseline_cv = evaluate_cv(x_dev, y_dev, n_splits=config.cv_folds,
                                  random_state=config.random_state)
        log(f"[CV] F1 médio de referência: {baseline_cv['f1']['media']:.4f}")
        phase("Buscando subconjuntos de características",
              f"[AG] {config.population_size} indivíduos · "
              f"{config.generations} gerações · {len(FEATURE_COLUMNS)} genes")
        genetic_result = select_features(
            x_dev, y_dev, config, on_generation=on_generation,
            on_evaluation=on_evaluation,
        )
        phase("Treinando os classificadores",
              "[TREINO] Ajustando os modelos com os dados de desenvolvimento")
        baseline = build_classifier()
        selected = build_classifier(genetic_result.selected_features)
        baseline.fit(x_dev, y_dev)
        selected.fit(x_dev, y_dev)
        phase("Avaliando no conjunto reservado",
              f"[TESTE] Calculando métricas nos mesmos {len(x_test)} casos reservados")
        base_metrics = evaluate_test(baseline, x_test, y_test)
        genetic_metrics = evaluate_test(selected, x_test, y_test)
        phase("Calculando a previsão",
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
        _render_kpis(None, "error", slot=slots["kpis"])
        slots["phase"].error("Execução interrompida")
        slots["technical"].error(f"Não foi possível concluir: {exc}")
        return

    summary = {
        "baseline": base_metrics,
        "genetico": genetic_metrics,
        "baseline_count": len(FEATURE_COLUMNS),
        "genetic_count": len(genetic_result.selected_features),
        "test_count": len(x_test),
        "reduction_pct": 100 * (len(FEATURE_COLUMNS) - len(genetic_result.selected_features))
                         / len(FEATURE_COLUMNS),
    }
    run = {
        "customer": customer,
        "predictions": predictions,
        "summary": summary,
        "history": history,
        "chromosome": genetic_result.chromosome,
        "events": events,
        "evaluated_subsets": genetic_result.evaluated_subsets,
        "elapsed_seconds": perf_counter() - started,
    }
    st.session_state["workflow_run"] = run
    _render_finished_run(run, slots)


def _render_client_panel() -> bool:
    st.markdown('<h2 class="churn-panel-heading">Cliente</h2>', unsafe_allow_html=True)
    with st.container(key="dashboard-client-fields", height=610, border=False):
        st.selectbox("Perfil de exemplo", list(PROFILE_FILES), key="profile_choice",
                     on_change=_choose_profile)
        st.button("Restaurar exemplo", on_click=_reset_profile, type="tertiary")
        a, b = st.columns(2, gap="small", wrap=True)
        with a:
            st.number_input(LABELS["tenure"], min_value=0, step=1, key="field_tenure")
            _select_field("InternetService")
        with b:
            _select_field("Contract")
            st.number_input(LABELS["MonthlyCharges"], min_value=0.0, step=1.0,
                            format="%.2f", key="field_MonthlyCharges")
        st.markdown('<div class="churn-subheading">Características adicionais</div>',
                    unsafe_allow_html=True)
        _render_client_details()
    with st.container(key="dashboard-client-footer", border=False):
        clicked = st.button("Calcular previsão", type="primary", use_container_width=True,
                            disabled=not DATASET.is_file())
        if not DATASET.is_file():
            st.caption("CSV não encontrado em data/raw/")
    return clicked


def _workspace_slots() -> dict:
    st.markdown('<h2 class="churn-panel-heading">Execução e previsão</h2>',
                unsafe_allow_html=True)
    kpis = st.empty()
    with st.container(key="dashboard-monitor-section", border=False):
        console_col, meta_col = st.columns([1.15, 0.85], gap="small", wrap=True)
        with console_col:
            console = st.empty()
        with meta_col:
            phase = st.empty()
            progress = st.empty()
            chromosome = st.empty()
    with st.container(key="dashboard-analysis-section", border=False):
        chart_col, technical_col = st.columns([1.1, 0.9], gap="small", wrap=True)
        with chart_col:
            st.markdown('<div class="churn-mini-heading">Evolução do F1-score</div>',
                        unsafe_allow_html=True)
            chart = st.empty()
        with technical_col:
            st.markdown('<div class="churn-mini-heading">Resumo técnico</div>',
                        unsafe_allow_html=True)
            technical = st.empty()
            log = st.empty()
    return {"kpis": kpis, "phase": phase, "progress": progress,
            "console": console, "chromosome": chromosome,
            "chart": chart, "technical": technical, "log": log}


def main() -> None:
    if "form_initialized" not in st.session_state:
        st.session_state["profile_choice"] = next(iter(PROFILE_FILES))
        _apply_profile(st.session_state["profile_choice"])
        st.session_state["form_initialized"] = True

    with st.container(key="dashboard-shell", border=False):
        st.markdown(
            '<header class="churn-topbar"><h1>Previsão de cancelamento</h1>'
            '<span class="churn-top-meta">19 características · 15 gerações</span></header>',
            unsafe_allow_html=True,
        )
        # As colunas são mantidas na horizontal em notebook e empilhadas no celular.
        client_col, workspace_col = st.columns([0.39, 0.61], gap="small", wrap=True)
        with client_col:
            with st.container(key="dashboard-client", height=780, border=True):
                clicked = _render_client_panel()
        with workspace_col:
            with st.container(key="dashboard-workspace", height=780, border=True):
                slots = _workspace_slots()
                if clicked:
                    st.session_state["workflow_run"] = None
                    customer = _current_customer()
                    if customer is None:
                        _render_idle(slots)
                        slots["technical"].error("Dados do cliente inválidos. Revise os campos.")
                    else:
                        _execute_full_workflow(customer, slots)
                elif st.session_state.get("workflow_run") is not None:
                    _render_finished_run(st.session_state["workflow_run"], slots)
                else:
                    _render_idle(slots)


if __name__ == "__main__":
    main()
