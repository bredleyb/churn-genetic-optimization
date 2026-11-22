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
/* Base do produto: componentes com chave explícita e classes de domínio. */
:root {color-scheme: dark;}
html, body, #root {overflow: hidden !important; background: #0B111B !important;}
.stApp, [data-testid="stMain"] {background: #0B111B !important; overflow: hidden !important; height: 100dvh !important;}
[data-testid="stHeader"], [data-testid="stDecoration"] {display: none !important;}
[data-testid="stMainBlockContainer"] {padding: 10px 18px 0 !important; max-width: none !important; height: 100dvh !important; overflow: hidden !important;}
.st-key-dashboard-shell {height: calc(100dvh - 20px); max-width: 1640px; margin: auto; overflow: hidden;}
.churn-topbar {display:flex; justify-content:space-between; align-items:center; gap:16px; height:52px; margin:0 0 10px;}
.churn-topbar h1 {font-size:20px;line-height:1.2;font-weight:650;letter-spacing:-.025em;margin:0;color:#F1F5F9;}
.churn-topbar .churn-top-meta {color:#8FA1B6;font-size:12px;white-space:nowrap;}
.st-key-dashboard-client, .st-key-dashboard-workspace {
  box-sizing:border-box;
  height:calc(100dvh - 88px)!important; min-height:0!important; overflow:hidden!important;
  background:#111B28!important; border:1px solid #263547!important; border-radius:12px!important;
  padding:14px!important;
}
.st-key-dashboard-client-fields {height:calc(100dvh - 248px)!important;min-height:0!important;overflow-y:auto!important;overflow-x:hidden!important;scrollbar-width:thin;scrollbar-color:#34465B transparent;}
.st-key-dashboard-client-footer {padding-top:10px; background:#111B28;}
.st-key-dashboard-client-footer [data-testid="stButton"] button {min-height:38px; font-weight:650;}
.churn-panel-heading {font-size:15px;letter-spacing:-.01em;font-weight:650;margin:0 0 10px;color:#E8EEF5;}
.churn-label {font-size:11px;color:#8FA1B6;}
.churn-subheading {font-size:11px;letter-spacing:.015em;text-transform:uppercase;color:#93A5BA;font-weight:650;margin:0 0 7px;}
.churn-help {color:#90A1B5;font-size:12px;line-height:1.4;}
.st-key-dashboard-client [data-testid="stWidgetLabel"] p {font-size:12px;}
.st-key-dashboard-client [data-testid="stVerticalBlock"] {gap:.55rem;}
.st-key-dashboard-workspace [data-testid="stVerticalBlock"] {gap:.45rem;}
.st-key-dashboard-client [data-baseweb="select"] > div,
.st-key-dashboard-client input {min-height:35px;}
.st-key-dashboard-client div[data-testid="stSegmentedControl"] {margin:5px 0 2px;}
.st-key-dashboard-client .st-key-dashboard-client-fields [data-testid="stVerticalBlock"] {gap:.42rem;}
.st-key-dashboard-workspace {overflow-y:auto!important;scrollbar-width:thin;scrollbar-color:#34465B transparent;}
.churn-kpis {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;min-width:0;margin-bottom:5px;}
.churn-kpi {min-width:0;padding:11px 12px 10px;border:1px solid #273749;background:#162230;border-radius:9px;}
.churn-kpi-label {font-size:11px;color:#93A6BA;line-height:1.25;margin:0 0 7px;}
.churn-kpi-value {font-size:21px;line-height:1.15;font-weight:700;letter-spacing:-.025em;color:#F1F5F9;white-space:nowrap;}
.churn-kpi-value.is-high {color:#F38E88;}
.churn-kpi-value.is-low {color:#63D7C0;}
.churn-kpi-foot {font-size:10px;line-height:1.3;color:#8194A9;margin-top:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.churn-phase {font-size:11px;color:#A6B7C9;line-height:1.4;margin:0 0 4px;}
.churn-console {margin:0;border:1px solid #2C3D50;border-radius:9px;overflow:hidden;background:#0B1420;min-width:0;}
.churn-console-head {display:flex;align-items:center;justify-content:space-between;gap:6px;padding:8px 10px;border-bottom:1px solid #263547;font-size:11px;font-weight:650;color:#D7E4F1;}
.churn-console-head small {font-size:10px;color:#7F94AA;font-weight:400;}
.churn-console-lines {height:192px;overflow-y:auto;overflow-x:hidden;scrollbar-width:thin;scrollbar-color:#34465B transparent;padding:9px 10px;color:#BACADC;font:11px/1.48 ui-monospace, SFMono-Regular, Consolas,monospace;overflow-wrap:anywhere;}
.churn-log-line {display:block;white-space:pre-wrap;}
.churn-log-line.is-step {color:#64CFC2;}
.churn-log-line.is-result {color:#EAF3FC;}
.churn-chromosome {margin:5px 0 0;background:#152130;border:1px solid #2A3B4D;border-radius:9px;padding:10px;min-width:0;}
.churn-chromosome-head {display:flex;align-items:center;justify-content:space-between;gap:6px;font-size:10px;color:#B1C1D2;margin-bottom:8px;}
.churn-chromosome-head strong {font-weight:650;color:#E4EEF8;}
.churn-bits {display:grid;grid-template-columns:repeat(19,minmax(0,1fr));gap:2px;}
.churn-bit {height:21px;display:flex;align-items:center;justify-content:center;border-radius:3px;background:#304053;color:#A4B4C5;font:600 9px ui-monospace, Consolas,monospace;min-width:0;}
.churn-bit.is-on {background:#168D88;color:#EEFFFC;}
.churn-legend {color:#8498AF;font-size:10px;margin-top:7px;}
.churn-mini-heading {font-size:11px;font-weight:650;color:#C3D2E1;margin:0 0 6px;}
.churn-chart-fallback {height:175px;border:1px solid #253548;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:12px;color:#8194AA;}
.churn-tech {display:grid;grid-template-columns:1fr 1fr;gap:7px;}
.churn-tech-item {border:1px solid #253548;border-radius:8px;background:#152131;padding:9px 10px;min-width:0;}
.churn-tech-item span {display:block;font-size:10px;color:#8DA1B5;}
.churn-tech-item strong {display:block;margin-top:4px;font-size:16px;color:#EEF5FA;font-variant-numeric:tabular-nums;}
.churn-tech-foot {font-size:10px;color:#8BA0B5;line-height:1.4;margin-top:8px;}
.churn-stale {font-size:11px;color:#F4BC83;border-left:2px solid #CC8B44;padding:6px 8px;background:#251F20;margin-top:4px;}
.churn-ready {font-size:12px;color:#8EA2B8;padding:5px 0;}
.churn-footer {color:#667E96;font-size:10px;}
.st-key-dashboard-workspace div[data-testid="stProgress"] {margin:6px 0 7px;}
.st-key-dashboard-workspace .stPlotlyChart,.st-key-dashboard-workspace [data-testid="stVegaLiteChart"] {min-width:0!important;}
@media (max-width:1150px) {
  .churn-kpi {padding:9px 8px;}
  .churn-kpi-value {font-size:17px;}
  .churn-kpi-foot {font-size:9px;}
  .churn-console-lines {height:170px;}
}
@media (max-width:900px) {
  [data-testid="stMainBlockContainer"] {padding:7px 10px 0!important;}
  .churn-topbar {height:44px; margin-bottom:6px;}
  .churn-topbar h1 {font-size:17px;}
  .churn-topbar .churn-top-meta {font-size:10px;}
  .st-key-dashboard-client, .st-key-dashboard-workspace {height:calc(100dvh - 68px)!important;padding:10px!important;}
  .st-key-dashboard-client-fields {height:calc(100dvh - 228px)!important;}
  .churn-kpis {grid-template-columns:repeat(2,minmax(0,1fr));}
  .churn-console-lines {height:144px;}
  .churn-bits {grid-template-columns:repeat(10,minmax(0,1fr));}
}
@media (max-width:620px) {
  /* Sem alturas internas em pixels: as colunas empilhadas devem ocupar apenas sua cota do viewport. */
  .churn-topbar {height:45px;}
  .churn-topbar .churn-top-meta {display:none;}
  /* O st.columns empilha as colunas abaixo de 640 px. É preciso limitar
     também a linha externa: controlar só os cartões internos deixa o tamanho
     natural das colunas ultrapassar a janela. */
  .st-key-dashboard-shell [data-testid="stHorizontalBlock"]:has(.st-key-dashboard-client):has(.st-key-dashboard-workspace) {
    /* A altura intrínseca dos wrappers do Streamlit pode ultrapassar o grid.
       Tirar a linha do fluxo e prender seus limites ao viewport evita que
       o conteúdo dos widgets expanda a área principal no modo móvel. */
    position: fixed !important;
    top: 60px !important;
    right: 10px !important;
    bottom: 8px !important;
    left: 10px !important;
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) !important;
    grid-template-rows: minmax(0, 43fr) minmax(0, 57fr) !important;
    gap: 8px !important;
    box-sizing: border-box !important;
    width: auto !important;
    height: auto !important;
    max-height: calc(100dvh - 68px) !important;
    min-height: 0 !important;
    margin: 0 !important;
    overflow: hidden !important;
    align-content: stretch !important;
  }
  .st-key-dashboard-shell [data-testid="stHorizontalBlock"]:has(.st-key-dashboard-client):has(.st-key-dashboard-workspace) > [data-testid="stColumn"] {
    width: 100% !important;
    min-width: 0 !important;
    height: 100% !important;
    min-height: 0 !important;
    overflow: hidden !important;
  }
  .st-key-dashboard-client, .st-key-dashboard-workspace {
    height: 100% !important;
    max-height: 100% !important;
    min-height: 0 !important;
  }
  /* Hierarquia real observada no trace do Playwright:
     stColumn > stVerticalBlock > stLayoutWrapper > dashboard-client/workspace.
     Os dois wrappers intermediários são auto-height no Streamlit; sem restrição,
     o painel Cliente cresce além da linha de 354px mesmo com a grade em 832px. */
  .st-key-dashboard-shell [data-testid="stHorizontalBlock"]:has(.st-key-dashboard-client):has(.st-key-dashboard-workspace) > [data-testid="stColumn"] > [data-testid="stVerticalBlock"] {
    box-sizing: border-box !important;
    display: block !important;
    width: 100% !important;
    height: 100% !important;
    max-height: 100% !important;
    min-height: 0 !important;
    overflow: hidden !important;
  }
  .st-key-dashboard-shell [data-testid="stHorizontalBlock"]:has(.st-key-dashboard-client):has(.st-key-dashboard-workspace) > [data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"] {
    box-sizing: border-box !important;
    display: block !important;
    width: 100% !important;
    height: 100% !important;
    max-height: 100% !important;
    min-height: 0 !important;
    overflow: hidden !important;
  }
  /* O cliente precisa de uma área flexível de campos e rodapé sempre visível. */
  .st-key-dashboard-client {
    display: grid !important;
    grid-template-rows: auto minmax(0, 1fr) auto !important;
    gap: 8px !important;
    align-content: stretch !important;
  }
  .st-key-dashboard-client > [data-testid="stLayoutWrapper"] {
    min-width: 0 !important;
    min-height: 0 !important;
  }
  .st-key-dashboard-client > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-client-fields) {
    height: 100% !important;
    max-height: 100% !important;
    overflow: hidden !important;
  }
  .st-key-dashboard-client-fields {
    height: 100% !important;
    max-height: 100% !important;
    min-height: 0 !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
  }
  .st-key-dashboard-client-footer {height:auto!important;}
  .churn-kpis {grid-template-columns:repeat(4,minmax(0,1fr));gap:4px;}
  .churn-kpi {padding:7px 5px;}
  .churn-kpi-label {font-size:9px;}
  .churn-kpi-value {font-size:15px;}
  .churn-kpi-foot {font-size:9px;}
  .churn-console-lines {height:110px;}
  .churn-chromosome {padding:8px;}
}
@media (max-width:410px) {
  .churn-topbar h1 {font-size:16px;}
  .churn-kpi-value {font-size:13px;}
  .churn-kpi-foot {display:none;}
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
    tab = st.selectbox("Editar características", ["Perfil", "Telefonia", "Internet", "Cobrança"],
                       key="detail_tab")
    if tab == "Perfil":
        for feature in PROFILE_FEATURES:
            _select_field(feature)
    elif tab == "Telefonia":
        _select_field("PhoneService")
        _select_field(
            "MultipleLines", disabled=st.session_state["field_PhoneService"] == "No",
            help_text="Indisponível quando o cliente não possui telefone.",
        )
    elif tab == "Internet":
        inactive = st.session_state["field_InternetService"] == "No"
        for feature in INTERNET_FEATURES:
            _select_field(feature, disabled=inactive,
                          help_text="Indisponível sem serviço de internet.")
    else:
        for feature in BILLING_FEATURES:
            _select_field(feature)
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
    semantics = "is-negative" if entry["classe"] == 1 else "is-positive"
    return f"{probability:.2f}".replace(".", ",") + "%", label, semantics


def _render_prediction_comparison(run: dict | None, status: str, *, slot) -> None:
    """Comparação protagonista. A cor é aplicada apenas à classe prevista."""
    ready = run is not None and status == "complete"
    count = run["summary"]["genetic_count"] if run is not None else None
    reference = _format_probability(run["predictions"]["baseline"]) if ready else ("—", "Aguardando", "")
    genetic = _format_probability(run["predictions"]["genetico"]) if ready else ("—", "Aguardando", "")
    states = {"idle":"Pronto", "running":"Processando", "complete":"Concluído",
              "stale":"Dados alterados", "error":"Erro"}
    def result(model: str, details: str, entry: tuple[str,str,str]) -> str:
        value, outcome, semantic = entry
        return (f'<div class="churn-model" aria-label="{escape(model)}">'
                f'<div class="churn-model-name">{escape(model)}</div>'
                f'<div class="churn-model-detail">{escape(details)}</div>'
                f'<div class="churn-prediction-value">{escape(value)}</div>'
                f'<div class="churn-outcome {semantic}">{escape(outcome)}</div></div>')
    markup = ('<section class="churn-comparison" aria-label="Comparação dos modelos">'
              '<div class="churn-section-top"><h3>Previsão do cliente</h3>'
              f'<span class="churn-state {"is-error" if status=="error" else ""}">{escape(states[status])}</span></div>'
              '<div class="churn-models">'
              + result("Referência", "19 características", reference)
              + result("Seleção genética", f"{count}/19 características" if count is not None else "Aguardando seleção", genetic)
              + '</div></section>')
    slot.markdown(markup, unsafe_allow_html=True)


def _render_console(events: list[str], *, slot, complete: bool = False) -> None:
    # Exibir últimas mensagens no início visível; o histórico integral segue disponível no download.
    visible = list(reversed(events[-9:]))
    rows = []
    for line in visible:
        kind = ("is-result" if line.startswith("[FIM]") else
                "is-step" if line.startswith("[GERAÇÃO]") else "")
        rows.append(f'<span class="churn-log-line {kind}">{escape(line)}</span>')
    markup = ('<section class="churn-console" aria-label="Eventos da busca genética">'
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
              '<div class="churn-section-top"><h3>Características selecionadas</h3>'
              f'<span class="churn-selection-count">{sum(chromosome)} / 19</span></div>'
              f'<div class="churn-bits">{bits}</div>'
              '<div class="churn-chromosome-note">1 = incluída · 0 = excluída</div></section>')
    slot.markdown(markup, unsafe_allow_html=True)


def _history_chart(history: list[dict], *, slot) -> None:
    """SVG proporcional, sem bibliotecas de gráficos ou dependências de rede.

    A escala inicia em zero e permanece constante nas 15 gerações, evitando
    sugerir uma melhora maior por mudanças automáticas dos limites do eixo.
    """
    values = [max(0.0, min(1.0, float(item["melhor_f1_cv"]))) for item in history]
    # Para resultados superiores a 0,8, ampliar o eixo em vez de truncar o dado.
    ceiling = max(0.8, min(1.0, (int(max(values) * 5 + 0.999999) / 5) if values else 0.8))
    points = " ".join(
        f'{1000 * (i / 14):.2f},{240 * (1 - value / ceiling):.2f}'
        for i, value in enumerate(values)
    )
    line = (f'<polyline class="churn-chart-line" points="{points}"/>' if values else '')
    grid = ''.join(f'<line x1="0" y1="{i*60}" x2="1000" y2="{i*60}"/>' for i in range(5))
    markup = (
        '<section class="churn-chart" aria-label="Evolução do F1-score em validação cruzada">'
        '<div class="churn-section-top"><h3>Evolução do F1-score</h3>'
        '<span class="churn-chart-descriptor">Validação cruzada · 15 gerações</span></div>'
        '<div class="churn-chart-plot">'
        '<div class="churn-chart-axis-y">' +
        "".join(f'<span>{(ceiling * tick / 4):.1f}</span>'.replace(".", ",") for tick in range(4, -1, -1)) +
        '</div>'
        '<div class="churn-chart-plot-main">'
        f'<svg class="churn-chart-svg" viewBox="0 0 1000 240" preserveAspectRatio="none" role="img" '
        f'aria-label="Evolução do F1 em validação cruzada; {len(values)} gerações">'
        f'<g class="churn-chart-grid">{grid}</g>{line}</svg>'
        '<div class="churn-chart-axis-x"><span>1</span><span>5</span><span>10</span><span>15</span></div>'
        '</div></div>'
        f'<div class="churn-chart-caption">{"Melhor F1 (CV): " + format(max(values), ".4f").replace(".", ",") if values else "Aguardando a primeira geração"}</div>'
        '</section>'
    )
    slot.markdown(markup, unsafe_allow_html=True)


def _render_technical(run: dict | None, *, slot, stale: bool = False) -> None:
    if run is None:
        metrics = (("Referência", "—"), ("Genético", "—"), ("ΔF1", "—"))
        summary = "F1 no teste reservado · 20% dos dados"
    else:
        data = run["summary"]
        base_f1, gen_f1 = data["baseline"]["f1"], data["genetico"]["f1"]
        metrics = (("Referência", f"{base_f1:.4f}".replace(".", ",")),
                   ("Genético", f"{gen_f1:.4f}".replace(".", ",")),
                   ("ΔF1", f"{gen_f1-base_f1:+.4f}".replace(".", ",")))
        summary = (f'{data["reduction_pct"]:.1f}% de redução · '
                   f'{run["evaluated_subsets"]} subconjuntos · '
                   f'{data["test_count"]} clientes no teste')
    rows = "".join(f'<div class="churn-metric"><dt>{escape(label)}</dt><dd>{escape(value)}</dd></div>'
                   for label,value in metrics)
    warning = ('<div class="churn-stale">Os dados do cliente foram alterados. '
               'Clique em Calcular previsão para atualizar.</div>') if stale else ""
    slot.markdown('<section class="churn-technical" aria-label="Métricas de teste">'
                  '<div class="churn-section-top"><h3>Desempenho no teste reservado</h3></div>'
                  f'<dl class="churn-metrics">{rows}</dl><div class="churn-technical-note">{escape(summary)}</div>'
                  f'{warning}</section>', unsafe_allow_html=True)


def _render_idle(slots: dict) -> None:
    _render_prediction_comparison(None, "idle", slot=slots["comparison"])
    slots["phase"].markdown('<span class="churn-phase">Pronto para iniciar</span>', unsafe_allow_html=True)
    slots["progress"].progress(0.0, text="Geração 0 de 15")
    _render_console(["[PRONTO] Aguardando execução do experimento"], slot=slots["console"])
    _render_chromosome(tuple(0 for _ in FEATURE_COLUMNS), "Aguardando avaliação", slot=slots["chromosome"])
    _history_chart([], slot=slots["chart"])
    _render_technical(None, slot=slots["technical"])


def _render_finished_run(run: dict, slots: dict) -> None:
    stale = _is_stale(run)
    _render_prediction_comparison(run, "stale" if stale else "complete", slot=slots["comparison"])
    slots["phase"].markdown('<span class="churn-phase">15 gerações concluídas</span>', unsafe_allow_html=True)
    slots["progress"].progress(1.0, text="Geração 15 de 15")
    _render_console(run["events"], slot=slots["console"], complete=True)
    _render_chromosome(run["chromosome"], "Melhor cromossomo", slot=slots["chromosome"])
    _history_chart(run["history"], slot=slots["chart"])
    _render_technical(run, slot=slots["technical"], stale=stale)
    if run.get("events"):
        slots["log"].download_button(
            "Baixar log completo", "\n".join(run["events"]) + "\n",
            file_name="execucao-genetica.log", mime="text/plain",
            key="download_full_log", type="tertiary",
        )


def _execute_full_workflow(customer: dict, slots: dict) -> None:
    """Execução completa ao clicar em Calcular previsão; não altera arquivos salvos."""
    config = GeneticConfig()
    started = perf_counter()
    events: list[str] = []
    history: list[dict] = []
    _render_prediction_comparison(None, "running", slot=slots["comparison"])
    slots["progress"].progress(0.0, text=f"Geração 0 de {config.generations}")
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
                                   text=f"Geração {number} de {config.generations}")
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
        _render_prediction_comparison(None, "error", slot=slots["comparison"])
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
    with st.container(key="dashboard-client-fields", border=False):
        a, b = st.columns([0.72, 0.28], gap="small", wrap=False)
        with a:
            st.selectbox("Perfil de exemplo", list(PROFILE_FILES), key="profile_choice",
                         on_change=_choose_profile)
        with b:
            st.button("Restaurar", on_click=_reset_profile, type="tertiary")
        a, b = st.columns(2, gap="small", wrap=True)
        with a:
            st.number_input(LABELS["tenure"], min_value=0, step=1, key="field_tenure")
            _select_field("InternetService")
        with b:
            _select_field("Contract")
            st.number_input(LABELS["MonthlyCharges"], min_value=0.0, step=1.0,
                            format="%.2f", key="field_MonthlyCharges")
        st.markdown('<div class="churn-subheading">Outras características</div>', unsafe_allow_html=True)
        _render_client_details()
    with st.container(key="dashboard-client-footer", border=False):
        clicked = st.button("Calcular previsão", type="primary", use_container_width=True,
                            disabled=not DATASET.is_file())
        if not DATASET.is_file():
            st.caption("CSV não encontrado em data/raw/")
    return clicked


def _workspace_slots() -> dict:
    st.markdown('<h2 class="churn-panel-heading">Análise e execução</h2>', unsafe_allow_html=True)
    comparison = st.empty()
    with st.container(key="dashboard-analysis-section", border=False):
        chart = st.empty()
    with st.container(key="dashboard-selection-section", border=False):
        chromosome = st.empty()
        technical = st.empty()
    with st.container(key="dashboard-monitor-section", border=False):
        st.markdown('<div class="churn-monitor-title">Monitor de execução</div>', unsafe_allow_html=True)
        phase = st.empty()
        progress = st.empty()
        console = st.empty()
        log = st.empty()
    return {"comparison":comparison,"chart":chart,"chromosome":chromosome,
            "technical":technical,"phase":phase,"progress":progress,
            "console":console,"log":log}


def main() -> None:
    if "form_initialized" not in st.session_state:
        st.session_state["profile_choice"] = next(iter(PROFILE_FILES))
        _apply_profile(st.session_state["profile_choice"])
        st.session_state["form_initialized"] = True

    with st.container(key="dashboard-shell", border=False):
        st.markdown(
            '<header class="churn-topbar"><h1>Previsão de cancelamento</h1>'
            '<span class="churn-top-meta">Projeto N3 · Seleção genética de características</span></header>',
            unsafe_allow_html=True,
        )
        client_col, workspace_col = st.columns([0.30, 0.70], gap="small", wrap=True)
        with client_col:
            with st.container(key="dashboard-client", border=True):
                clicked = _render_client_panel()
        with workspace_col:
            with st.container(key="dashboard-workspace", border=True):
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
