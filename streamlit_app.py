"""Dashboard local da previsão de churn e da execução genética reproduzível.

Execute: python -m streamlit run streamlit_app.py
"""

import math
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
from src.panel_values import (generation_series, impact_values, log_bytes, metric_sections,
                              probability_values, status_values)
from src.workflow_state import (
    fail_attempt, finish_search, new_attempt, record_evaluation,
    record_generation, start_search, view_state,
)
from src.tenure_control import render_tenure_control
from src.client_scroll_cues import mount_client_scroll_cues
from src.example_profiles import (
    MAX_EXAMPLES,
    append_example,
    can_delete_example,
    delete_example,
    initial_examples,
    is_original,
)
from src.ui_data import (
    BILLING_FEATURES,
    INTERNET_FEATURES,
    LABELS,
    PROFILE_FEATURES,
    PROFILE_FILES,
    align_services,
    form_errors,
    format_evaluation_line,
    format_generation_line,
    label_for,
    load_profile,
    model_input,
    options_for,
)

ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "data" / "raw" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"
QUICK_FIELD_COLUMNS = (0.55, 0.45)

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
   Contraste deliberado; gradientes somente como pistas funcionais de rolagem. */
:root {
  color-scheme: dark;
  --n3-font-ui:"Familjen Grotesk","Segoe UI",Arial,sans-serif;
  --n3-bg:#000000; --n3-surface:#0E1013; --n3-control:#17181B;
  --n3-elevated:#202124; --n3-surface-alt:#282A2D;
  --n3-line:#383A3E; --n3-outline:#55585D;
  --n3-text:#F5F5F5; --n3-secondary:#D8D8D8; --n3-muted:#B7B7B7;
  --n3-positive:#5FE29A; --n3-negative:#FF6464;
  --n3-field-height:42px; --n3-field-radius:4px;
  --n3-client-action-height:48px;
  --n3-field-fill:#0E1013; --n3-field-action-fill:#0E1013;
  --n3-field-text-size:14px; --n3-field-text-line:20px;
  /* Ajuste óptico uniforme; o controle selecionável usa seu input real. */
  --n3-field-text-shift:-1px;
  --n3-page-pad:12px; --n3-panel-pad:12px;
  --n3-client-content-inset:10px;
  --n3-client-shadow-top:0; --n3-client-shadow-bottom:0;
  /* Uma intensidade e extensão compartilhadas pelas duas extremidades. */
  --n3-client-shadow-length:52px;
  --n3-client-shadow-strong:rgba(0,0,0,.48);
  --n3-client-shadow-soft:rgba(0,0,0,.20);
  --n3-profile-button-size:32px;--n3-profile-button-gap:4px;
}
html, body, #root {height:100%;overflow:hidden!important;background:var(--n3-bg)!important;}
.stApp,[data-testid="stMain"] {height:100dvh!important;overflow:hidden!important;background:var(--n3-bg)!important;}
[data-testid="stHeader"],[data-testid="stDecoration"],[data-testid="stToolbar"] {display:none!important;}
[data-testid="stMainBlockContainer"] {box-sizing:border-box!important;padding:var(--n3-page-pad)!important;max-width:none!important;height:100dvh!important;overflow:hidden!important;}
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
.st-key-dashboard-shell {height:calc(100dvh - var(--n3-page-pad) - var(--n3-page-pad));width:100%;max-width:1680px;margin:auto;overflow:hidden;}
/* A linha externa e seus wrappers são controlados; o Streamlit cria alturas automáticas. */
.st-key-dashboard-shell [data-testid="stHorizontalBlock"]:has(.st-key-dashboard-client):has(.st-key-dashboard-workspace) {
  /* Âncoras da viewport: impedir altura herdada da grade em janelas menores. */
  position:fixed!important;top:var(--n3-page-pad)!important;right:var(--n3-page-pad)!important;
  bottom:var(--n3-page-pad)!important;left:var(--n3-page-pad)!important;
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
  border-radius:6px!important;padding:var(--n3-panel-pad)!important;overflow:hidden!important;
}
/* Durante o treino, uma cobertura escura ocupa todo o Cliente e
   impede interação com campos, abas, perfis e botão. Usa a mesma opacidade
   da sombra de rolagem; inert é aplicado pelo observador JS para bloquear
   também teclado, foco e tecnologias de entrada alternativas. */
.st-key-dashboard-client[data-n3-interaction-locked="true"]::after {
  content:"";position:absolute;inset:1px;z-index:20;
  border-radius:5px;background:var(--n3-client-shadow-strong);
  pointer-events:auto;touch-action:none;
}
.st-key-dashboard-client {
  position:relative!important;display:grid!important;
  grid-template-columns:minmax(0,1fr)!important;
  grid-template-rows:20px minmax(0,1fr) auto!important;
  gap:var(--n3-panel-pad)!important;align-content:stretch!important;
  /* Uma única coluna ocupa todo o painel, inclusive a faixa do título.
     Evita que o grid implícito se ajuste à largura do conteúdo rolável. */
  container-name:n3-client;container-type:inline-size;
}
.st-key-dashboard-client > [data-testid="stLayoutWrapper"] {min-width:0!important;min-height:0!important;}
/* Camada de rolagem e máscaras: o topo acompanha a janela de conteúdo,
   enquanto o rodapé permanece fixo na grade do painel. */
.st-key-dashboard-client > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-client-fields) {
  position:relative!important;z-index:1!important;
  height:100%!important;max-height:100%!important;overflow:hidden!important;
}
/* Campos e rodapé compartilham a mesma geometria horizontal. As calhas
   bilaterais compensam scrollbars clássicas; o padding cobre as sobrepostas. */
.st-key-dashboard-client-fields,
.st-key-dashboard-client-footer {
  box-sizing:border-box!important;min-width:0!important;width:100%!important;
  scrollbar-gutter:stable both-edges!important;
  padding-inline:var(--n3-client-content-inset)!important;
}
.st-key-dashboard-client-fields {
  height:100%!important;max-height:100%!important;min-height:0!important;
  overflow-y:auto!important;overflow-x:hidden!important;
  scrollbar-width:thin!important;
  scrollbar-color:var(--n3-outline) transparent!important;
}
/* O gradiente superior começa na primeira linha realmente rolável, após o
   espaçamento do título, para cobrir os campos que passam por baixo dele. */
.st-key-dashboard-client > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-client-fields)::before {
  content:"";position:absolute;top:0;left:0;right:0;
  height:var(--n3-client-shadow-length);z-index:2;pointer-events:none;
  background:linear-gradient(to bottom,
    var(--n3-client-shadow-strong) 0%,var(--n3-client-shadow-soft) 48%,rgba(0,0,0,0) 100%);
  opacity:var(--n3-client-shadow-top,0);transition:opacity .16s ease-out;
}
/* O gradiente pertence ao wrapper fixo: o botão pode manter as calhas e
   overflow:hidden sem recortar a sombra projetada sobre os campos. */
.st-key-dashboard-client > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-client-footer) {
  position:relative!important;z-index:3!important;overflow:visible!important;
}
/* overflow:hidden reserva calhas também sem scrollbar visível.
   A sombra fica no wrapper externo, preservando sua projeção superior. */
.st-key-dashboard-client-footer {
  position:relative!important;height:auto!important;
  overflow:hidden!important;scrollbar-width:thin!important;
  padding-top:8px;border-top:0!important;
}
.st-key-dashboard-client > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-client-footer)::before {
  content:"";position:absolute;bottom:100%;left:0;right:0;
  height:var(--n3-client-shadow-length);pointer-events:none;
  background:linear-gradient(to top,
    var(--n3-client-shadow-strong) 0%,var(--n3-client-shadow-soft) 48%,rgba(0,0,0,0) 100%);
  opacity:var(--n3-client-shadow-bottom,0);transition:opacity .16s ease-out;
}
@media(prefers-reduced-motion:reduce) {
  .st-key-dashboard-client > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-client-footer)::before,
  .st-key-dashboard-client > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-client-fields)::before {
    transition:none!important;
  }
}
/* Identificadores discretos, centralizados dentro dos painéis e sem traços. */
.churn-panel-heading {
  display:block!important;box-sizing:border-box!important;width:100%!important;
  height:20px!important;margin:0!important;padding:0!important;
  font-size:16px!important;line-height:20px!important;font-weight:600!important;
  letter-spacing:0!important;white-space:nowrap!important;
  text-align:center!important;color:var(--n3-outline)!important;
}
/* Streamlit 1.67: st.selectbox usa React Aria Group/Input/Button.
   O seletor antigo [data-baseweb="select"] não existe nesta versão.
   Seletores e entradas numéricas compartilham geometria e tipografia. */
.st-key-dashboard-client [data-testid="stWidgetLabel"] {
  box-sizing:border-box!important;display:flex!important;align-items:center!important;
  height:20px!important;min-height:20px!important;max-height:20px!important;
  padding:0!important;margin:0 0 6px!important;
}
.st-key-dashboard-client [data-testid="stWidgetLabel"] p,
.st-key-dashboard-client label p {
  font-size:15px!important;line-height:20px!important;
  color:var(--n3-secondary)!important;margin:0!important;
  transform:translateY(var(--n3-field-text-shift))!important;
}
.st-key-dashboard-client [data-testid="stVerticalBlock"] {gap:.65rem;}
.st-key-dashboard-client-fields [data-testid="stVerticalBlock"] {gap:.62rem;}
.st-key-dashboard-client [data-testid="stSelectbox"] [role="group"],
.st-key-dashboard-client [data-testid="stNumberInput"]
  :is([data-testid="stNumberInputContainer"],[data-baseweb="input"]) {
  box-sizing:border-box!important;width:100%!important;
  height:var(--n3-field-height)!important;min-height:var(--n3-field-height)!important;
  max-height:var(--n3-field-height)!important;
  display:flex!important;align-items:center!important;overflow:hidden!important;
  background:var(--n3-field-fill)!important;border:1px solid var(--n3-outline)!important;
  border-radius:var(--n3-field-radius)!important;
  outline:none!important;box-shadow:none!important;
}
/* Os seletores só recebem borda clara enquanto a lista está expandida.
   Após escolher uma opção ou fechar com Esc, aria-expanded volta a false
   mesmo que o Streamlit mantenha foco DOM no combobox.
   Campos numéricos preservam o contrato separado de :focus-within. */
.st-key-dashboard-client [data-testid="stSelectbox"]
  [role="group"]:has([aria-expanded="true"]),
.st-key-dashboard-client [data-testid="stNumberInput"]
  :is([data-testid="stNumberInputContainer"],[data-baseweb="input"]):focus-within {
  border-color:var(--n3-text)!important;
  outline:none!important;box-shadow:none!important;
}
.st-key-dashboard-client [data-testid="stSelectbox"] input[role="combobox"] {
  box-sizing:border-box!important;flex:1 1 auto!important;width:0!important;
  min-width:0!important;height:calc(var(--n3-field-height) - 2px)!important;
  min-height:0!important;max-height:none!important;
  padding:0 10px!important;border:0!important;border-radius:0!important;
  box-shadow:none!important;outline:0!important;background:transparent!important;
  color:var(--n3-text)!important;font-family:var(--n3-font-ui)!important;
  font-size:var(--n3-field-text-size)!important;line-height:var(--n3-field-text-line)!important;
  transform:translateY(var(--n3-field-text-shift))!important;
}
.st-key-dashboard-client [data-testid="stNumberInput"] input {
  box-sizing:border-box!important;min-width:0!important;
  height:calc(var(--n3-field-height) - 2px)!important;min-height:0!important;
  padding:0 10px!important;background:transparent!important;
  border:0!important;border-radius:0!important;box-shadow:none!important;
  color:var(--n3-text)!important;font-family:var(--n3-font-ui)!important;
  font-size:var(--n3-field-text-size)!important;line-height:var(--n3-field-text-line)!important;
  transform:translateY(var(--n3-field-text-shift))!important;
}
.st-key-dashboard-client [data-n3-invalid="true"] [data-testid="stWidgetLabel"] p,
.st-key-dashboard-client [data-n3-invalid="true"] label p {
  color:#79A9F5!important;
}
.st-key-dashboard-client [data-testid="stSelectbox"][data-n3-invalid="true"] [role="group"],
.st-key-dashboard-client [data-testid="stNumberInput"][data-n3-invalid="true"]
  :is([data-testid="stNumberInputContainer"],[data-baseweb="input"]) {
  border-color:#79A9F5!important;
}
.st-key-dashboard-client-footer a.n3-validation-jump {
  color:#79A9F5!important;font-size:12px;line-height:17px;
  display:inline-flex;align-items:center;min-height:24px;text-decoration:underline;
}
.st-key-dashboard-client-footer a.n3-validation-jump:focus-visible {
  outline:2px solid #79A9F5;outline-offset:2px;
}
/* O botão real de expansão é o StyledOpenButton do Streamlit.
   Estilizar o próprio botão garante que o hover seja visível. */
.st-key-dashboard-client [data-testid="stSelectbox"] button[aria-haspopup="listbox"] {
  box-sizing:border-box!important;flex:0 0 32px!important;
  width:32px!important;min-width:32px!important;
  height:calc(var(--n3-field-height) - 2px)!important;min-height:0!important;
  display:flex!important;align-items:center!important;justify-content:center!important;
  padding:0!important;border:0!important;border-radius:0!important;
  background:var(--n3-field-action-fill)!important;color:var(--n3-secondary)!important;
  cursor:pointer!important;transition:background-color .12s ease!important;
}
.st-key-dashboard-client [data-testid="stSelectbox"] button[aria-haspopup="listbox"]:hover {
  background:var(--n3-elevated)!important;
}
/* Os botões internos herdam o indicador de foco da borda da caixa. */
.st-key-dashboard-client [data-testid="stSelectbox"] button[aria-haspopup="listbox"]:focus-visible,
.st-key-dashboard-client [data-testid="stNumberInput"] button:focus-visible {
  outline:none!important;box-shadow:none!important;
}
/* A lista do st.selectbox é um Popover do React Aria, inserido em um
   portal separado do botão. A seta só inicia a transição DEPOIS que esse
   popover é montado; o clique e a abertura nativa não aguardam a rotação. */
.st-key-dashboard-client [data-testid="stSelectbox"] button[aria-haspopup="listbox"] svg {
  color:inherit!important;
  transform-origin:center center!important;
  transform:rotate(0deg)!important;
  transition:transform .16s ease-in-out!important;
}
body:has([data-testid="stSelectboxVirtualDropdown"])
  .st-key-dashboard-client [data-testid="stSelectbox"]
  [role="group"]:has([aria-expanded="true"]) button[aria-haspopup="listbox"] svg {
  transform:rotate(180deg)!important;
}
@media(prefers-reduced-motion:reduce) {
  .st-key-dashboard-client [data-testid="stSelectbox"] button[aria-haspopup="listbox"] svg {
    transition:none!important;
  }
}
.st-key-dashboard-client [data-testid="stNumberInput"] button {
  box-sizing:border-box!important;min-width:32px!important;width:32px!important;
  height:calc(var(--n3-field-height) - 2px)!important;min-height:0!important;
  padding:0!important;display:flex!important;align-items:center!important;
  justify-content:center!important;background:var(--n3-field-action-fill)!important;
  border:0!important;border-radius:0!important;color:var(--n3-secondary)!important;
}
/* A cor acompanha o último movimento real do ponteiro; a remoção da marca
   no pointerdown evita hover obsoleto no botão vizinho após um rerun. */
.st-key-dashboard-client [data-testid="stNumberInput"]
  button[data-n3-pointer-hover="true"]:not(:disabled) {
  background:var(--n3-elevated)!important;
}
.st-key-dashboard-client-footer [data-testid="stButton"] button[kind="primary"],
.st-key-dashboard-client-footer button {
  height:var(--n3-client-action-height)!important;
  min-height:var(--n3-client-action-height)!important;
  background:var(--n3-text)!important;color:#000!important;
  border:1px solid var(--n3-text)!important;border-radius:var(--n3-field-radius)!important;
  font-family:var(--n3-font-ui)!important;
  font-size:var(--n3-field-text-size)!important;
  line-height:var(--n3-field-text-line)!important;font-weight:600!important;
}
.st-key-dashboard-client-footer [data-testid="stButton"] button p {
  font-family:inherit!important;font-size:inherit!important;
  line-height:inherit!important;font-weight:inherit!important;
}
/* O hover fica desarmado ao terminar o processamento enquanto o ponteiro
   permanece sobre o botão. A saída do ponteiro o habilita novamente. */
.st-key-dashboard-client-footer button:hover:not(:disabled):not([data-n3-hover-ready="false"]) {
  background:var(--n3-secondary)!important;border-color:var(--n3-secondary)!important;
}
/* O estado ocupado é cinza médio, separado do hover cinza-claro. */
.st-key-dashboard-client-footer [data-testid="stButton"] button[kind="primary"]:disabled,
.st-key-dashboard-client-footer button:disabled {
  background:var(--n3-outline)!important;border-color:var(--n3-outline)!important;
  color:var(--n3-text)!important;opacity:1!important;cursor:default!important;
}
/* As reticências evoluem somente no navegador, com largura reservada para
   não deslocar o texto. A legenda sem pontos continua acessível no botão. */
.st-key-dashboard-client-footer button[data-n3-prediction-state="running"] p::after {
  content:".";
  display:inline-block;min-width:1.7em;text-align:left;white-space:pre;
  font-family:inherit!important;font-size:inherit!important;line-height:inherit!important;
  animation:n3-calculating-ellipsis 1.35s linear infinite;
}
@keyframes n3-calculating-ellipsis {
  0%,32.99% {content:".";}
  33%,65.99% {content:"..";}
  66%,100% {content:"...";}
}
@media(prefers-reduced-motion:reduce) {
  .st-key-dashboard-client-footer button[data-n3-prediction-state="running"] p::after {
    animation:none!important;content:"...";
  }
}
.st-key-dashboard-client-footer button:focus-visible {
  outline:2px solid var(--n3-bg)!important;outline-offset:-4px!important;
}
.st-key-dashboard-client-fields button[kind="tertiary"],
.st-key-dashboard-client-fields button {font-size:14px!important;color:var(--n3-secondary)!important;}
/* Perfis e ações pertencem a uma única linha alinhada verticalmente.
   Apenas números e '+' são circulares. Restaurar e Excluir são quadrados
   com os mesmos tokens e dimensões, sem ajustes individuais de posição. */
.churn-profile-label {
  display:block;min-height:20px;margin:0 0 6px;padding:0;
  font-size:15px;line-height:20px;color:var(--n3-secondary);
  transform:translateY(var(--n3-field-text-shift));
}
.st-key-dashboard-profile-picker {box-sizing:border-box!important;min-width:0!important;width:100%!important;}
.st-key-dashboard-profile-picker [data-testid="stMarkdownContainer"]:has(.churn-profile-label) {
  margin:0!important;padding:0!important;
}
/* Ações ocupam duas células fixas; os cinco perfis usam o espaço restante.
   As proporções padrão de st.columns deixam o quinto perfil fora da coluna
   e recortam o botão Excluir em painéis de 300px. */
.st-key-dashboard-profile-picker [data-testid="stHorizontalBlock"]:has(.st-key-dashboard-profile-choices):has(.st-key-dashboard-profile-actions) {
  display:grid!important;
  grid-template-columns:minmax(0,1fr) calc(2 * var(--n3-profile-button-size) + var(--n3-profile-button-gap))!important;
  align-items:center!important;column-gap:var(--n3-profile-button-gap)!important;
}
.st-key-dashboard-profile-picker [data-testid="stHorizontalBlock"]:has(.st-key-dashboard-profile-choices):has(.st-key-dashboard-profile-actions) > [data-testid="stColumn"] {
  box-sizing:border-box!important;min-width:0!important;width:100%!important;
  max-width:none!important;flex:none!important;
}
.st-key-dashboard-profile-choices,
.st-key-dashboard-profile-actions {
  box-sizing:border-box!important;min-width:0!important;width:100%!important;
  height:42px!important;min-height:42px!important;
  display:flex!important;align-items:center!important;
}
.st-key-dashboard-profile-choices > [data-testid="stVerticalBlock"],
.st-key-dashboard-profile-actions > [data-testid="stVerticalBlock"] {
  min-width:0!important;width:100%!important;
}
.st-key-dashboard-profile-choices [data-testid="stHorizontalBlock"],
.st-key-dashboard-profile-actions [data-testid="stHorizontalBlock"] {
  display:flex!important;gap:var(--n3-profile-button-gap)!important;
  align-items:center!important;flex-wrap:nowrap!important;width:100%!important;
}
/* Impede scrollLeft automático ao clicar no quinto exemplo, que recortava o primeiro. */
.st-key-dashboard-profile-choices [data-testid="stHorizontalBlock"] {justify-content:flex-start!important;overflow:visible!important;}
.st-key-dashboard-profile-actions [data-testid="stHorizontalBlock"] {justify-content:flex-end!important;}
.st-key-dashboard-profile-choices [data-testid="stColumn"],
.st-key-dashboard-profile-actions [data-testid="stColumn"] {
  flex:0 0 var(--n3-profile-button-size)!important;
  box-sizing:border-box!important;min-width:var(--n3-profile-button-size)!important;
  max-width:var(--n3-profile-button-size)!important;width:var(--n3-profile-button-size)!important;
}
.st-key-dashboard-profile-choices [data-testid="stButton"] button,
.st-key-dashboard-profile-actions [data-testid="stButton"] button {
  box-sizing:border-box!important;
  width:var(--n3-profile-button-size)!important;min-width:var(--n3-profile-button-size)!important;
  max-width:var(--n3-profile-button-size)!important;
  height:var(--n3-profile-button-size)!important;min-height:var(--n3-profile-button-size)!important;
  max-height:var(--n3-profile-button-size)!important;
  padding:0!important;border:1px solid var(--n3-outline)!important;
  display:flex!important;align-items:center!important;justify-content:center!important;
  background:var(--n3-field-fill)!important;color:var(--n3-secondary)!important;
}
.st-key-dashboard-profile-choices [data-testid="stButton"] button {
  border-radius:50%!important;font-size:14px!important;font-weight:600!important;
  line-height:1!important;font-variant-numeric:tabular-nums!important;
}
.st-key-dashboard-profile-actions [data-testid="stButton"] button {
  position:relative!important;border-radius:var(--n3-field-radius)!important;
}
.st-key-dashboard-profile-choices [data-testid="stButton"] button:hover,
.st-key-dashboard-profile-actions [data-testid="stButton"] button:hover:not(:disabled) {
  background:var(--n3-elevated)!important;color:var(--n3-text)!important;
}
.st-key-dashboard-profile-choices [data-testid="stButton"] button[kind="primary"] {
  border-color:var(--n3-text)!important;color:var(--n3-text)!important;
  background:var(--n3-elevated)!important;
}
.st-key-dashboard-profile-actions [data-testid="stButton"] button:disabled {
  background:var(--n3-bg)!important;color:var(--n3-outline)!important;
  border-color:var(--n3-line)!important;opacity:.65!important;cursor:default!important;
}
.st-key-dashboard-profile-choices [data-testid="stButton"] button:focus-visible,
.st-key-dashboard-profile-actions [data-testid="stButton"] button:focus-visible {
  outline:2px solid var(--n3-text)!important;outline-offset:2px!important;
}
.st-key-dashboard-profile-actions [data-testid="stButton"] button > div {
  position:static!important;margin:0!important;padding:0!important;
}
.st-key-dashboard-profile-actions [data-testid="stIconMaterial"] {
  position:absolute!important;left:50%!important;top:50%!important;
  transform:translate(-50%,-50%)!important;box-sizing:border-box!important;
  display:flex!important;align-items:center!important;justify-content:center!important;
  width:calc(var(--n3-profile-button-size) * .64)!important;
  height:calc(var(--n3-profile-button-size) * .64)!important;
  margin:0!important;padding:0!important;line-height:1!important;
  font-size:calc(var(--n3-profile-button-size) * .64)!important;
  text-align:center!important;
}
.st-key-dashboard-profile-actions [data-testid="stButton"] button p {
  position:absolute!important;width:1px!important;height:1px!important;
  overflow:hidden!important;clip-path:inset(50%)!important;white-space:nowrap!important;
}
@media(max-width:1150px) {
  :root {--n3-profile-button-size:28px;--n3-profile-button-gap:3px;}
}
@media(max-width:900px) {
  :root {--n3-profile-button-size:26px;--n3-profile-button-gap:2px;}
}
/* Área analítica: cinco seções com função definida, uma só superfície principal. */
.st-key-dashboard-workspace {
  display:grid!important;grid-template-rows:auto auto minmax(150px,1fr) auto minmax(116px,19dvh)!important;
  gap:var(--n3-panel-pad)!important;align-content:stretch!important;
}
.st-key-dashboard-workspace > [data-testid="stLayoutWrapper"] {min-width:0!important;min-height:0!important;overflow:hidden!important;}
.st-key-dashboard-analysis-section {height:100%!important;min-height:0!important;overflow:hidden!important;}
.st-key-dashboard-selection-section {display:grid!important;grid-template-columns: minmax(0,1fr) minmax(0,1fr)!important;gap:22px!important;min-height:0!important;overflow:hidden!important;align-items:start;}
.st-key-dashboard-monitor-section {height:100%!important;min-height:0!important;overflow:auto!important;scrollbar-color:var(--n3-outline) transparent;scrollbar-width:thin;}
.st-key-dashboard-workspace > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-analysis-section),
.st-key-dashboard-workspace > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-monitor-section) {height:100%!important;min-height:0!important;overflow:hidden!important;}
.n3-status {box-sizing:border-box;display:grid;grid-template-columns:minmax(175px,1.3fr) minmax(130px,2fr) minmax(85px,.65fr) minmax(105px,.75fr);align-items:center;min-height:90px;background:var(--n3-control);border:1px solid var(--n3-line);border-radius:6px;padding:12px 0;gap:0;}
.n3-status > div {min-width:0;padding:0 14px;}
.n3-status > div+div {border-left:1px solid var(--n3-line);}
.n3-status-identity {display:flex;gap:12px;align-items:center;}
.n3-status-icon {flex:0 0 34px;width:34px;height:34px;border:1px solid currentColor;border-radius:50%;display:grid;place-items:center;font-size:23px;line-height:1;color:var(--n3-muted);}
.n3-status-icon.is-negative {color:var(--n3-negative);}
.n3-status-icon.is-positive {color:var(--n3-positive);}
.n3-status-icon.is-error {color:#E94B75;}
.n3-status-icon.is-invalid {color:#79A9F5;}
.n3-status-icon.is-stale {color:#E6C35C;}
.n3-status-title {font-size:15px;font-weight:600;line-height:20px;overflow-wrap:anywhere;}
.n3-status-note {font-size:12px;color:var(--n3-muted);line-height:17px;}
.n3-status-number {font-size:22px;font-weight:600;line-height:29px;font-variant-numeric:tabular-nums;}
.n3-status-segments {display:grid;grid-template-columns:repeat(15,minmax(0,1fr));gap:3px;margin-top:8px;}
.n3-status-segments span {height:10px;background:var(--n3-surface-alt);border-radius:2px;}
.n3-status-segments span.is-done {background:var(--n3-text);}
.n3-risk-scale {display:flex;justify-content:space-between;font-size:12px;color:var(--n3-muted);font-variant-numeric:tabular-nums;margin-top:5px;}
.n3-risk-track {position:relative;height:10px;margin-top:10px;background:linear-gradient(to right,#222A25 0 50%,#2C2324 50% 100%);border-radius:3px;}
.n3-risk-fill {height:100%;border-radius:3px;background:var(--n3-positive);}
.n3-risk-fill.is-negative {background:var(--n3-negative);}
.n3-risk-threshold {position:absolute;left:50%;top:-3px;bottom:-3px;width:1px;background:var(--n3-secondary);z-index:1;}
.n3-prob-suffix {font-size:24px;}
.churn-prediction-value.is-unavailable {font-size:24px;overflow-wrap:anywhere;line-height:1.5;}
.churn-comparison .churn-models {gap:16px;}
.churn-comparison .churn-model {box-sizing:border-box;min-height:146px;background:var(--n3-control);border:1px solid var(--n3-line);border-radius:6px;padding:12px 20px;}
.churn-comparison .churn-model+.churn-model {border:1px solid var(--n3-line);padding:12px 20px;}
@media(max-width:1150px) {
  .n3-status {grid-template-columns:repeat(2,minmax(0,1fr));row-gap:12px;}
  .n3-status > div:nth-child(3) {border-left:0;}
  .churn-comparison .churn-model,.churn-comparison .churn-model+.churn-model {padding:10px 12px;}
}
@media(max-width:620px) {
  .n3-status > div {padding:0 8px;}
  .n3-status-identity {gap:6px;}
  .n3-status-icon {width:26px;height:26px;flex-basis:26px;font-size:16px;}
  .n3-status-title {font-size:13px;}
  .churn-comparison .churn-models {gap:8px;}
  .churn-comparison .churn-model,.churn-comparison .churn-model+.churn-model {padding:8px;}
  .churn-prediction-value.is-unavailable {font-size:16px;}
}
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
/* Cartões do resumo inferior, com a mesma superfície dos resultados. */
.churn-chart,.churn-chromosome,.n3-impact,.st-key-dashboard-monitor-section {
  box-sizing:border-box;background:var(--n3-control);border:1px solid var(--n3-line);
  border-radius:6px;padding:12px 14px;
}
.churn-chart .churn-section-top {align-items:center;flex-wrap:wrap;gap:4px 12px;}
.n3-chart-legend {display:flex;gap:14px;align-items:center;font-size:12px;color:var(--n3-secondary);}
.n3-chart-legend span {display:inline-flex;gap:5px;align-items:center;}
.n3-chart-legend i {width:18px;height:2px;background:var(--n3-text);display:inline-block;}
.n3-chart-legend .n3-f1-key {background:#A6A9AE;}
.churn-chart-line.n3-f1-line {stroke:#A6A9AE;stroke-width:1.8;stroke-dasharray:5 4;}
.n3-chart-point {outline:none;cursor:help;}
.n3-chart-point:focus-visible .n3-chart-dot {stroke:#79A9F5;stroke-width:2;vector-effect:non-scaling-stroke;}
.n3-chart-dot {fill:var(--n3-text);}
.churn-chromosome .churn-bits {grid-template-columns:repeat(10,minmax(0,22px));gap:2px;justify-content:center;}
.churn-chromosome .churn-bit {height:29px;cursor:help;font-weight:500;}
.churn-bit:focus-visible {outline:2px solid #79A9F5;outline-offset:1px;}
.churn-chromosome .churn-section-top {flex-wrap:wrap;gap:4px;}
.n3-impact .churn-metrics {gap:6px;}
.n3-impact .churn-metric dt {white-space:normal;}
.n3-impact .churn-metric dd {font-size:18px;white-space:normal;}
.n3-impact .is-negative {color:var(--n3-negative);}
.n3-impact .is-positive {color:var(--n3-positive);}
.n3-impact .n3-workspace-link {display:block;margin-top:10px;padding-top:9px;border-top:1px solid var(--n3-line);}
.n3-impact .churn-technical-note {min-height:30px;}
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
  .churn-prediction-value {font-size:32px;}
  .st-key-dashboard-selection-section {gap:12px!important;}
  .churn-bit {height:24px;font-size:11px;}
  .churn-metric dd {font-size:18px;}
}
@media(max-width:900px) {
  :root {--n3-page-pad:10px;--n3-panel-pad:10px;}
  .st-key-dashboard-shell [data-testid="stHorizontalBlock"]:has(.st-key-dashboard-client):has(.st-key-dashboard-workspace) {
    grid-template-columns:270px minmax(0,1fr)!important;gap:8px!important;
  }
  .st-key-dashboard-selection-section {grid-template-columns:1fr!important;overflow-y:auto!important;}
  .churn-model-name {font-size:15px;}
  .churn-prediction-value {font-size:27px;}
  .churn-bits {gap:2px;}
}
@media(max-height:760px) and (min-width:621px) {
  .st-key-dashboard-workspace {grid-template-rows:auto auto minmax(105px,1fr) auto minmax(90px,16dvh)!important;}
  .churn-model-detail {font-size:12px;}
  .churn-prediction-value {font-size:32px;}
  .churn-comparison {padding-bottom:7px;}
  .churn-console-lines {max-height:52px;min-height:32px;}
  .churn-chart-caption {font-size:12px;}
  .churn-section-top {margin-bottom:5px;}
  .churn-bit {height:23px;}
}
@media(max-width:620px) {
  :root {
    --n3-page-pad:8px;--n3-panel-pad:8px;
    --n3-client-action-height:44px;
  }
  /* Grade de dois painéis com margens simétricas na viewport. */
  .st-key-dashboard-shell [data-testid="stHorizontalBlock"]:has(.st-key-dashboard-client):has(.st-key-dashboard-workspace) {
    position:fixed!important;display:grid!important;
    grid-template-columns:minmax(0,1fr)!important;
    grid-template-rows:minmax(0,36fr) minmax(0,64fr)!important;
    gap:8px!important;box-sizing:border-box!important;
    width:auto!important;height:auto!important;
    max-height:calc(100dvh - var(--n3-page-pad) - var(--n3-page-pad))!important;
    min-height:0!important;margin:0!important;overflow:hidden!important;align-content:stretch!important;
  }
  .st-key-dashboard-client,.st-key-dashboard-workspace {height:100%!important;max-height:100%!important;min-height:0!important;}
  .churn-panel-heading {font-size:14px!important;}
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

/* A navegação e o conteúdo compartilham uma única estrutura em todas as larguras.
   O painel Cliente mantém a geometria da baseline até a revisão responsiva. */
.st-key-dashboard-workspace {
  grid-template-columns:minmax(0,1fr)!important;
  grid-template-rows:20px minmax(0,1fr)!important;
  min-height:0!important;
}
.st-key-dashboard-workspace > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-prediction-tabs),
.st-key-dashboard-prediction-tabs {
  width:100%!important;height:100%!important;min-height:0!important;overflow:hidden!important;
}
.st-key-dashboard-prediction-tabs [data-testid="stTabs"] {
  display:flex!important;flex-direction:column!important;min-height:0!important;
  height:100%!important;overflow:hidden!important;gap:0!important;
}
.st-key-dashboard-prediction-tabs [role="tablist"] {
  flex:0 0 auto!important;display:flex!important;gap:4px!important;
  overflow-x:auto!important;overflow-y:hidden!important;scrollbar-width:thin;
  min-height:40px!important;flex-wrap:nowrap!important;
}
.st-key-dashboard-prediction-tabs [role="tab"] {
  flex:0 0 auto!important;white-space:nowrap!important;
  padding:7px 12px!important;min-height:36px!important;
  font-size:14px!important;color:var(--n3-secondary)!important;
}
.st-key-dashboard-prediction-tabs [role="tab"][aria-selected="true"] {
  color:var(--n3-text)!important;font-weight:600!important;
}
.st-key-dashboard-prediction-tabs [role="tab"]:focus-visible {
  outline:2px solid var(--n3-text)!important;outline-offset:-3px!important;
}
.st-key-dashboard-prediction-tabs [role="tabpanel"] {
  flex:1 1 auto!important;min-height:0!important;min-width:0!important;
  overflow-y:auto!important;overflow-x:hidden!important;padding-top:12px!important;
  scrollbar-width:thin;scrollbar-color:var(--n3-outline) transparent;
}
.st-key-dashboard-prediction-tabs [role="tabpanel"] [data-testid="stVerticalBlock"] {min-width:0!important;}
.st-key-dashboard-prediction-panel {display:flex!important;flex-direction:column!important;gap:12px!important;min-width:0!important;}
.st-key-dashboard-analysis-section {height:auto!important;min-height:0!important;overflow:visible!important;}
.st-key-dashboard-analysis-section .churn-chart {height:173px;}
.st-key-dashboard-selection-section {display:grid!important;grid-template-columns:minmax(0,1fr) minmax(0,1fr) minmax(0,.9fr)!important;gap:12px!important;overflow:visible!important;align-items:stretch!important;}
.st-key-dashboard-selection-section > * {min-width:0!important;}
.st-key-dashboard-selection-section .churn-chromosome,.st-key-dashboard-selection-section .n3-impact {min-height:190px;}
.st-key-dashboard-selection-section .churn-chromosome .churn-bits {grid-template-columns:repeat(10,minmax(0,22px));}
@media(max-width:1150px) {
  .st-key-dashboard-selection-section {grid-template-columns:repeat(2,minmax(0,1fr))!important;}
  .st-key-dashboard-selection-section > [data-testid="stLayoutWrapper"]:has(.st-key-dashboard-monitor-section) {grid-column:1/-1;}
}
.st-key-dashboard-monitor-section {height:auto!important;min-height:0!important;overflow:visible!important;}
.st-key-dashboard-monitor-section .churn-console-lines {max-height:112px!important;}
.n3-terminal-log {background:#0A0B0D;border:1px solid var(--n3-line);border-radius:4px;padding:10px;font:13px/1.5 Consolas,"Liberation Mono",monospace;white-space:pre-wrap;overflow-wrap:anywhere;max-height:55dvh;overflow:auto;user-select:text;}
.n3-workspace-link {color:var(--n3-text)!important;font-size:13px;text-decoration:underline;}
.n3-workspace-link:focus-visible {outline:2px solid var(--n3-text);outline-offset:2px;}
@media(min-width:1366px) {
  .st-key-dashboard-shell [data-testid="stHorizontalBlock"]:has(.st-key-dashboard-client):has(.st-key-dashboard-workspace) {
    grid-template-columns:366px minmax(0,1fr)!important;
  }
}
@media(max-width:1150px) {
  .st-key-dashboard-selection-section .churn-bits {grid-template-columns:repeat(10,minmax(0,1fr));}
}
@media(max-width:620px) {
  .st-key-dashboard-prediction-tabs [role="tablist"] {gap:0!important;min-height:36px!important;}
  .st-key-dashboard-prediction-tabs [role="tab"] {padding:6px 7px!important;font-size:12px!important;}
  .st-key-dashboard-selection-section {grid-template-columns:minmax(0,1fr)!important;}
  .st-key-dashboard-analysis-section .churn-chart {height:180px;}
}
.st-key-dashboard-client > [data-testid="stLayoutWrapper"]:has(.churn-panel-heading),
.st-key-dashboard-workspace > [data-testid="stLayoutWrapper"]:has(.churn-workspace-heading) {
  box-sizing:border-box!important;margin:0!important;padding:0!important;
  width:100%!important;min-width:0!important;
  height:20px!important;min-height:0!important;max-height:20px!important;
  align-self:start!important;overflow:visible!important;
}
.st-key-dashboard-client [data-testid="stElementContainer"]:has(.churn-panel-heading),
.st-key-dashboard-workspace [data-testid="stElementContainer"]:has(.churn-workspace-heading),
.st-key-dashboard-client [data-testid="stMarkdownContainer"]:has(.churn-panel-heading),
.st-key-dashboard-workspace [data-testid="stMarkdownContainer"]:has(.churn-workspace-heading) {
  box-sizing:border-box!important;margin:0!important;padding:0!important;
  height:20px!important;min-height:0!important;max-height:20px!important;
}
.churn-workspace-heading {
  position:relative;display:flex;align-items:center;justify-content:center;
  width:100%;height:20px;min-height:20px;margin:0;
}
.churn-run-icon {
  position:absolute;right:0;top:0;
  display:inline-flex;align-items:center;justify-content:center;
  width:20px;height:20px;color:var(--n3-text);
}
.churn-run-spinner::before {
  content:"";display:block;width:16px;height:16px;box-sizing:border-box;
  border:2px solid var(--n3-secondary);border-right-color:transparent;
  border-radius:50%;animation:n3-run-spin .75s linear infinite;
}
.churn-run-check {
  border:2px solid var(--n3-text);border-radius:50%;
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
.st-key-dashboard-detail-tabs [role="tablist"] {
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
/* React Aria usa box-shadow como anel de foco, criando duas barras laterais
   durante capturas. Foco de teclado permanece identificável pela faixa inferior. */
.st-key-dashboard-detail-tabs [role="tab"]:focus,
.st-key-dashboard-detail-tabs [role="tab"][data-focus-visible] {
  outline:none!important;box-shadow:none!important;
}
.st-key-dashboard-detail-tabs [role="tab"]:focus-visible,
.st-key-dashboard-detail-tabs [role="tab"][data-focus-visible] {
  background:var(--n3-elevated)!important;
  box-shadow:inset 0 -2px 0 var(--n3-outline)!important;
}
.st-key-dashboard-detail-tabs [role="tabpanel"] {
  min-width:0!important;padding-top:8px!important;
}

/* O campo de meses utiliza um componente v2 com valor e unidade protegida. */
/* Os quatro campos rápidos preenchem as mesmas duas colunas de largura.
   O componente v2 tem sua própria raiz, mas ocupa 100% do mesmo trilho. */
.st-key-dashboard-quick-fields [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
  min-width:0!important;
}
.st-key-dashboard-tenure-control {
  box-sizing:border-box!important;min-width:0!important;width:100%!important;
}
.st-key-dashboard-tenure-control [data-testid="stCustomComponentV2"] {
  box-sizing:border-box!important;min-width:0!important;width:100%!important;
}
@media(max-width:620px) {
  .st-key-dashboard-detail-tabs [role="tab"] {
    font-size:13px!important;padding:7px 8px!important;
  }
}

/* Reduz o espaço das abas no tablet para exibir também o último rótulo. */
@media (min-width:621px) and (max-width:900px) {
  .st-key-dashboard-detail-tabs [role="tablist"] {gap:0!important;}
  .st-key-dashboard-detail-tabs [role="tab"] {
    font-size:13px!important;padding:7px 3px!important;
  }
}
/* Quando o Cliente perde largura útil, as duas linhas rápidas passam a
   controles empilhados. Isso preserva os rótulos e os steppers nativos.
   A mesma regra serve a desktop estreito, tablet e janelas redimensionadas. */
@container n3-client (max-width:335px) {
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

/* I4: mesmas superfícies, conteúdo semântico e rolagem interna do log. */
.n3-metrics,.n3-methodology {display:flex;flex-direction:column;gap:12px;min-width:0;}
.n3-metrics-header,.n3-method-card,.n3-metrics-summary,.n3-metrics-table {
  background:var(--n3-control);border:1px solid var(--n3-line);border-radius:6px;padding:12px 16px;
}
.n3-metrics-header h3,.n3-methodology h3,.n3-method-card h4 {margin:0 0 6px;font-size:15px;font-weight:600;}
.n3-metrics-header p,.n3-method-card p,.n3-metrics-summary p {margin:4px 0;font-size:13px;line-height:1.5;color:var(--n3-secondary);}
.n3-metrics-table {width:100%;border-collapse:separate;border-spacing:0;table-layout:fixed;font-size:14px;overflow-wrap:anywhere;}
.n3-metrics-table th,.n3-metrics-table td {padding:9px 8px;border-bottom:1px solid var(--n3-line);text-align:left;height:40px;vertical-align:middle;}
.n3-metrics-table tr:last-child th,.n3-metrics-table tr:last-child td {border-bottom:0;}
.n3-metrics-table thead th {font-size:13px;color:var(--n3-secondary);}
.n3-metrics-table th:first-child {width:44%;}
.n3-metrics-table tbody th {font-weight:400;}
.n3-metrics-table td {font-variant-numeric:tabular-nums;font-weight:600;text-align:right;}
.n3-metrics-table thead th:not(:first-child) {text-align:right;}
.n3-metrics-section {margin:0 0 5px;font-size:15px;font-weight:600;}
.n3-metrics-note {font-size:12px;color:var(--n3-muted);margin:7px 0 0;line-height:1.4;}
.n3-method-stats {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;}
.n3-method-stats div {background:var(--n3-control);border:1px solid var(--n3-line);border-radius:6px;padding:10px 12px;min-width:0;}
.n3-method-stats strong {display:block;font-size:22px;font-variant-numeric:tabular-nums;}
.n3-method-stats span {font-size:12px;color:var(--n3-muted);}
.n3-method-grid {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;}
.n3-formula {font-size:15px;color:var(--n3-text);font-weight:600;}
.n3-log-notice {font-size:12px;color:var(--n3-muted);margin:5px 0;}
.n3-terminal-log,.churn-console-lines {background:#0A0B0D;user-select:text;white-space:pre-wrap;overflow-wrap:anywhere;}
.n3-terminal-log {height:clamp(150px,54dvh,650px);max-height:none;overflow:auto;scrollbar-width:thin;scrollbar-color:var(--n3-outline) transparent;}
.n3-terminal-log:focus-visible,.churn-console-lines:focus-visible {outline:2px solid #79A9F5;outline-offset:-2px;}
@media(max-width:620px) {
  .n3-method-stats,.n3-method-grid {grid-template-columns:repeat(2,minmax(0,1fr));}
  .n3-metrics-table {font-size:12px;padding:4px;}
  .n3-metrics-table th,.n3-metrics-table td {padding:7px 4px;}
  .n3-metrics-table thead th {font-size:11px;}
  .n3-method-card,.n3-metrics-header,.n3-metrics-summary {padding:10px;}
  .n3-terminal-log {height:180px;}
}
</style>
""",
    unsafe_allow_html=True,
)


def _ensure_examples() -> None:
    """Inicializa a coleção e migra o perfil de sessões Streamlit anteriores."""
    if "example_profiles" in st.session_state:
        return
    examples = initial_examples(ROOT)
    active = st.session_state.get("profile_choice")
    if active in examples and "customer_values" in st.session_state:
        examples[active]["values"] = st.session_state["customer_values"].copy()
    st.session_state["example_profiles"] = examples


def _save_active_example() -> None:
    """Conserva o rascunho completo antes de trocar o exemplo."""
    name = st.session_state.get("profile_choice")
    if (name in st.session_state.get("example_profiles", {})
            and "customer_values" in st.session_state):
        st.session_state["example_profiles"][name]["values"] = _form_data()


def _apply_profile(profile_name: str, *, preserve_previous: bool = True) -> None:
    _ensure_examples()
    examples = st.session_state["example_profiles"]
    if profile_name not in examples:
        raise ValueError(f"Exemplo desconhecido: {profile_name}")
    if preserve_previous:
        _save_active_example()
    values = examples[profile_name]["values"].copy()
    st.session_state["profile_choice"] = profile_name
    st.session_state["customer_values"] = values.copy()
    for feature in FEATURE_COLUMNS:
        st.session_state[f"field_{feature}"] = values[feature]
    st.session_state["field_total_missing"] = values["total_missing"]
    # A chave do componente textual de Tempo precisa mudar ao carregar valores.
    st.session_state["tenure_revision"] = st.session_state.get("tenure_revision", 0) + 1
    st.session_state["workflow_run"] = None
    st.session_state["workflow_attempt"] = None
    st.session_state["prediction_error"] = None


def _select_example(name: str) -> None:
    if name != st.session_state["profile_choice"]:
        _apply_profile(name)


def _create_example() -> None:
    _ensure_examples()
    values = _form_data()
    _save_active_example()
    name = append_example(st.session_state["example_profiles"], values)
    _apply_profile(name)


def _reset_profile() -> None:
    _ensure_examples()
    name = st.session_state["profile_choice"]
    entry = st.session_state["example_profiles"][name]
    entry["values"] = entry["original"].copy()
    _apply_profile(name, preserve_previous=False)


def _is_profile_pristine() -> bool:
    _ensure_examples()
    return is_original(
        st.session_state["example_profiles"],
        st.session_state["profile_choice"],
        _form_data(),
    )


def _delete_active_example() -> str:
    """Remove o exemplo selecionado, seleciona o anterior e invalida a previsão."""
    _ensure_examples()
    current = st.session_state["profile_choice"]
    previous = delete_example(st.session_state["example_profiles"], current)
    # A entrada excluída deixou de existir e as posteriores foram renumeradas:
    # nunca salvar os widgets antigos sob a chave do novo exemplo.
    _apply_profile(previous, preserve_previous=False)
    return previous


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
    st.session_state["prediction_error"] = None
    attempt = st.session_state.get("workflow_attempt")
    if attempt is not None and attempt["phase"] == "failed":
        st.session_state["workflow_attempt"] = None
    _save_active_example()


def _on_tenure_component_change() -> None:
    """Sincroniza meses antes de cada rerun, mantendo a entrada e o modelo coerentes."""
    key = f'n3-tenure-{st.session_state["tenure_revision"]}'
    component = st.session_state.get(key, {})
    changed = component.get("value") if hasattr(component, "get") else None
    if changed is None:
        return
    value = max(0, min(999, int(changed)))
    if value != st.session_state["field_tenure"]:
        st.session_state["field_tenure"] = value
        _remember_field("tenure")


def _on_service_change(feature: str) -> None:
    _remember_field(feature)
    revised = align_services(st.session_state["customer_values"], changed=feature)
    st.session_state["customer_values"] = revised
    dependents = ("MultipleLines",) if feature == "PhoneService" else INTERNET_FEATURES
    for name in dependents:
        st.session_state[f"field_{name}"] = revised[name]
    _save_active_example()


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
        # A seleção da aba pertence ao estado do widget: reruns provocados
        # pelos campos não podem devolver o usuário automaticamente a Perfil.
        tabs = st.tabs(list(DETAIL_TABS), key="dashboard_client_active_tab",
                       on_change="rerun")
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


def _validation_errors() -> dict[str, str]:
    return form_errors(_form_data())


def _current_customer() -> dict | None:
    if _validation_errors():
        return None
    try:
        return model_input(_form_data())
    except ValueError:
        return None


def _render_client_feedback(errors: dict[str, str]) -> None:
    if errors:
        first, message = next(iter(errors.items()))
        tab = next((name for name, features in DETAIL_TABS.items() if first in features), None)
        location = f" ({tab})" if tab else ""
        count = len(errors)
        prefix = "1 campo inválido" if count == 1 else f"{count} campos inválidos"
        descriptors = "".join(
            f'<span hidden id="n3-validation-{escape(feature)}" '
            f'data-n3-error-label="{escape(LABELS[feature], quote=True)}" '
            f'data-n3-error-tab="{escape(next((n for n, fs in DETAIL_TABS.items() if feature in fs), ""), quote=True)}">'
            f'{escape(detail)}</span>'
            for feature, detail in errors.items()
        )
        st.markdown(
            '<div class="n3-client-validation" id="n3-client-validation" role="status" '
            'style="color:#79A9F5;font-size:12px;line-height:17px">'
            f'{prefix} · {escape(LABELS[first] + location)}: {escape(message)} '
            '<a class="n3-validation-jump" href="#n3-client-validation">Corrigir</a>'
            f'{descriptors}</div>',
            unsafe_allow_html=True,
        )
    elif st.session_state.get("prediction_error") and (
        st.session_state.get("workflow_attempt") or {}
    ).get("phase") == "failed":
        st.markdown(
            '<div role="status" style="color:#E94B75;font-size:12px;line-height:17px">'
            f'{escape(st.session_state["prediction_error"])}</div>', unsafe_allow_html=True,
        )


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
        '<div class="churn-panel-heading" role="heading" aria-level="2">Previsão</div>'
        f'{indicator}</header>',
        unsafe_allow_html=True,
    )


def _render_status(status: str, data: dict | None, *, slot, phase: str = "") -> None:
    values = status_values(data, now=perf_counter())
    title, symbol, semantic = {
        "idle": ("Aguardando", "—", ""),
        "running": ("Em execução", "↻", ""),
        "stale": ("Dados alterados", "!", "is-stale"),
        "invalid": ("Dados inválidos", "!", "is-invalid"),
        "error": ("Falha na execução", "×", "is-error"),
        "complete": ("Previsão concluída", "✓", ""),
    }[status]
    if status == "complete" and data is not None:
        _, outcome, semantic = probability_values(data["predictions"]["genetico"])
        title = "Cancelamento previsto" if outcome == "Cancelamento" else "Permanência prevista"
        symbol = "!" if outcome == "Cancelamento" else "✓"
    elapsed = values["elapsed"]
    time = "—" if elapsed is None else f"{elapsed:.1f} s".replace(".", ",")
    historical = status in ("stale", "invalid") and data is not None
    time_label = "Última execução" if historical else "Tempo da busca"
    completed = values["generations"]
    total = GeneticConfig().generations
    selected = values["selected"]
    count = "—" if selected is None else f"{selected}/{len(FEATURE_COLUMNS)}"
    reduction = "" if selected is None else f" · −{values['reduction']:.1f}%".replace(".", ",")
    segments = "".join(
        f'<span class="{"is-done" if i < completed else ""}" aria-hidden="true"></span>'
        for i in range(total)
    )
    slot.markdown(
        f'<section class="n3-status" data-n3-status="{status}" aria-label="Status da previsão">'
        f'<div class="n3-status-identity"><span class="n3-status-icon {semantic}" aria-hidden="true">{symbol}</span>'
        f'<div><div class="n3-status-title" role="status">{escape(title)}</div>'
        f'<div class="n3-status-note">{escape(time_label)} · <span class="n3-search-time">{time}</span></div></div></div>'
        f'<div><div class="n3-status-note">{escape(phase or ("Última execução" if historical else "Gerações"))}</div>'
        f'<div class="n3-status-number">{completed}/{total}</div>'
        f'<div class="n3-status-segments" role="progressbar" aria-label="Gerações concluídas" '
        f'aria-valuemin="0" aria-valuemax="{total}" aria-valuenow="{completed}">{segments}</div></div>'
        f'<div><div class="n3-status-number n3-subset-count">{values["subsets"]}</div>'
        '<div class="n3-status-note">Subconjuntos</div></div>'
        f'<div><div class="n3-status-number n3-feature-count">{count}</div>'
        f'<div class="n3-status-note">Características{reduction}</div></div></section>',
        unsafe_allow_html=True,
    )


def _render_prediction_comparison(run: dict | None, status: str, *, slot) -> None:
    """Usa probabilidade de churn e classe real, sem reaproveitar previsões antigas."""
    ready = run is not None and status == "complete"
    count = run["summary"]["genetic_count"] if ready else None
    unavailable = {"stale": "Desatualizada", "invalid": "Indisponível",
                   "error": "Indisponível"}.get(status, "—")

    def result(model: str, details: str, entry: dict | None) -> str:
        probability, outcome, semantic = probability_values(entry)
        if probability is None:
            value = escape(unavailable)
            value_class = "is-unavailable"
            fill = ""
            accessible = "Probabilidade ainda indisponível"
        else:
            value = f"{probability:.2f}".replace(".", ",") + '<span class="n3-prob-suffix">%</span>'
            value_class = ""
            fill = f'<div class="n3-risk-fill {semantic}" style="width:{probability:.8f}%"></div>'
            accessible = f"Probabilidade de cancelamento: {probability:.2f}%".replace(".", ",")
        return (f'<div class="churn-model" aria-label="{escape(model)}">'
                f'<div class="churn-model-name">{escape(model)}</div>'
                f'<div class="churn-model-detail">{escape(details)}</div>'
                f'<div class="churn-prediction-value {value_class}">{value}</div>'
                f'<div class="churn-outcome {semantic}">{escape(outcome or "Probabilidade de cancelamento")}</div>'
                f'<div class="n3-risk-track" role="img" aria-label="{escape(accessible, quote=True)}">'
                f'{fill}<span class="n3-risk-threshold" aria-hidden="true"></span></div>'
                '<div class="n3-risk-scale" aria-hidden="true"><span>0%</span><span>50%</span><span>100%</span></div></div>')

    alert = (
        '<div class="churn-state" role="status">Dados alterados</div>'
        if status == "stale" else
        '<div class="churn-state is-error" role="status">Erro</div>'
        if status == "error" else
        '<div class="churn-state" role="status">Dados inválidos</div>'
        if status == "invalid" else ""
    )
    predictions = run["predictions"] if ready else {}
    markup = ('<section class="churn-comparison" aria-label="Comparação dos modelos">'
              f'{alert}<div class="churn-models">'
              + result("Referência", "19 características", predictions.get("baseline"))
              + result("Seleção genética", f"{count}/19 características" if count is not None else "Aguardando seleção", predictions.get("genetico"))
              + '</div></section>')
    slot.markdown(markup, unsafe_allow_html=True)


def _render_console(events: list[str], *, slot, message: str = "") -> None:
    # A janela do Monitor contém exclusivamente os últimos eventos reais.
    rows = []
    for line in reversed(events[-9:]):
        kind = ("is-result" if line.startswith("[FIM]") else
                "is-step" if line.startswith("[GERAÇÃO]") else "")
        rows.append(f'<span class="churn-log-line {kind}">{escape(line)}</span>')
    notice = f'<p class="n3-log-notice">{escape(message)}</p>' if message else ""
    markup = ('<section class="churn-console" aria-label="Eventos da busca genética">'
              + notice + f'<div class="churn-console-lines" role="region" aria-label="Eventos recentes" '
              f'tabindex="0" data-n3-log-count="{len(events)}">'
              + "".join(rows) + '</div></section>')
    slot.markdown(markup, unsafe_allow_html=True)


def _render_logs(events: list[str], slots: dict, *, historical: bool = False,
                 message: str = "") -> None:
    _render_console(events, slot=slots["console"], message=message)
    title = "Última execução" if historical else "Log da execução"
    notice = f'<p class="n3-log-notice">{escape(message)}</p>' if message else ""
    body = "\n".join(events)
    slots["terminal"].markdown(
        f'<section aria-label="{title}"><div class="churn-section-top"><h3>{title}</h3></div>'
        f'{notice}<div class="n3-terminal-log" role="region" aria-label="Log cronológico" '
        f'tabindex="0" data-n3-log-count="{len(events)}">{escape(body)}</div></section>',
        unsafe_allow_html=True,
    )


def _render_downloads(events: list[str], slots: dict, *, enabled: bool) -> None:
    data = log_bytes(events)
    for key, location in (("monitor_log", "log"), ("terminal_log", "terminal_download")):
        slots[location].download_button(
            "Baixar log", data, file_name="execucao-genetica.log",
            mime="text/plain; charset=utf-8", key=key,
            type="tertiary", disabled=not enabled or not events, on_click="ignore",
            help="Baixar os eventos completos da tentativa (UTF-8)",
        )


def _render_metrics(run: dict | None, slots: dict, *, historical: bool = False) -> None:
    _render_impact(run, slot=slots["technical"], historical=historical)
    _render_technical(run, slot=slots["metrics"], historical=historical, link_metrics=False)


def _render_chromosome(chromosome: tuple[int, ...] | None, title: str, *, slot,
                       customer: dict | None = None) -> None:
    bits = []
    for i, name in enumerate(FEATURE_COLUMNS):
        bit = None if chromosome is None else int(chromosome[i])
        value = "—"
        if customer is not None:
            raw = customer[name]
            value = "Indisponível" if raw is None else label_for(str(raw))
        state = "Ainda indisponível" if bit is None else ("Incluída" if bit else "Excluída")
        description = f"Gene {i + 1} · {LABELS[name]} · Valor: {value} · {state}"
        bits.append(
            f'<span class="churn-bit {"is-on" if bit else ""}" tabindex="0" '
            f'title="{escape(description, quote=True)}" aria-label="{escape(description, quote=True)}">'
            f'{"—" if bit is None else bit}</span>'
        )
    count = "—" if chromosome is None else str(sum(chromosome))
    markup = ('<section class="churn-chromosome" aria-label="Cromossomo de 19 características">'
              f'<div class="churn-section-top"><h3>{escape(title)}</h3>'
              f'<span class="churn-selection-count">{count} / 19</span></div>'
              f'<div class="churn-bits">{"".join(bits)}</div>'
              '<div class="churn-chromosome-note">1 = incluída · 0 = excluída</div></section>')
    slot.markdown(markup, unsafe_allow_html=True)


def _history_chart(history: list[dict], *, slot, historical: bool = False) -> None:
    """Desenha os pares medidos, na mesma escala, sem preencher gerações ausentes."""
    series = generation_series(history)
    observed = [value for _, f1, fitness in series for value in (f1, fitness)]
    # Faixa inicial conforme a referência; ampliar quando necessário.
    lower = min(0.56, min(observed, default=0.56))
    upper = max(0.64, max(observed, default=0.64))
    floor = math.floor(lower * 50) / 50
    ceiling = math.ceil(upper * 50) / 50
    total = GeneticConfig().generations
    def x(generation): return 1000 * (generation - 1) / max(1, total - 1)
    def y(value): return 240 * (1 - (value - floor) / (ceiling - floor))
    def points(index):
        return " ".join(f'{x(row[0]):.2f},{y(row[index]):.2f}' for row in series)
    lines = ""
    if series:
        lines = (f'<polyline class="churn-chart-line n3-f1-line" points="{points(1)}"/>'
                 f'<polyline class="churn-chart-line n3-fitness-line" points="{points(2)}"/>')
    markers = []
    for generation, f1, fitness in series:
        label = f"Geração {generation} · F1 (CV): {f1:.4f} · Fitness: {fitness:.4f}".replace(".", ",")
        markers.append(
            f'<g class="n3-chart-point" tabindex="0" role="img" aria-label="{escape(label, quote=True)}">'
            f'<title>{escape(label)}</title>'
            f'<circle cx="{x(generation):.2f}" cy="{y(fitness):.2f}" r="4" class="n3-chart-dot"/>'
            f'<circle cx="{x(generation):.2f}" cy="{y(f1):.2f}" r="3" fill="#A6A9AE"/></g>'
        )
    grid = ''.join(f'<line x1="0" y1="{i*60}" x2="1000" y2="{i*60}"/>' for i in range(5))
    title = "Evolução da seleção genética · execução anterior" if historical else "Evolução da seleção genética"
    labels = "".join(f'<span>{(floor + (ceiling-floor)*tick/4):.2f}</span>'.replace(".", ",")
                     for tick in range(4, -1, -1))
    markup = (
        '<section class="churn-chart" aria-label="Evolução do F1 e fitness em validação cruzada">'
        f'<div class="churn-section-top"><h3>{title}</h3>'
        '<div class="n3-chart-legend"><span><i class="n3-f1-key"></i>F1 (CV)</span><span><i></i>Fitness</span></div></div>'
        '<div class="churn-chart-plot"><div class="churn-chart-axis-y">' + labels +
        '</div><div class="churn-chart-plot-main">'
        '<svg class="churn-chart-svg" viewBox="0 0 1000 240" preserveAspectRatio="none" '
        f'role="group" aria-label="{len(series)} gerações observadas">'
        f'<g class="churn-chart-grid">{grid}</g>{lines}{"".join(markers)}</svg>'
        '<div class="churn-chart-axis-x"><span>1</span><span>5</span><span>10</span><span>15</span></div>'
        '</div></div></section>'
    )
    slot.markdown(markup, unsafe_allow_html=True)


def _render_impact(run: dict | None, *, slot, historical: bool = False) -> None:
    values = impact_values(run["summary"] if run is not None else None)
    rows = []
    for key, label, decimals, unit in (("f1", "ΔF1", 4, ""),
                                        ("recall_pp", "ΔRecall", 2, " pp"),
                                        ("fn", "ΔFN", 0, "")):
        value = values[key]
        if value is None:
            display, semantic = "—", ""
        else:
            display = f"{value:+.{decimals}f}".replace(".", ",") + unit
            beneficial = value < 0 if key == "fn" else value > 0
            semantic = "" if value == 0 else ("is-positive" if beneficial else "is-negative")
        rows.append(f'<div class="churn-metric"><dt>{label}</dt><dd class="{semantic}">{display}</dd></div>')
    title = "Impacto · execução anterior" if historical else "Impacto da seleção"
    slot.markdown(
        f'<section class="n3-impact" aria-label="{title}"><div class="churn-section-top"><h3>{title}</h3></div>'
        f'<dl class="churn-metrics">{"".join(rows)}</dl>'
        '<div class="churn-technical-note">Genético − referência · teste reservado</div>'
        '<a class="n3-workspace-link" href="#n3-workspace-metrics" data-n3-prediction-tab="Métricas">Ver métricas</a></section>',
        unsafe_allow_html=True,
    )


def _render_technical(run: dict | None, *, slot, historical: bool = False,
                      link_metrics: bool = False) -> None:
    data = run["summary"] if run is not None else None
    folds = GeneticConfig().cv_folds
    test_count = f'{data["test_count"]:,}'.replace(",", ".") if data is not None else "—"
    sections = []
    for title, rows in metric_sections(data):
        lines = "".join(
            f'<tr><th scope="row">{escape(label)}</th><td>{escape(base)}</td><td>{escape(genetic)}</td></tr>'
            for label, base, genetic in rows
        )
        note = (f'<p class="n3-metrics-note">Fitness: F1 médio em {folds} folds estratificados, '
                'com penalização pelo número de características.</p>') if title == "Validação cruzada" else ""
        sections.append(
            f'<section><h4 class="n3-metrics-section">{title}</h4>'
            f'<table class="n3-metrics-table" aria-label="{title}">'
            '<thead><tr><th scope="col">Indicador</th><th scope="col">Referência</th>'
            '<th scope="col">Seleção genética</th></tr></thead>'
            f'<tbody>{lines}</tbody></table>{note}</section>'
        )
    summary = "Aguardando avaliação completa."
    if data is not None:
        delta = impact_values(data)
        reduction = f'{data["reduction_pct"]:.1f}'.replace(".", ",")
        recall = f'{delta["recall_pp"]:+.2f}'.replace(".", ",")
        fn = delta["fn"]
        fn_text = (f"{fn} cancelamentos adicionais não identificados" if fn > 0 else
                   f"{abs(fn)} cancelamentos não identificados a menos" if fn < 0 else
                   "Sem diferença de cancelamentos não identificados")
        summary = (f'−{reduction}% de características ({data["baseline_count"]} → {data["genetic_count"]}) '
                   f'· {recall} p.p. de recall · {fn_text}.')
    title = "Métricas · execução anterior" if historical else "Avaliação dos modelos"
    slot.markdown(
        f'<section class="n3-metrics" aria-label="{title}"><header class="n3-metrics-header">'
        f'<h3>{title}</h3><p>Validação cruzada: {folds} folds estratificados · '
        f'Conjunto de teste: {test_count} clientes · Classe positiva: cancelamento.</p></header>'
        + "".join(sections) +
        f'<section class="n3-metrics-summary"><h4 class="n3-metrics-section">Resumo</h4><p>{escape(summary)}</p></section></section>',
        unsafe_allow_html=True,
    )


def _render_methodology() -> None:
    config = GeneticConfig()
    n = len(FEATURE_COLUMNS)
    def percent(value):
        return f"{100 * value:g}".replace(".", ",") + "%"
    stats = (("7.043", "Clientes"), (str(n), "Características originais"),
             ("26,54%", "Cancelamentos"), (str(config.random_state), "Seed"))
    indicators = "".join(f'<div><strong>{value}</strong><span>{label}</span></div>'
                         for value, label in stats)
    pipeline = (
        ("1 · Preparação dos dados",
         "Exclusão do identificador. Imputação por mediana e moda, one-hot e padronização numérica. "
         "Ajuste do pré-processamento apenas no treino de cada fold e no desenvolvimento final."),
        ("2 · Treino e avaliação",
         "Divisão estratificada 80/20; no estudo original, 5.634 clientes no desenvolvimento e 1.409 no teste. "
         "Regressão logística nos dois modelos, mesmo conjunto de teste reservado e cancelamento como classe positiva."),
        ("3 · Seleção genética",
         f"{n} bits, {config.population_size} indivíduos, {config.generations} gerações, "
         f"torneio de {config.tournament_size}, cruzamento de um ponto ({percent(config.crossover_rate)}), "
         f"mutação por indivíduo ({percent(config.mutation_rate)}), inversão de 1/{n} por bit, "
         f"elitismo {config.elite_count} e CV estratificada de {config.cv_folds} folds."),
        ("4 · Função de fitness",
         f"Fitness = F1 médio (CV) − {str(config.penalty).replace('.', ',')} × k/{n}. "
         "k é o número de características selecionadas; penalização favorece subconjuntos menores."),
    )
    limitations = (
        ("Validação e generalização", "Uma divisão e uma busca; outras amostras e seeds podem alterar os resultados. A seleção por CV também pode introduzir viés."),
        ("Simplificação e desempenho", "A busca não garante ótimo global. Reduzir características pode diminuir a detecção de cancelamentos."),
        ("Representatividade", "O dataset registra gênero em Female/Male e não contempla todos os grupos. Excluir gênero não elimina essa limitação."),
        ("Interpretação", "A previsão é uma estimativa probabilística baseada em associações. Não estabelece relações causais."),
    )
    def cards(items):
        return "".join(f'<section class="n3-method-card"><h4>{escape(title)}</h4><p>{escape(body)}</p></section>'
                       for title, body in items)
    st.markdown(
        '<section class="n3-methodology" aria-label="Metodologia">'
        '<p class="n3-metrics-note">Base de referência do estudo: Telco Customer Churn (Kaggle). '
        'Quantidades históricas do dataset original; características e Seed da configuração atual.</p>'
        f'<div class="n3-method-stats">{indicators}</div>'
        '<h3>Pipeline experimental</h3>'
        f'<div class="n3-method-grid">{cards(pipeline)}</div><h3>Limitações</h3>'
        f'<div class="n3-method-grid">{cards(limitations)}</div></section>',
        unsafe_allow_html=True,
    )


def _render_idle(slots: dict, *, status: str = "idle") -> None:
    _render_workspace_heading(status, slot=slots["heading"])
    _render_status(status, None, slot=slots["status"])
    _render_prediction_comparison(None, status, slot=slots["comparison"])
    message = ("Execução bloqueada pela validação dos dados."
               if status == "invalid" else "Aguardando início da execução.")
    _render_logs([], slots, message=message)
    _render_downloads([], slots, enabled=False)
    _render_chromosome(None, "Aguardando avaliação", slot=slots["chromosome"])
    _history_chart([], slot=slots["chart"])
    _render_metrics(None, slots)


def _render_finished_run(run: dict, slots: dict) -> None:
    status = view_state(running=False, customer=_current_customer(),
                        last_success=run, attempt=None)
    historical = status != "complete"
    _render_workspace_heading(status, slot=slots["heading"])
    _render_prediction_comparison(run, status, slot=slots["comparison"])
    _render_status(status, run, slot=slots["status"])
    notice = ""
    if historical:
        notice = ("[VALIDAÇÃO] Dados inválidos. Nenhuma nova execução iniciada."
                  if status == "invalid" else "[ESTADO] Dados alterados. Execução anterior.")
    _render_logs(run["events"], slots, historical=historical, message=notice)
    _render_chromosome(run["chromosome"],
                       "Subconjunto anterior" if historical else "Melhor cromossomo",
                       slot=slots["chromosome"], customer=run["customer"])
    _history_chart(run["history"], slot=slots["chart"], historical=historical)
    _render_metrics(run, slots, historical=historical)
    _render_downloads(run["events"], slots, enabled=not st.session_state.get("prediction_running", False))


def _execute_full_workflow(customer: dict, slots: dict) -> None:
    """Execução completa ao clicar em Calcular previsão; não altera arquivos salvos."""
    _render_workspace_heading("running", slot=slots["heading"])
    config = GeneticConfig()
    attempt = new_attempt(customer)
    st.session_state["workflow_attempt"] = attempt
    events = attempt["events"]
    history = attempt["history"]
    _render_prediction_comparison(None, "running", slot=slots["comparison"])
    _render_status("running", attempt, slot=slots["status"], phase="Preparando os dados")
    _render_chromosome(None, "Aguardando avaliação",
                       slot=slots["chromosome"])
    _history_chart([], slot=slots["chart"])
    _render_metrics(None, slots)
    _render_downloads([], slots, enabled=False)

    def log(message: str) -> None:
        events.append(message)
        _render_logs(events, slots)

    current_phase = "Preparando os dados"

    def update_status() -> None:
        _render_status("running", attempt, slot=slots["status"], phase=current_phase)

    def phase(label: str, message: str) -> None:
        nonlocal current_phase
        current_phase = label
        update_status()
        log(message)

    def on_evaluation(record: dict[str, object]) -> None:
        record_evaluation(attempt, record)
        update_status()
        if record["etapa"] == "inicio":
            chromosome = tuple(int(bit) for bit in record["cromossomo"])
            _render_chromosome(
                chromosome,
                f"Geração {record['geracao']} · indivíduo {record['individuo']}",
                slot=slots["chromosome"], customer=attempt["customer"],
            )
        log(format_evaluation_line(record))

    def on_generation(record: dict[str, int | float]) -> None:
        record_generation(attempt, record)
        update_status()
        log("[GERAÇÃO] " + format_generation_line(record))
        _history_chart(history, slot=slots["chart"])

    try:
        log("[EXECUÇÃO] Processamento iniciado.")
        phase("Preparando os dados", "[DADOS] Lendo o conjunto Telco Customer Churn")
        dataset = load_dataset(DATASET)
        x_dev, x_test, y_dev, y_test = split_dataset(
            dataset, random_state=config.random_state,
        )
        log(f"[DIVISÃO] {len(dataset)} clientes · {len(x_dev)} desenvolvimento · "
            f"{len(x_test)} teste reservado")
        phase("Validando a referência",
              f"[CV] Regressão logística · {config.cv_folds} folds")
        baseline_cv = evaluate_cv(x_dev, y_dev, n_splits=config.cv_folds,
                                  random_state=config.random_state)
        log(f"[CV] F1 médio de referência: {baseline_cv['f1']['media']:.4f}")
        phase("Buscando subconjuntos de características",
              f"[AG] {config.population_size} indivíduos · "
              f"{config.generations} gerações · {len(FEATURE_COLUMNS)} genes")
        start_search(attempt, perf_counter())
        update_status()
        genetic_result = select_features(
            x_dev, y_dev, config, on_generation=on_generation,
            on_evaluation=on_evaluation,
        )
        finish_search(attempt, genetic_result.elapsed_seconds)
        attempt["chromosome"] = genetic_result.chromosome
        attempt["evaluated_subsets"] = genetic_result.evaluated_subsets
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
        summary = {
            "baseline": base_metrics,
            "genetico": genetic_metrics,
            "baseline_cv_f1": baseline_cv["f1"]["media"],
            "genetic_cv_f1": genetic_result.best_cv_f1,
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
            "elapsed_seconds": genetic_result.elapsed_seconds,
        }
    except Exception:
        fail_attempt(attempt, perf_counter())
        message = ("CSV não encontrado em data/raw/. Adicione o arquivo e tente novamente."
                   if not DATASET.is_file() else
                   "Não foi possível concluir a execução. Verifique os dados e tente novamente.")
        st.session_state["prediction_error"] = message
        events.append("[ERRO] " + message)
        # O rerun de main renderiza a falha e habilita o log parcial.
        # Não registrar novamente os widgets da tentativa em andamento.
        return

    attempt["phase"] = "complete"
    st.session_state["workflow_run"] = run
    st.session_state["prediction_error"] = None
    # main libera o Cliente e solicita um rerun. Os downloads desabilitados
    # já foram registrados neste ciclo; a conclusão é renderizada no próximo.


def _render_failed_attempt(attempt: dict, slots: dict) -> None:
    _render_workspace_heading("error", slot=slots["heading"])
    _render_prediction_comparison(None, "error", slot=slots["comparison"])
    _render_status("error", attempt, slot=slots["status"])
    _render_logs(attempt["events"], slots)
    _render_chromosome(attempt["chromosome"], "Análise de subconjunto", slot=slots["chromosome"],
                       customer=attempt["customer"])
    _history_chart(attempt["history"], slot=slots["chart"])
    _render_metrics(None, slots)
    _render_downloads(attempt["events"], slots,
                      enabled=not st.session_state.get("prediction_running", False))


def _request_prediction() -> None:
    """Widget callback: executado antes do rerun, permitindo renderizar Calculando..."""
    if st.session_state.get("prediction_running"):
        return
    st.session_state["prediction_requested"] = True
    st.session_state["prediction_running"] = True
    st.session_state["prediction_error"] = None


def _prediction_button_label() -> str:
    """Única origem da legenda do botão conforme o estado da execução."""
    if st.session_state.get("prediction_running", False):
        return "Calculando"
    attempt = st.session_state.get("workflow_attempt")
    if attempt is not None and attempt["phase"] == "failed":
        return "Tentar novamente"
    if st.session_state.get("workflow_run") is not None:
        return "Recalcular previsão"
    return "Calcular previsão"


def _render_client_panel() -> bool:
    st.markdown('<div class="churn-panel-heading" role="heading" aria-level="2">Cliente</div>',
                unsafe_allow_html=True)
    with st.container(key="dashboard-client-fields", border=False):
        # Ações superiores: botões circulares representam exemplos independentes.
        with st.container(key="dashboard-profile-picker", border=False):
            st.markdown('<div class="churn-profile-label">Perfil de exemplo</div>',
                        unsafe_allow_html=True)
            a, b = st.columns([0.70, 0.30], gap=None, vertical_alignment="center", wrap=False)
            with a:
                with st.container(key="dashboard-profile-choices", border=False):
                    names = tuple(st.session_state["example_profiles"])
                    slots = st.columns(
                        len(names) + int(len(names) < MAX_EXAMPLES), gap=None, wrap=False,
                    )
                    for index, name in enumerate(names):
                        with slots[index]:
                            st.button(
                                str(index + 1), key=f"select_example_{index + 1}",
                                help=f"Selecionar {name}",
                                type="primary" if name == st.session_state["profile_choice"]
                                else "secondary",
                                on_click=_select_example, args=(name,),
                                use_container_width=True,
                            )
                    if len(names) < MAX_EXAMPLES:
                        with slots[-1]:
                            st.button(
                                "+", key="create_example", help="Criar exemplo a partir do cliente atual",
                                type="secondary", on_click=_create_example,
                                use_container_width=True,
                            )
            with b:
                with st.container(key="dashboard-profile-actions", border=False):
                    restore, delete = st.columns(2, gap=None, wrap=False)
                    with restore:
                        with st.container(key="dashboard-restore-action", border=False):
                            st.button(
                                "Restaurar perfil", icon=":material/history:",
                                help="Restaurar os dados do exemplo selecionado.",
                                key="restore_profile", type="tertiary",
                                disabled=_is_profile_pristine(),
                                on_click=_reset_profile, use_container_width=True,
                            )
                    with delete:
                        with st.container(key="dashboard-delete-action", border=False):
                            st.button(
                                "Excluir perfil", icon=":material/delete_outline:",
                                help="Excluir o exemplo selecionado (exemplos 1 e 2 protegidos).",
                                key="delete_profile", type="tertiary",
                                disabled=not can_delete_example(
                                    st.session_state["example_profiles"],
                                    st.session_state["profile_choice"],
                                ),
                                on_click=_delete_active_example,
                                use_container_width=True,
                            )
        with st.container(key="dashboard-quick-fields", border=False):
            a, b = st.columns(QUICK_FIELD_COLUMNS, gap="small", wrap=False)
            with a:
                with st.container(key="dashboard-tenure-control", border=False):
                    months = render_tenure_control(
                        st, value=int(st.session_state["field_tenure"]),
                        revision=st.session_state["tenure_revision"],
                        on_change=_on_tenure_component_change,
                    )
                    if months != st.session_state["field_tenure"]:
                        st.session_state["field_tenure"] = months
                        _remember_field("tenure")
            with b:
                _select_field("Contract")
            a, b = st.columns(QUICK_FIELD_COLUMNS, gap="small", wrap=False)
            with a:
                _select_field("InternetService")
            with b:
                _ensure_widget_field("MonthlyCharges")
                st.number_input(LABELS["MonthlyCharges"], min_value=0.0, step=1.0,
                                format="%.2f", key="field_MonthlyCharges",
                                on_change=_remember_field, args=("MonthlyCharges",))
        _render_client_details()
    with st.container(key="dashboard-client-footer", border=False):
        errors = _validation_errors()
        _render_client_feedback(errors)
        st.button(
            _prediction_button_label(), key="run_prediction",
            type="primary", use_container_width=True,
            disabled=bool(errors) or st.session_state.get("prediction_running", False),
            on_click=_request_prediction,
        )
    return bool(st.session_state.get("prediction_requested", False))


PREDICTION_TABS = ("Painel", "Terminal", "Métricas", "Metodologia")


def _workspace_slots() -> dict:
    """Uma navegação nativa; todos os conteúdos recebem a mesma execução.

    Trocar aba não solicita rerun, inclusive durante a busca síncrona.
    """
    heading = st.empty()
    with st.container(key="dashboard-prediction-tabs", border=False):
        panel, terminal, metrics, methodology = st.tabs(
            list(PREDICTION_TABS), key="dashboard_prediction_active_tab",
            on_change="ignore",
        )
        with panel:
            with st.container(key="dashboard-prediction-panel", border=False):
                status_slot = st.empty()
                comparison = st.empty()
                with st.container(key="dashboard-analysis-section", border=False):
                    chart = st.empty()
                with st.container(key="dashboard-selection-section", border=False):
                    chromosome = st.empty()
                    technical = st.empty()
                    with st.container(key="dashboard-monitor-section", border=False):
                        st.markdown('<div class="churn-monitor-title">Monitor</div>', unsafe_allow_html=True)
                        console, log = st.empty(), st.empty()
        with terminal:
            terminal_download = st.empty()
            terminal_log = st.empty()
        with metrics:
            metrics_slot = st.empty()
        with methodology:
            _render_methodology()
    return {
        "heading": heading, "comparison": comparison, "chart": chart,
        "chromosome": chromosome, "technical": technical, "status": status_slot,
        "console": console, "log": log,
        "terminal": terminal_log, "terminal_download": terminal_download,
        "metrics": metrics_slot,
    }


def main() -> None:
    _ensure_examples()
    if "form_initialized" not in st.session_state:
        name = st.session_state.get("profile_choice", next(iter(PROFILE_FILES)))
        if name not in st.session_state["example_profiles"]:
            name = next(iter(PROFILE_FILES))
        _apply_profile(name, preserve_previous=False)
        st.session_state["form_initialized"] = True
    elif "customer_values" not in st.session_state:
        # Recupera o exemplo ativo, inclusive depois de remount de sessão.
        _apply_profile(st.session_state["profile_choice"], preserve_previous=False)

    st.session_state.setdefault("tenure_revision", 1)

    with st.container(key="dashboard-shell", border=False):
        client_col, workspace_col = st.columns([0.30, 0.70], gap="small", wrap=True)
        with client_col:
            with st.container(key="dashboard-client", border=True):
                _render_client_panel()
        # O callback antecede o rerun e é a fonte da solicitação.
        requested = bool(st.session_state.pop("prediction_requested", False))
        with workspace_col:
            with st.container(key="dashboard-workspace", border=True):
                slots = _workspace_slots()
                if requested:
                    st.session_state["workflow_attempt"] = None
                    customer = _current_customer()
                    try:
                        if customer is None:
                            st.session_state["prediction_error"] = (
                                "Dados do cliente inválidos. Revise os campos."
                            )
                            previous = st.session_state.get("workflow_run")
                            if previous is not None:
                                _render_finished_run(previous, slots)
                            else:
                                _render_idle(slots, status="invalid")
                        else:
                            _execute_full_workflow(customer, slots)
                    finally:
                        st.session_state["prediction_running"] = False
                    # Atualiza a legenda depois de concluir sem executar o modelo novamente.
                    st.rerun()
                elif _current_customer() is None:
                    previous = st.session_state.get("workflow_run")
                    if previous is not None:
                        _render_finished_run(previous, slots)
                    else:
                        _render_idle(slots, status="invalid")
                elif (st.session_state.get("workflow_attempt") is not None
                      and st.session_state["workflow_attempt"]["phase"] == "failed"):
                    _render_failed_attempt(st.session_state["workflow_attempt"], slots)
                elif st.session_state.get("workflow_run") is not None:
                    _render_finished_run(st.session_state["workflow_run"], slots)
                elif st.session_state.get("prediction_error"):
                    _render_idle(slots)
                    _render_workspace_heading("error", slot=slots["heading"])
                    slots["technical"].error(st.session_state["prediction_error"])
                else:
                    _render_idle(slots)

        # Componente JS sem interface, dentro do shell e fora da grade fixa.
        # Não acrescenta altura ao documento nem desloca campos ou rodapé.
        mount_client_scroll_cues(st)


if __name__ == "__main__":
    main()
