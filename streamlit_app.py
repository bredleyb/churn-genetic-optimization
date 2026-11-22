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
/* N3 — sistema monocromático para leitura em projetor.
   Contraste deliberado, sem cartões decorativos, sombras ou gradientes. */
:root {
  color-scheme: dark;
  --n3-font-ui:"Familjen Grotesk","Segoe UI",Arial,sans-serif;
  --n3-bg:#000000; --n3-surface:#0E1013; --n3-control:#17181B;
  --n3-elevated:#202124; --n3-surface-alt:#282A2D;
  --n3-line:#383A3E; --n3-outline:#55585D;
  --n3-text:#F5F5F5; --n3-secondary:#D8D8D8; --n3-muted:#B7B7B7;
  --n3-positive:#5FE29A; --n3-negative:#FF6464;
  --n3-field-height:42px; --n3-field-radius:4px;
  --n3-field-text-size:16px; --n3-field-text-line:20px;
}
html, body, #root {height:100%;overflow:hidden!important;background:var(--n3-bg)!important;}
.stApp,[data-testid="stMain"] {height:100dvh!important;overflow:hidden!important;background:var(--n3-bg)!important;}
[data-testid="stHeader"],[data-testid="stDecoration"],[data-testid="stToolbar"] {display:none!important;}
[data-testid="stMainBlockContainer"] {box-sizing:border-box!important;padding:12px 18px 10px!important;max-width:none!important;height:100dvh!important;overflow:hidden!important;}
.stApp {font-family:var(--n3-font-ui)!important;color:var(--n3-text)!important;}
/* Os widgets do Streamlit podem definir tipografia própria via Emotion. */
.stApp :is(button,input,textarea,select,[role="combobox"],[role="tab"],[role="option"]),
.stApp [data-testid="stWidgetLabel"],
.stApp [data-testid="stWidgetLabel"] *,
.stApp [data-testid="stMarkdownContainer"] {
  font-family:var(--n3-font-ui)!important;
}
/* Logs e bits continuam monoespaçados para manter as colunas alinhadas. */
.stApp .churn-console-lines,
.stApp .churn-console-lines *,
.stApp .churn-bit {
  font-family:Consolas,"Liberation Mono",monospace!important;
}
.st-key-dashboard-shell {height:calc(100dvh - 22px);width:100%;max-width:1680px;margin:auto;overflow:hidden;}
/* A linha externa e seus wrappers são controlados; o Streamlit cria alturas automáticas. */
.st-key-dashboard-shell [data-testid="stHorizontalBlock"]:has(.st-key-dashboard-client):has(.st-key-dashboard-workspace) {
  /* Âncoras da viewport: impedir altura herdada da grade em janelas menores. */
  position:fixed!important;top:12px!important;right:18px!important;bottom:10px!important;left:18px!important;
  box-sizing:border-box!important;display:grid!important;
  grid-template-columns:clamp(300px,27vw,380px) minmax(0,1fr)!important;
  gap:12px!important;width:auto!important;height:auto!important;
  min-height:0!important;max-height:none!important;overflow:hidden!important;
}
.st-key-dashboard-shell [data-testid="stHorizontalBlock"]:has(.st-key-dashboard-client):has(.st-key-dashboard-workspace) > [data-testid="stColumn"] {
  box-sizing:border-box!important;width:100%!important;min-width:0!important;height:100%!important;min-height:0!important;overflow:hidden!important;
}
.st-key-dashboard-shell [data-testid="stHorizontalBlock"]:has(.st-key-dashboard-client):has(.st-key-dashboard-workspace) > [data-testid="stColumn"] > [data-testid="stVerticalBlock"],
.st-key-dashboard-shell [data-testid="stHorizontalBlock"]:has(.st-key-dashboard-client):has(.st-key-dashboard-workspace) > [data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"] {
  box-sizing:border-box!important;display:block!important;width:100%!important;height:100%!important;max-height:100%!important;min-height:0!important;overflow:hidden!important;
}
.st-key-dashboard-client,.st-key-dashboard-workspace {
  box-sizing:border-box!important;min-width:0!important;min-height:0!important;
  width:100%!important;height:100%!important;max-height:100%!important;
  background:var(--n3-surface)!important;border:1px solid var(--n3-outline)!important;
  border-radius:6px!important;padding:16px!important;overflow:hidden!important;
}
.st-key-dashboard-client {display:grid!important;grid-template-rows:auto minmax(0,1fr) auto!important;gap:6px!important;align-content:stretch!important;}
.st-key-dashboard-client > [data-testid="stLayoutWrapper"] {min-width:0!important;min-height:0!important;}
.st-key-dashboard-client > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-client-fields) {height:100%!important;max-height:100%!important;overflow:hidden!important;}
.st-key-dashboard-client-fields {height:100%!important;max-height:100%!important;min-height:0!important;overflow-y:auto!important;overflow-x:hidden!important;scrollbar-color:var(--n3-outline) transparent;scrollbar-width:thin;}
.st-key-dashboard-client-footer {height:auto!important;padding-top:8px;border-top:1px solid var(--n3-line);}
.churn-panel-heading {font-size:19px;line-height:1.3;font-weight:600;letter-spacing:-.01em;margin:0!important;color:var(--n3-text);}
/* Base visual compartilhada por seletores e entradas numéricas nativas. */
.st-key-dashboard-client [data-testid="stWidgetLabel"] {
  display:flex!important;align-items:center!important;
  min-height:20px!important;margin-bottom:6px!important;
}
.st-key-dashboard-client [data-testid="stWidgetLabel"] p,
.st-key-dashboard-client label p {
  font-size:15px!important;line-height:20px!important;
  color:var(--n3-secondary)!important;margin:0!important;
}
.st-key-dashboard-client [data-testid="stVerticalBlock"] {gap:.65rem;}
.st-key-dashboard-client-fields [data-testid="stVerticalBlock"] {gap:.62rem;}
.st-key-dashboard-client [data-baseweb="select"] > div,
.st-key-dashboard-client [data-testid="stNumberInput"] [data-baseweb="input"] {
  box-sizing:border-box!important;height:var(--n3-field-height)!important;
  min-height:var(--n3-field-height)!important;max-height:var(--n3-field-height)!important;
  display:flex!important;align-items:center!important;
  background:var(--n3-control)!important;border:1px solid var(--n3-outline)!important;
  border-radius:var(--n3-field-radius)!important;
}
.st-key-dashboard-client [data-testid="stNumberInput"] input {
  box-sizing:border-box!important;min-width:0!important;
  height:calc(var(--n3-field-height) - 2px)!important;min-height:0!important;
  padding:0 10px!important;background:transparent!important;
  border:0!important;border-radius:0!important;box-shadow:none!important;
  color:var(--n3-text)!important;font-family:var(--n3-font-ui)!important;
  font-size:var(--n3-field-text-size)!important;line-height:var(--n3-field-text-line)!important;
}
.st-key-dashboard-client [data-baseweb="select"] input {
  box-sizing:border-box!important;min-height:0!important;
  font-size:var(--n3-field-text-size)!important;line-height:var(--n3-field-text-line)!important;
}
.st-key-dashboard-client [data-testid="stNumberInput"] button {
  box-sizing:border-box!important;min-width:32px!important;width:32px!important;
  height:calc(var(--n3-field-height) - 2px)!important;min-height:0!important;
  padding:0!important;display:flex!important;align-items:center!important;
  justify-content:center!important;background:var(--n3-surface)!important;
  border:0!important;border-radius:0!important;color:var(--n3-text)!important;
}
.st-key-dashboard-client [data-testid="stNumberInput"] button:hover {
  background:var(--n3-elevated)!important;
}
.st-key-dashboard-client-footer [data-testid="stButton"] button[kind="primary"],
.st-key-dashboard-client-footer button {height:48px!important;min-height:48px!important;background:var(--n3-text)!important;color:#000!important;border:1px solid var(--n3-text)!important;border-radius:4px!important;font-size:16px!important;font-weight:600!important;}
.st-key-dashboard-client-footer button:hover {background:#D8D8D8!important;border-color:#D8D8D8!important;}
.st-key-dashboard-client-footer button:focus-visible {outline:2px solid #fff!important;outline-offset:3px!important;}
.st-key-dashboard-client-fields button[kind="tertiary"],
.st-key-dashboard-client-fields button {font-size:14px!important;color:var(--n3-secondary)!important;}
/* Área analítica: cinco seções com função definida, uma só superfície principal. */
.st-key-dashboard-workspace {
  display:grid!important;grid-template-rows:auto auto minmax(150px,1fr) auto minmax(116px,19dvh)!important;
  gap:6px!important;align-content:stretch!important;
}
.st-key-dashboard-workspace > [data-testid="stLayoutWrapper"] {min-width:0!important;min-height:0!important;overflow:hidden!important;}
.st-key-dashboard-analysis-section {height:100%!important;min-height:0!important;overflow:hidden!important;}
.st-key-dashboard-selection-section {display:grid!important;grid-template-columns: minmax(0,1fr) minmax(0,1fr)!important;gap:22px!important;min-height:0!important;overflow:hidden!important;align-items:start;}
.st-key-dashboard-monitor-section {height:100%!important;min-height:0!important;overflow:auto!important;scrollbar-color:var(--n3-outline) transparent;scrollbar-width:thin;}
.st-key-dashboard-workspace > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-analysis-section),
.st-key-dashboard-workspace > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-monitor-section) {height:100%!important;min-height:0!important;overflow:hidden!important;}
/* Predição: dois resultados em uma comparação contínua. */
.churn-comparison {margin:0;padding:0 0 12px;border-bottom:1px solid var(--n3-line);}
.churn-section-top {display:flex;align-items:baseline;justify-content:space-between;gap:12px;margin:0 0 8px;min-width:0;}
.churn-section-top h3 {font-size:16px;font-weight:600;line-height:1.35;margin:0;color:var(--n3-text);}
.churn-state {font-size:13px;color:var(--n3-muted);white-space:nowrap;}
.churn-state.is-error {color:var(--n3-negative);}
.churn-models {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0;}
.churn-model {min-width:0;padding:0 18px 0 0;}
.churn-model + .churn-model {border-left:1px solid var(--n3-line);padding:0 0 0 22px;}
.churn-model-name {font-size:16px;font-weight:600;color:var(--n3-secondary);line-height:1.3;}
.churn-model-detail {font-size:13px;color:var(--n3-muted);line-height:1.4;}
.churn-prediction-value {font-size:36px;font-weight:650;letter-spacing:-.025em;line-height:1.2;color:var(--n3-text);font-variant-numeric:tabular-nums;margin-top:4px;}
.churn-outcome {font-size:15px;line-height:1.3;color:var(--n3-secondary);font-weight:600;}
.churn-outcome.is-positive {color:var(--n3-positive);}
.churn-outcome.is-negative {color:var(--n3-negative);}
/* Gráfico SVG: fonte fora do vetor para não encolher com a escala. */
.churn-chart {height:100%;min-height:0;display:flex;flex-direction:column;border-bottom:1px solid var(--n3-line);padding:2px 0 10px;}
.churn-chart-plot {display:flex;gap:8px;flex:1;min-height:100px;}
.churn-chart-axis-y {width:33px;display:flex;flex-direction:column;justify-content:space-between;align-items:flex-end;padding-bottom:20px;font-size:13px;color:var(--n3-secondary);font-variant-numeric:tabular-nums;}
.churn-chart-plot-main {flex:1;min-width:0;display:flex;flex-direction:column;}
.churn-chart-svg {width:100%;flex:1;min-height:80px;display:block;overflow:visible;}
.churn-chart-grid line {stroke:var(--n3-line);stroke-width:1.4;vector-effect:non-scaling-stroke;}
.churn-chart-line {fill:none;stroke:var(--n3-text);stroke-width:2.6;stroke-linejoin:round;stroke-linecap:round;vector-effect:non-scaling-stroke;}
.churn-chart-axis-x {display:flex;justify-content:space-between;color:var(--n3-secondary);font-size:13px;font-variant-numeric:tabular-nums;margin-top:3px;}
.churn-chart-caption {color:var(--n3-muted);font-size:13px;line-height:1.35;min-height:17px;margin:4px 0 0 41px;}
/* Características e resultados técnicos: nenhuma fila de KPI aninhados. */
.churn-chromosome {min-width:0;}
.churn-selection-count {font-size:15px;font-weight:600;color:var(--n3-text);font-variant-numeric:tabular-nums;white-space:nowrap;}
.churn-bits {display:grid;grid-template-columns:repeat(19,minmax(0,1fr));gap:3px;min-width:0;}
.churn-bit {height:26px;min-width:0;display:flex;align-items:center;justify-content:center;border-radius:2px;background:var(--n3-elevated);color:var(--n3-muted);font:600 12px/1 Consolas,"Liberation Mono",monospace;}
.churn-bit.is-on {color:#000;background:var(--n3-text);}
.churn-chromosome-note {font-size:12px;color:var(--n3-muted);margin-top:5px;}
.churn-metrics {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:0;}
.churn-metric {min-width:0;}
.churn-metric dt {font-size:13px;color:var(--n3-secondary);white-space:nowrap;}
.churn-metric dd {font-size:20px;color:var(--n3-text);font-weight:600;margin:3px 0 0;white-space:nowrap;font-variant-numeric:tabular-nums;}
.churn-technical-note {font-size:12px;line-height:1.4;color:var(--n3-muted);margin-top:7px;}
/* Monitor: monoespaçada, conteúdo mais recente primeiro, largura estável. */
.churn-monitor-title {font-size:16px;font-weight:600;color:var(--n3-text);line-height:1.3;margin:0;}
.churn-phase {font-size:13px;color:var(--n3-secondary);}
.churn-console {background:var(--n3-control);border-top:1px solid var(--n3-line);margin-top:4px;}
.churn-console-lines {max-height:66px;min-height:42px;overflow-y:auto;overflow-x:hidden;padding:5px 2px;scrollbar-width:thin;scrollbar-color:var(--n3-outline) transparent;font:13px/1.4 Consolas,"Liberation Mono",monospace;color:var(--n3-secondary);overflow-wrap:anywhere;}
.churn-log-line {display:block;white-space:pre-wrap;}
.churn-log-line.is-result {color:var(--n3-text);font-weight:600;}
.churn-log-line.is-step {color:var(--n3-secondary);}
.st-key-dashboard-monitor-section [data-testid="stVerticalBlock"] {gap:.18rem!important;}
.st-key-dashboard-workspace [data-testid="stProgress"] {margin:1px 0!important;}
.st-key-dashboard-workspace [data-testid="stProgress"] p {font-size:12px!important;color:var(--n3-muted)!important;}
.st-key-dashboard-monitor-section button[kind="tertiary"] {font-size:13px!important;color:var(--n3-secondary)!important;min-height:26px!important;padding:0 4px!important;}
@media(max-width:1150px) {
  .st-key-dashboard-shell [data-testid="stHorizontalBlock"]:has(.st-key-dashboard-client):has(.st-key-dashboard-workspace) {grid-template-columns:310px minmax(0,1fr)!important;}
  .st-key-dashboard-workspace {grid-template-rows:auto auto minmax(130px,1fr) auto minmax(100px,17dvh)!important;gap:8px!important;padding:12px!important;}
  .churn-prediction-value {font-size:32px;}
  .st-key-dashboard-selection-section {gap:12px!important;}
  .churn-bit {height:24px;font-size:11px;}
  .churn-metric dd {font-size:18px;}
}
@media(max-width:900px) {
  [data-testid="stMainBlockContainer"] {padding:9px 10px 8px!important;}
  .st-key-dashboard-shell {height:calc(100dvh - 17px);}
  .st-key-dashboard-shell [data-testid="stHorizontalBlock"]:has(.st-key-dashboard-client):has(.st-key-dashboard-workspace) {
    grid-template-columns:270px minmax(0,1fr)!important;
    top:9px!important;right:10px!important;bottom:8px!important;left:10px!important;gap:8px!important;
  }
  .st-key-dashboard-client,.st-key-dashboard-workspace {padding:11px!important;}
  .st-key-dashboard-selection-section {grid-template-columns:1fr!important;overflow-y:auto!important;}
  .churn-model-name {font-size:15px;}
  .churn-prediction-value {font-size:27px;}
  .churn-bits {gap:2px;}
}
@media(max-height:760px) and (min-width:621px) {
  .st-key-dashboard-workspace {grid-template-rows:auto auto minmax(105px,1fr) auto minmax(90px,16dvh)!important;gap:6px!important;}
  .churn-model-detail {font-size:12px;}
  .churn-prediction-value {font-size:32px;}
  .churn-comparison {padding-bottom:7px;}
  .churn-console-lines {max-height:52px;min-height:32px;}
  .churn-chart-caption {font-size:12px;}
  .churn-section-top {margin-bottom:5px;}
  .churn-bit {height:23px;}
}
@media(max-width:620px) {
  /* Preserva a correção diagnosticada com trace real: colunas e wrappers limitados. */
  .st-key-dashboard-shell [data-testid="stHorizontalBlock"]:has(.st-key-dashboard-client):has(.st-key-dashboard-workspace) {
    position:fixed!important;top:8px!important;right:8px!important;bottom:8px!important;left:8px!important;
    display:grid!important;grid-template-columns:minmax(0,1fr)!important;
    grid-template-rows:minmax(0,36fr) minmax(0,64fr)!important;
    gap:8px!important;box-sizing:border-box!important;
    width:auto!important;height:auto!important;max-height:calc(100dvh - 16px)!important;
    min-height:0!important;margin:0!important;overflow:hidden!important;align-content:stretch!important;
  }
  .st-key-dashboard-client,.st-key-dashboard-workspace {height:100%!important;max-height:100%!important;min-height:0!important;}
  .st-key-dashboard-client {padding:10px!important;gap:6px!important;}
  .churn-panel-heading {font-size:17px;}
  .st-key-dashboard-client-footer button {height:44px!important;min-height:44px!important;}
  .st-key-dashboard-workspace {padding:10px!important;display:grid!important;grid-template-rows:auto auto minmax(110px,1fr) auto minmax(75px,15dvh)!important;gap:7px!important;}
  .churn-comparison {padding-bottom:7px;}
  .churn-section-top h3 {font-size:14px;}
  .churn-model-name {font-size:14px;}
  .churn-model-detail {font-size:12px;}
  .churn-model {padding-right:10px;}
  .churn-model+.churn-model {padding-left:10px;}
  .churn-prediction-value {font-size:26px;}
  .churn-outcome {font-size:13px;}
  .churn-chart-plot {min-height:65px;}
  .churn-chart-axis-y,.churn-chart-axis-x {font-size:12px;}
  .churn-chart-caption {font-size:12px;}
  .st-key-dashboard-selection-section {display:block!important;overflow-y:auto!important;}
  .churn-monitor-title {font-size:14px;}
  .churn-console-lines {font-size:12px;max-height:46px;min-height:24px;}
}

/* Duas apresentações do mesmo estado: grade completa no projetor, abas no celular. */
.st-key-dashboard-workspace {
  grid-template-columns:minmax(0,1fr)!important;
  grid-template-rows:auto auto minmax(0,1fr)!important;
}
.st-key-dashboard-workspace > [data-testid="stLayoutWrapper"] {
  width:100%!important;min-width:0!important;
}
/* O Streamlit conserva o wrapper da versão móvel. Em desktop ele criava
   uma quarta linha implícita, empurrando o monitor para fora do painel. */
.st-key-dashboard-workspace > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-mobile-detail) {
  display:none!important;
}
.st-key-dashboard-desktop-detail {
  display:grid!important;grid-template-columns:minmax(0,1fr)!important;
  width:100%!important;max-width:100%!important;
  grid-template-rows:minmax(145px,1fr) auto minmax(115px,19dvh)!important;
  gap:10px!important;height:100%!important;min-height:0!important;overflow:hidden!important;
}
.st-key-dashboard-desktop-detail > [data-testid="stLayoutWrapper"] {min-height:0!important;overflow:hidden!important;}
.st-key-dashboard-desktop-detail > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-analysis-section),
.st-key-dashboard-desktop-detail > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-monitor-section) {height:100%!important;min-height:0!important;}
.st-key-dashboard-mobile-detail {display:none!important;}
@media(max-width:1150px) {
 .st-key-dashboard-desktop-detail {grid-template-rows:minmax(120px,1fr) auto minmax(100px,17dvh)!important;gap:8px!important;}
}
@media(max-height:760px) and (min-width:621px) {
 .st-key-dashboard-desktop-detail {grid-template-rows:minmax(105px,1fr) auto minmax(90px,16dvh)!important;gap:6px!important;}
}
@media(max-width:620px) {
 .st-key-dashboard-workspace {grid-template-rows:auto auto minmax(0,1fr)!important;}
 .st-key-dashboard-workspace > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-desktop-detail) {display:none!important;}
 .st-key-dashboard-desktop-detail {display:none!important;}
 .st-key-dashboard-workspace > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-mobile-detail) {
   display:block!important;height:100%!important;min-height:0!important;overflow:hidden!important;
 }
 .st-key-dashboard-mobile-detail {display:block!important;height:100%!important;min-height:0!important;overflow:hidden!important;}
 .st-key-dashboard-mobile-detail [data-testid="stTabs"] {height:100%!important;max-height:100%!important;min-height:0!important;overflow:hidden!important;}
 .st-key-dashboard-mobile-detail [data-baseweb="tab-list"] {height:41px!important;min-height:41px!important;}
 .st-key-dashboard-mobile-detail [role="tab"] {font-size:15px!important;color:var(--n3-secondary)!important;}
 .st-key-dashboard-mobile-detail [role="tab"][aria-selected="true"] {color:var(--n3-text)!important;}
 .st-key-dashboard-mobile-detail [data-baseweb="tab-panel"] {
    height:calc(100% - 42px)!important;max-height:calc(100% - 42px)!important;
    min-height:0!important;overflow-y:auto!important;overflow-x:hidden!important;
    scrollbar-width:thin;scrollbar-color:var(--n3-outline) transparent;
 }
 .st-key-dashboard-mobile-detail .churn-chart {height:190px;}
 .st-key-dashboard-mobile-detail .churn-technical {padding-top:12px;border-top:1px solid var(--n3-line);margin-top:10px;}
 .st-key-dashboard-mobile-detail .churn-chromosome {padding-top:10px;border-top:1px solid var(--n3-line);margin-top:8px;}
 .st-key-dashboard-mobile-detail .churn-console-lines {max-height:210px!important;min-height:100px;}
 .st-key-dashboard-mobile-detail .churn-monitor-title {display:none;}
}

/* A seção do gráfico precisa preencher o trilho do grid. Os wrappers Markdown
   do Streamlit usavam altura intrínseca, fazendo o SVG sobrepor as métricas. */
.st-key-dashboard-analysis-section > [data-testid="stElementContainer"],
.st-key-dashboard-analysis-section [data-testid="stMarkdown"],
.st-key-dashboard-analysis-section [data-testid="stMarkdown"] > div,
.st-key-dashboard-analysis-section [data-testid="stMarkdownContainer"] {
  box-sizing:border-box!important;
  height:100%!important;max-height:100%!important;min-height:0!important;
  overflow:hidden!important;
}
.st-key-dashboard-analysis-section .churn-chart {
  height:100%!important;max-height:100%!important;min-height:0!important;
  overflow:hidden!important;
}

/* 1280x720 é o formato prioritário de projeção. Comprimir o gráfico e o
   monitor na mesma coluna vertical reduz a leitura; a faixa inferior usa
   seleção à esquerda e console à direita, ambos com altura própria. */
@media (min-width:1000px) and (max-height:760px) {
  .st-key-dashboard-desktop-detail {
    grid-template-columns:minmax(0,1.3fr) minmax(0,.7fr)!important;
    grid-template-rows:minmax(0,1fr) minmax(150px,23dvh)!important;
    gap:8px 12px!important;
  }
  .st-key-dashboard-desktop-detail > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-analysis-section) {
    grid-column:1 / -1!important;grid-row:1!important;
  }
  .st-key-dashboard-desktop-detail > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-selection-section) {
    grid-column:1!important;grid-row:2!important;
    height:100%!important;max-height:100%!important;
    min-height:0!important;overflow:hidden!important;
  }
  .st-key-dashboard-desktop-detail > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-monitor-section) {
    grid-column:2!important;grid-row:2!important;
  }
  /* Características e F1 compartilham a largura da faixa inferior.
     O conteúdo não deve impor uma altura maior que a linha disponível. */
  .st-key-dashboard-selection-section {
    box-sizing:border-box!important;
    width:100%!important;height:100%!important;max-height:100%!important;
    min-height:0!important;display:grid!important;
    grid-template-columns:repeat(2,minmax(0,1fr))!important;
    grid-template-rows:minmax(0,1fr)!important;
    gap:12px!important;overflow:hidden!important;
  }
  .st-key-dashboard-selection-section > [data-testid="stElementContainer"] {
    min-width:0!important;min-height:0!important;max-height:100%!important;
    overflow:hidden!important;
  }
  .st-key-dashboard-selection-section .churn-bits {
    grid-template-columns:repeat(10,minmax(0,1fr))!important;
  }
  .st-key-dashboard-selection-section .churn-section-top {
    gap:6px!important;margin-bottom:5px!important;
  }
  /* O último passo da execução acrescenta um botão de download ao monitor.
     No projetor, o botão compartilha a linha do título e a fase textual
     redundante é omitida (a geração continua no indicador de progresso). */
  .st-key-dashboard-monitor-section {
    position:relative!important;overflow:hidden!important;
  }
  .st-key-dashboard-monitor-section > [data-testid="stElementContainer"]:has(.churn-phase) {
    display:none!important;
  }
  .st-key-dashboard-monitor-section > [data-testid="stElementContainer"]:has([data-testid="stDownloadButton"]) {
    position:absolute!important;top:0!important;right:0!important;
    width:auto!important;max-width:50%!important;z-index:1!important;
  }
  .st-key-dashboard-monitor-section .churn-monitor-title {
    padding-right:118px!important;
  }
  .st-key-dashboard-monitor-section [data-testid="stDownloadButton"] button {
    min-height:26px!important;font-size:12px!important;padding:0 2px!important;
  }
}


/* Painel técnico desktop: a área do console absorve o espaço restante.
   O histórico longo rola dentro do console e não empurra outros painéis. */
@media (min-width:621px) {
  .st-key-dashboard-monitor-section {
    box-sizing:border-box!important;position:relative!important;
    display:flex!important;flex-direction:column!important;
    gap:6px!important;min-height:0!important;overflow:hidden!important;
  }
  /* Progresso já informa a geração; remover a fase repetida economiza altura. */
  .st-key-dashboard-monitor-section > [data-testid="stElementContainer"]:has(.churn-phase),
  .st-key-dashboard-monitor-section > [data-testid="stElementContainer"]:has([data-testid="stEmpty"]) {
    display:none!important;
  }
  .st-key-dashboard-monitor-section > [data-testid="stElementContainer"]:has([data-testid="stDownloadButton"]) {
    position:absolute!important;top:0!important;right:0!important;
    width:auto!important;max-width:50%!important;z-index:2!important;
  }
  .st-key-dashboard-monitor-section .churn-monitor-title {
    padding-right:120px!important;
  }
  .st-key-dashboard-monitor-section > [data-testid="stElementContainer"]:has(.churn-console) {
    flex:1 1 0px!important;min-height:0!important;max-height:100%!important;
    overflow:hidden!important;
  }
  .st-key-dashboard-monitor-section > [data-testid="stElementContainer"]:has(.churn-console) [data-testid="stMarkdown"],
  .st-key-dashboard-monitor-section > [data-testid="stElementContainer"]:has(.churn-console) [data-testid="stMarkdown"] > div,
  .st-key-dashboard-monitor-section > [data-testid="stElementContainer"]:has(.churn-console) [data-testid="stMarkdownContainer"] {
    box-sizing:border-box!important;height:100%!important;max-height:100%!important;
    min-height:0!important;overflow:hidden!important;
  }
  /* O MarkdownContainer do Streamlit traz margem inferior de -16px.
     Centralizado em um wrapper flex de altura integral, isso desloca o
     console 8px para baixo, além do limite real do monitor. */
  .st-key-dashboard-monitor-section [data-testid="stMarkdownContainer"]:has(.churn-console),
  .st-key-dashboard-monitor-section [data-testid="stMarkdownContainer"]:has(.churn-monitor-title) {
    margin-bottom:0!important;
  }
  .st-key-dashboard-monitor-section > [data-testid="stElementContainer"]:has([data-testid="stProgress"]) {
    margin-top:2px!important;
  }
  .st-key-dashboard-monitor-section .churn-console {
    box-sizing:border-box!important;height:100%!important;max-height:100%!important;
    min-height:0!important;margin:0!important;overflow:hidden!important;
  }
  .st-key-dashboard-monitor-section .churn-console-lines {
    box-sizing:border-box!important;height:100%!important;max-height:100%!important;
    min-height:0!important;overflow-y:auto!important;overflow-x:hidden!important;
  }
}

/* Em desktop, a faixa inferior reúne as características e o monitor.
   Aumenta a área útil do gráfico e impede as duas seções de se sobreporem. */
@media (min-width:1000px) and (min-height:761px) {
  .st-key-dashboard-desktop-detail {
    grid-template-columns:minmax(0,1.3fr) minmax(0,.7fr)!important;
    grid-template-rows:minmax(0,1fr) minmax(186px,23dvh)!important;
    gap:8px 12px!important;
  }
  .st-key-dashboard-desktop-detail > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-analysis-section) {
    grid-column:1 / -1!important;grid-row:1!important;height:100%!important;
  }
  .st-key-dashboard-desktop-detail > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-selection-section) {
    grid-column:1!important;grid-row:2!important;height:100%!important;
    max-height:100%!important;min-height:0!important;overflow:hidden!important;
  }
  .st-key-dashboard-desktop-detail > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-monitor-section) {
    grid-column:2!important;grid-row:2!important;height:100%!important;
    min-height:0!important;overflow:hidden!important;
  }
  .st-key-dashboard-selection-section {
    display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;
    grid-template-rows:minmax(0,1fr)!important;gap:12px!important;
    height:100%!important;min-height:0!important;overflow:hidden!important;
  }
  .st-key-dashboard-selection-section .churn-bits {
    grid-template-columns:repeat(10,minmax(0,1fr))!important;
  }
}

/* Em 1024 px, manter as duas regiões técnicas na mesma faixa inferior.
   Isso libera altura para mostrar o gráfico sem recortar seus eixos. */
@media (min-width:1000px) and (max-width:1150px) and (min-height:761px) {
  .st-key-dashboard-desktop-detail {
    grid-template-rows:minmax(0,1fr) minmax(184px,24dvh)!important;
  }
  .st-key-dashboard-selection-section {
    grid-template-columns:repeat(2,minmax(0,1fr))!important;
    grid-template-rows:minmax(0,1fr)!important;align-content:stretch!important;
    gap:8px!important;
  }
  .st-key-dashboard-selection-section .churn-bits {
    grid-template-columns:repeat(10,minmax(0,1fr))!important;
  }
  .st-key-dashboard-selection-section .churn-section-top {
    flex-wrap:wrap!important;gap:4px!important;margin-bottom:6px!important;
  }
  .st-key-dashboard-selection-section .churn-metrics {
    gap:4px!important;
  }
  .st-key-dashboard-selection-section .churn-metric dt {
    white-space:normal!important;
  }
  .st-key-dashboard-selection-section [data-testid="stMarkdownContainer"]:has(.churn-chromosome),
  .st-key-dashboard-selection-section [data-testid="stMarkdownContainer"]:has(.churn-technical) {
    margin-bottom:0!important;
  }
}

/* Tablet em paisagem: a seleção precisa acomodar também as métricas após
   o cálculo. Manter console dentro de um trilho independente de 126px. */
@media (min-width:621px) and (max-width:999px) and (min-height:800px) {
  .st-key-dashboard-desktop-detail {
    grid-template-rows:minmax(160px,1fr) minmax(255px,auto) minmax(125px,14dvh)!important;
    gap:8px!important;
  }
  /* A faixa de 255px precisa ser ocupada pelo wrapper, que o Streamlit
     deixava em altura automática; com isso as métricas não ficam cortadas. */
  .st-key-dashboard-desktop-detail > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-selection-section) {
    height:100%!important;max-height:100%!important;min-height:0!important;
  }
  .st-key-dashboard-selection-section {
    grid-template-columns:minmax(0,1fr)!important;
    height:100%!important;max-height:100%!important;
    min-height:0!important;overflow:hidden!important;
  }
}

/* Espaçamento coerente entre títulos, conteúdo e bordas dos painéis. */
.st-key-dashboard-client > [data-testid="stLayoutWrapper"]:has(.churn-panel-heading),
.st-key-dashboard-workspace > [data-testid="stLayoutWrapper"]:has(.churn-workspace-heading) {
  margin:0!important;padding:0!important;align-self:start!important;
  min-height:0!important;max-height:26px!important;
}
.st-key-dashboard-client [data-testid="stElementContainer"]:has(.churn-panel-heading),
.st-key-dashboard-workspace [data-testid="stElementContainer"]:has(.churn-workspace-heading),
.st-key-dashboard-client [data-testid="stMarkdownContainer"]:has(.churn-panel-heading),
.st-key-dashboard-workspace [data-testid="stMarkdownContainer"]:has(.churn-workspace-heading) {
  margin:0!important;padding:0!important;min-height:0!important;
}
.churn-panel-heading {line-height:1.2!important;}
.churn-workspace-heading {
  display:flex;align-items:center;justify-content:space-between;
  min-height:24px;gap:12px;margin:0;
}
.churn-run-icon {
  display:inline-flex;align-items:center;justify-content:center;
  width:20px;height:20px;flex:0 0 20px;color:var(--n3-text);
}
.churn-run-spinner::before {
  content:"";display:block;width:16px;height:16px;box-sizing:border-box;
  border:2px solid var(--n3-secondary);border-right-color:transparent;
  border-radius:50%;animation:n3-run-spin .75s linear infinite;
}
.churn-run-check {
  position:relative;border:2px solid var(--n3-text);border-radius:50%;
  width:20px;height:20px;box-sizing:border-box;
  animation:n3-check-in .2s ease-out both;
}
.churn-run-check::before {
  content:"";position:absolute;left:5px;top:2px;
  width:5px;height:9px;box-sizing:border-box;
  border-right:2px solid var(--n3-text);border-bottom:2px solid var(--n3-text);
  transform:rotate(45deg);
}
.churn-run-error::before {
  content:"×";font-size:21px;font-weight:600;color:var(--n3-negative);line-height:1;
}
@keyframes n3-run-spin {to {transform:rotate(360deg);}}
@keyframes n3-check-in {from {opacity:0;transform:scale(.6);}to {opacity:1;transform:scale(1);}}
@media(prefers-reduced-motion:reduce) {
  .churn-run-spinner::before,.churn-run-check::before {animation:none!important;}
}
.churn-comparison .churn-state {
  font-size:13px;margin:0 0 6px;text-align:right;color:var(--n3-muted);
}
.churn-comparison .churn-state.is-error {color:var(--n3-negative);}

/* Quatro abas locais, com rótulos completos mesmo em painéis estreitos. */
.st-key-dashboard-detail-tabs {min-width:0;}
.st-key-dashboard-detail-tabs [data-baseweb="tab-list"] {
  overflow-x:auto!important;overflow-y:hidden!important;
  flex-wrap:nowrap!important;scrollbar-width:thin;
  scrollbar-color:var(--n3-outline) transparent;
}
.st-key-dashboard-detail-tabs [role="tab"] {
  flex:0 0 auto!important;white-space:nowrap!important;
  padding:7px 7px!important;font-size:14px!important;
  color:var(--n3-secondary)!important;
}
.st-key-dashboard-detail-tabs [role="tab"][aria-selected="true"] {
  color:var(--n3-text)!important;font-weight:600!important;
}
.st-key-dashboard-detail-tabs [data-baseweb="tab-panel"] {
  min-width:0!important;padding-top:8px!important;
}

/* O campo de meses utiliza st.number_input como Cobrança e Total cobrado. */
.st-key-dashboard-tenure-control {min-width:0!important;}
@media(max-width:620px) {
  .st-key-dashboard-detail-tabs [role="tab"] {
    font-size:13px!important;padding:7px 8px!important;
  }
}

/* Reduz o espaço das abas no tablet para exibir também o último rótulo. */
@media (min-width:621px) and (max-width:900px) {
  .st-key-dashboard-detail-tabs [data-baseweb="tab-list"] {gap:0!important;}
  .st-key-dashboard-detail-tabs [role="tab"] {
    font-size:13px!important;padding:7px 3px!important;
  }
}
/* A faixa dos campos rápidos passa a uma coluna no tablet estreito. */
@media (min-width:621px) and (max-width:900px) {
  .st-key-dashboard-quick-fields [data-testid="stHorizontalBlock"]:has(.st-key-dashboard-tenure-control),
  .st-key-dashboard-quick-fields [data-testid="stHorizontalBlock"]:has(input[aria-label="Cobrança mensal"]) {
    display:flex!important;flex-direction:column!important;gap:7px!important;
  }
  .st-key-dashboard-quick-fields [data-testid="stHorizontalBlock"]:has(.st-key-dashboard-tenure-control) > [data-testid="stColumn"],
  .st-key-dashboard-quick-fields [data-testid="stHorizontalBlock"]:has(input[aria-label="Cobrança mensal"]) > [data-testid="stColumn"] {
    flex:0 0 auto!important;width:100%!important;min-width:0!important;
  }
}
/* Descrição do arquivo fica na dica; rótulo visível permanece em uma linha. */
.st-key-dashboard-monitor-section [data-testid="stDownloadButton"] button {
  white-space:nowrap!important;
}

</style>
""",
    unsafe_allow_html=True,
)


def _apply_profile(profile_name: str) -> None:
    example = load_profile(ROOT, profile_name)
    st.session_state["customer_values"] = example.copy()
    for feature in FEATURE_COLUMNS:
        st.session_state[f"field_{feature}"] = example[feature]
    st.session_state["field_total_missing"] = example["total_missing"]
    st.session_state["workflow_run"] = None


def _choose_profile() -> None:
    _apply_profile(st.session_state["profile_choice"])


def _reset_profile() -> None:
    _apply_profile(st.session_state["profile_choice"])


def _ensure_widget_field(feature: str) -> None:
    """Recupera o valor salvo quando o Streamlit recria um widget de outra aba."""
    key = f"field_{feature}"
    if key not in st.session_state:
        st.session_state[key] = st.session_state["customer_values"][feature]


def _remember_field(feature: str) -> None:
    """Persiste edições independentemente da existência do widget na tela."""
    saved = st.session_state["customer_values"].copy()
    saved[feature] = st.session_state[f"field_{feature}"]
    st.session_state["customer_values"] = saved


def _on_service_change(feature: str) -> None:
    _remember_field(feature)
    revised = align_services(st.session_state["customer_values"], changed=feature)
    st.session_state["customer_values"] = revised
    dependents = ("MultipleLines",) if feature == "PhoneService" else INTERNET_FEATURES
    for name in dependents:
        st.session_state[f"field_{name}"] = revised[name]


def _form_data() -> dict:
    data = st.session_state["customer_values"].copy()
    # Preserva também edições diretas no estado dos controles ativos.
    for name in (*FEATURE_COLUMNS, "total_missing"):
        key = f"field_{name}"
        if key in st.session_state:
            data[name] = st.session_state[key]
    return data


def _select_field(feature: str, *, disabled: bool = False, help_text: str | None = None) -> None:
    _ensure_widget_field(feature)
    callback = _on_service_change if feature in ("InternetService", "PhoneService") else _remember_field
    st.selectbox(
        LABELS[feature], options_for(feature), format_func=label_for,
        key=f"field_{feature}", on_change=callback, args=(feature,),
        disabled=disabled, help=help_text,
    )


DETAIL_TABS = {
    "Perfil": PROFILE_FEATURES,
    "Conta": BILLING_FEATURES,
    "Serviços": (
        "PhoneService", "MultipleLines", "OnlineSecurity",
        "OnlineBackup", "DeviceProtection",
    ),
    "Extras": ("TechSupport", "StreamingTV", "StreamingMovies"),
}


def _render_client_details() -> None:
    with st.container(key="dashboard-detail-tabs", border=False):
        tabs = st.tabs(list(DETAIL_TABS))
        for name, tab in zip(DETAIL_TABS, tabs):
            with tab:
                for feature in DETAIL_TABS[name]:
                    if feature == "TotalCharges":
                        # Campo numérico renderizado abaixo, com a opção de valor ausente.
                        continue
                    disabled = (
                        feature == "MultipleLines"
                        and st.session_state["customer_values"]["PhoneService"] == "No"
                    ) or (
                        feature in INTERNET_FEATURES
                        and st.session_state["customer_values"]["InternetService"] == "No"
                    )
                    help_text = (
                        "Indisponível quando o cliente não possui telefone."
                        if feature == "MultipleLines" and disabled else
                        "Indisponível sem serviço de internet."
                        if feature in INTERNET_FEATURES and disabled else None
                    )
                    _select_field(feature, disabled=disabled, help_text=help_text)

                if name == "Conta":
                    _ensure_widget_field("total_missing")
                    st.checkbox(
                        "Total cobrado indisponível",
                        key="field_total_missing",
                        on_change=_remember_field, args=("total_missing",),
                    )
                    _ensure_widget_field("TotalCharges")
                    st.number_input(
                        LABELS["TotalCharges"], min_value=0.0, step=1.0,
                        format="%.2f", key="field_TotalCharges",
                        on_change=_remember_field, args=("TotalCharges",),
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


def _render_workspace_heading(status: str, *, slot) -> None:
    """Indicador discreto: sem estado na espera, animação na busca e check final."""
    variants = {
        "running": ("churn-run-spinner", "Executando previsão"),
        "complete": ("churn-run-check", "Previsão concluída"),
        "error": ("churn-run-error", "Execução interrompida"),
    }
    if status in variants:
        css_class, description = variants[status]
        indicator = (
            f'<span class="churn-run-icon {css_class}" role="status" '
            f'aria-label="{description}"></span>'
        )
    else:
        indicator = ""
    slot.markdown(
        f'<header class="churn-workspace-heading" data-run-state="{status}">'
        '<h2 class="churn-panel-heading">Previsão</h2>'
        f'{indicator}</header>',
        unsafe_allow_html=True,
    )


def _render_prediction_comparison(run: dict | None, status: str, *, slot) -> None:
    """Comparação dos modelos, com aviso apenas em caso de erro ou dados alterados."""
    ready = run is not None and status == "complete"
    count = run["summary"]["genetic_count"] if run is not None else None
    reference = _format_probability(run["predictions"]["baseline"]) if ready else ("—", "Aguardando", "")
    genetic = _format_probability(run["predictions"]["genetico"]) if ready else ("—", "Aguardando", "")

    def result(model: str, details: str, entry: tuple[str, str, str]) -> str:
        value, outcome, semantic = entry
        return (f'<div class="churn-model" aria-label="{escape(model)}">'
                f'<div class="churn-model-name">{escape(model)}</div>'
                f'<div class="churn-model-detail">{escape(details)}</div>'
                f'<div class="churn-prediction-value">{escape(value)}</div>'
                f'<div class="churn-outcome {semantic}">{escape(outcome)}</div></div>')

    alert = (
        '<div class="churn-state" role="status">Dados alterados</div>'
        if status == "stale" else
        '<div class="churn-state is-error" role="status">Erro</div>'
        if status == "error" else ""
    )
    markup = ('<section class="churn-comparison" aria-label="Comparação dos modelos">'
              f'{alert}<div class="churn-models">'
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
        '<div class="churn-section-top"><h3>Evolução do F1-score</h3></div>'
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


def _render_technical(run: dict | None, *, slot) -> None:
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
    slot.markdown('<section class="churn-technical" aria-label="Métricas de teste">'
                  '<div class="churn-section-top"><h3>Desempenho no teste reservado</h3></div>'
                  f'<dl class="churn-metrics">{rows}</dl><div class="churn-technical-note">{escape(summary)}</div>'
                  '</section>', unsafe_allow_html=True)


def _render_idle(slots: dict) -> None:
    _render_workspace_heading("idle", slot=slots["heading"])
    _render_prediction_comparison(None, "idle", slot=slots["comparison"])
    slots["phase"].markdown("", unsafe_allow_html=True)
    slots["progress"].empty()
    _render_console([], slot=slots["console"])
    _render_chromosome(tuple(0 for _ in FEATURE_COLUMNS), "Aguardando avaliação", slot=slots["chromosome"])
    _history_chart([], slot=slots["chart"])
    _render_technical(None, slot=slots["technical"])


def _render_finished_run(run: dict, slots: dict) -> None:
    stale = _is_stale(run)
    _render_workspace_heading("stale" if stale else "complete", slot=slots["heading"])
    _render_prediction_comparison(run, "stale" if stale else "complete", slot=slots["comparison"])
    slots["phase"].markdown('<span class="churn-phase">15 gerações concluídas</span>', unsafe_allow_html=True)
    slots["progress"].progress(1.0, text="Geração 15 de 15")
    _render_console(run["events"], slot=slots["console"], complete=True)
    _render_chromosome(run["chromosome"], "Melhor cromossomo", slot=slots["chromosome"])
    _history_chart(run["history"], slot=slots["chart"])
    _render_technical(run, slot=slots["technical"])
    if run.get("events"):
        slots["log"].download_button(
            "Baixar log", "\n".join(run["events"]) + "\n",
            file_name="execucao-genetica.log", mime="text/plain",
            key="download_full_log", type="tertiary",
            help="Baixar o histórico completo da execução genética",
        )


def _execute_full_workflow(customer: dict, slots: dict) -> None:
    """Execução completa ao clicar em Calcular previsão; não altera arquivos salvos."""
    _render_workspace_heading("running", slot=slots["heading"])
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
        _render_workspace_heading("error", slot=slots["heading"])
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
        with st.container(key="dashboard-quick-fields", border=False):
            a, b = st.columns([0.62, 0.38], gap="small", wrap=False)
            with a:
                with st.container(key="dashboard-tenure-control", border=False):
                    st.number_input(
                        "Tempo como cliente",
                        min_value=0, max_value=999, step=1, format="%d",
                        help="Informe o tempo de permanência em meses.",
                        key="field_tenure", on_change=_remember_field, args=("tenure",),
                    )
            with b:
                _select_field("Contract")
            a, b = st.columns([0.55, 0.45], gap="small", wrap=False)
            with a:
                _select_field("InternetService")
            with b:
                _ensure_widget_field("MonthlyCharges")
                st.number_input(LABELS["MonthlyCharges"], min_value=0.0, step=1.0,
                                format="%.2f", key="field_MonthlyCharges",
                                on_change=_remember_field, args=("MonthlyCharges",))
        _render_client_details()
    with st.container(key="dashboard-client-footer", border=False):
        clicked = st.button("Calcular previsão", type="primary", use_container_width=True,
                            disabled=not DATASET.is_file())
        if not DATASET.is_file():
            st.caption("CSV não encontrado em data/raw/")
    return clicked


class _BroadcastSlot:
    """Atualiza as saídas visíveis em desktop e as abas compactas do celular."""

    def __init__(self, *targets):
        self.targets = targets

    def __getattr__(self, method):
        def dispatch(*args, **kwargs):
            output = None
            for index, target in enumerate(self.targets):
                options = dict(kwargs)
                if index and method == "download_button" and "key" in options:
                    options["key"] += "_mobile"
                output = getattr(target, method)(*args, **options)
            return output
        return dispatch


def _workspace_slots() -> dict:
    heading = st.empty()
    comparison = st.empty()
    with st.container(key="dashboard-desktop-detail", border=False):
        with st.container(key="dashboard-analysis-section", border=False):
            chart_desktop = st.empty()
        with st.container(key="dashboard-selection-section", border=False):
            chromosome_desktop = st.empty()
            technical_desktop = st.empty()
        with st.container(key="dashboard-monitor-section", border=False):
            st.markdown('<div class="churn-monitor-title">Monitor</div>', unsafe_allow_html=True)
            phase_desktop = st.empty()
            progress_desktop = st.empty()
            console_desktop = st.empty()
            log_desktop = st.empty()
    # As duas abas pertencem à apresentação móvel. Em desktop a grade técnica
    # acima é mostrada integralmente e o contêiner abaixo fica oculto por CSS.
    with st.container(key="dashboard-mobile-detail", border=False):
        analysis_tab, execution_tab = st.tabs(["Análise", "Execução"])
        with analysis_tab:
            chart_mobile = st.empty()
            chromosome_mobile = st.empty()
            technical_mobile = st.empty()
        with execution_tab:
            phase_mobile = st.empty()
            progress_mobile = st.empty()
            console_mobile = st.empty()
            log_mobile = st.empty()
    return {
        "heading": heading,
        "comparison": comparison,
        "chart": _BroadcastSlot(chart_desktop, chart_mobile),
        "chromosome": _BroadcastSlot(chromosome_desktop, chromosome_mobile),
        "technical": _BroadcastSlot(technical_desktop, technical_mobile),
        "phase": _BroadcastSlot(phase_desktop, phase_mobile),
        "progress": _BroadcastSlot(progress_desktop, progress_mobile),
        "console": _BroadcastSlot(console_desktop, console_mobile),
        "log": _BroadcastSlot(log_desktop, log_mobile),
    }


def main() -> None:
    if "form_initialized" not in st.session_state:
        st.session_state["profile_choice"] = next(iter(PROFILE_FILES))
        _apply_profile(st.session_state["profile_choice"])
        st.session_state["form_initialized"] = True
    elif "customer_values" not in st.session_state:
        # Sessões abertas antes da mudança continuam válidas após atualizar o código.
        profile = load_profile(ROOT, st.session_state["profile_choice"])
        for name in (*FEATURE_COLUMNS, "total_missing"):
            profile[name] = st.session_state.get(f"field_{name}", profile[name])
        st.session_state["customer_values"] = profile

    with st.container(key="dashboard-shell", border=False):
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
                        _render_workspace_heading("error", slot=slots["heading"])
                        slots["technical"].error("Dados do cliente inválidos. Revise os campos.")
                    else:
                        _execute_full_workflow(customer, slots)
                elif st.session_state.get("workflow_run") is not None:
                    _render_finished_run(st.session_state["workflow_run"], slots)
                else:
                    _render_idle(slots)


if __name__ == "__main__":
    main()
