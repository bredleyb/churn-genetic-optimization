"""Interface local para comparar previsões de cancelamento de clientes.

Execute a partir da raiz: python -m streamlit run streamlit_app.py
"""

import json
from html import escape
from pathlib import Path

import streamlit as st
from joblib import load

from src.data import FEATURE_COLUMNS
from src.prediction import predict_customer
from src.ui_data import (
    BILLING_FEATURES,
    INTERNET_FEATURES,
    LABELS,
    PHONE_FEATURES,
    PROFILE_FEATURES,
    PROFILE_FILES,
    align_services,
    experiment_summary,
    label_for,
    load_profile,
    model_input,
    options_for,
)

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
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

# As regras de estilo usam apenas classes HTML criadas pelo próprio projeto.
st.markdown(
    """
<style>
.churn-hero {padding: 7px 0 20px; margin-bottom: 14px; border-bottom: 1px solid #E2E8F0;}
.churn-kicker {font: 700 11px/1.3 sans-serif; letter-spacing: .15em; color: #0F766E; margin: 0 0 11px;}
.churn-title {font: 700 clamp(26px, 3vw, 35px)/1.16 sans-serif; letter-spacing: -.035em;
  color: #0F172A; margin: 0 0 10px;}
.churn-subtitle {color: #516071; font: 400 15px/1.55 sans-serif; max-width: 760px; margin: 0;}
.churn-panel-heading {font: 700 17px/1.35 sans-serif; color: #0F172A; margin: 1px 0 5px;}
.churn-panel-description {font: 400 13px/1.5 sans-serif; color: #516071; margin: 0 0 8px;}
.churn-result {border: 1px solid #E2E8F0; background: #FFFFFF; border-radius: 12px;
  padding: 19px 20px 18px; margin: 12px 0;}
.churn-result-top {display: flex; gap: 12px; align-items: start; justify-content: space-between;}
.churn-model {font: 650 14px/1.35 sans-serif; color: #0F172A; margin-bottom: 4px;}
.churn-model-detail {font: 400 12px/1.4 sans-serif; color: #516071;}
.churn-value {font: 700 clamp(26px, 2.6vw, 34px)/1.15 sans-serif; letter-spacing: -.04em;
  font-variant-numeric: tabular-nums; white-space: nowrap;}
.churn-meter {width: 100%; height: 8px; border-radius: 20px; background: #E2E8F0;
  overflow: hidden; margin-top: 17px;}
.churn-meter > span {display:block; height: 100%; border-radius: 20px;}
.churn-result-bottom {display: flex; align-items: center; justify-content: space-between;
  gap: 12px; margin-top: 11px; flex-wrap: wrap;}
.churn-result-label {font: 650 12px/1.4 sans-serif;}
.churn-small {font: 400 12px/1.45 sans-serif; color: #516071;}
.churn-metrics {width:100%; border-collapse:collapse; margin-top: 8px;
  font: 13px/1.45 sans-serif; font-variant-numeric: tabular-nums;}
.churn-metrics th {text-align:right; font-size:11px; color:#516071; font-weight:650;
  border-bottom:1px solid #E2E8F0; padding:11px 8px;}
.churn-metrics th:first-child {text-align:left;}
.churn-metrics td {text-align:right; border-bottom:1px solid #E2E8F0; padding:10px 8px; color:#0F172A;}
.churn-metrics td:first-child {text-align:left; color:#516071;}
.churn-metrics tr:last-child td {border-bottom:0;}
.churn-stat {margin: 6px 0 0; font: 650 14px/1.45 sans-serif; color:#0F172A;}
.churn-stat strong {color:#0F766E; font-weight:750;}
.churn-note {color:#516071; font:400 12px/1.5 sans-serif; margin:10px 0 2px;}
@media (max-width: 768px) {
  .churn-hero {padding: 0 0 14px; margin-bottom: 8px;}
  .churn-title {font-size: 28px;}
  .churn-subtitle {font-size:14px;}
  .churn-result {padding:15px; margin: 9px 0;}
  .churn-metrics {font-size:12px;}
  .churn-metrics th, .churn-metrics td {padding: 9px 5px;}
}
@media (max-width: 430px) {
  .churn-result-top {gap: 8px;}
  .churn-value {font-size: 25px;}
  .churn-model {font-size: 13px;}
  .churn-model-detail {font-size: 11px;}
}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner=False)
def cached_model(file_path: str, modified_ns: int, file_size: int):
    """Recarrega o modelo se o arquivo local for substituído."""
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
    callback = None
    if feature in ("InternetService", "PhoneService"):
        callback = _on_service_change
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
    p = max(0.0, min(100.0, float(entry["probabilidade_cancelamento"]) * 100.0))
    cancellation = entry["classe"] == 1
    color = "#B42318" if cancellation else "#0F766E"
    status = "Cancelamento previsto" if cancellation else "Permanência prevista"
    detail = f"{feature_count} características" if feature_count is not None else "Modelo treinado"
    st.markdown(
        f"""<section class="churn-result" aria-label="{escape(title)}">
<div class="churn-result-top"><div><div class="churn-model">{escape(title)}</div>
<div class="churn-model-detail">{escape(detail)}</div></div>
<div class="churn-value" style="color:{color}">{p:.2f}%</div></div>
<div class="churn-meter" role="progressbar" aria-label="Probabilidade estimada de cancelamento"
  aria-valuemin="0" aria-valuemax="100" aria-valuenow="{p:.2f}">
<span style="width:{p:.2f}%;background:{color}"></span></div>
<div class="churn-result-bottom"><span class="churn-result-label" style="color:{color}">{status}</span>
<span class="churn-small">Probabilidade de cancelamento</span></div></section>""",
        unsafe_allow_html=True,
    )


def _render_metrics(summary: dict) -> None:
    rows = "".join(
        "<tr><td>" + name + "</td><td>" +
        f"{summary['baseline'][key]:.4f}</td><td>{summary['genetico'][key]:.4f}</td></tr>"
        for key, name in METRIC_LABELS.items()
    )
    st.markdown(
        "<div class='churn-panel-heading'>Desempenho no conjunto de teste</div>"
        f"<p class='churn-panel-description'>Métricas obtidas com os {summary['test_count']:,} clientes "
        "separados da busca.</p>"
        "<table class='churn-metrics'><thead><tr><th scope='col'>Métrica</th>"
        "<th scope='col'>Referência</th><th scope='col'>Genético</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
        f"<p class='churn-stat'>{summary['baseline_count']} → {summary['genetic_count']} "
        f"características <strong>({summary['reduction_pct']:.2f}% a menos)</strong></p>"
        "<p class='churn-note'>Ambos os modelos usam regressão logística; a seleção genética "
        "reduz as variáveis consideradas. Os resultados do teste são diferentes das "
        "probabilidades estimadas para o cliente acima.</p>",
        unsafe_allow_html=True,
    )


def main() -> None:
    st.markdown(
        "<header class='churn-hero'><p class='churn-kicker'>APRENDIZAGEM DE MÁQUINA · PROJETO N3</p>"
        "<h1 class='churn-title'>Previsão de cancelamento</h1>"
        "<p class='churn-subtitle'>Configure um perfil de cliente e compare as estimativas "
        "da regressão logística completa e do modelo com seleção genética de características.</p>"
        "</header>",
        unsafe_allow_html=True,
    )

    if "form_initialized" not in st.session_state:
        st.session_state["profile_choice"] = next(iter(PROFILE_FILES))
        _apply_profile(st.session_state["profile_choice"])
        st.session_state["form_initialized"] = True

    model_ready = all((RESULTS / filename).is_file() for _, filename in MODEL_NAMES.values())
    # Duas colunas apenas quando cada painel comportar ao menos 440 px.
    # st.grid deixa uma coluna em larguras menores, inclusive 768 e 390 px.
    layout = st.grid(2, min_column_width=440, gap=20, wrap=True)
    panel_form = layout.cell()
    panel_result = layout.cell()

    with panel_form:
        with st.container(border=True):
            st.markdown("<div class='churn-panel-heading'>Dados do cliente</div>"
                        "<p class='churn-panel-description'>Selecione um perfil e altere os campos para simular um novo cliente.</p>",
                        unsafe_allow_html=True)
            st.selectbox(
                "Perfil inicial", list(PROFILE_FILES), key="profile_choice",
                on_change=_choose_profile,
            )
            st.button("Restaurar dados do perfil", on_click=_reset_profile,
                      use_container_width=True, type="tertiary")
            st.markdown("**Edição rápida**")
            quick_a, quick_b = st.columns(2, gap="small", wrap=True)
            with quick_a:
                st.number_input(LABELS["tenure"], min_value=0, step=1, key="field_tenure")
                _select_field("InternetService")
            with quick_b:
                _select_field("Contract")
                st.number_input(LABELS["MonthlyCharges"], min_value=0.0,
                                step=1.0, format="%.2f", key="field_MonthlyCharges")

            with st.expander("Perfil e características pessoais"):
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

            with st.expander("Serviços adicionais de internet"):
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
                                use_container_width=True, disabled=not model_ready)
            if not model_ready:
                st.info("Modelos ainda não encontrados. No terminal, execute "
                        "`python -m scripts.compare_models` antes de calcular.")
            if clicked:
                try:
                    client = model_input(_form_data())
                    predictions = {}
                    for name, (_, filename) in MODEL_NAMES.items():
                        path = RESULTS / filename
                        model = cached_model(*_file_version(path))
                        predictions[name] = predict_customer(model, client)
                    st.session_state["last_prediction"] = {
                        "customer": client, "predictions": predictions,
                    }
                except (ValueError, OSError, ImportError, KeyError) as exc:
                    st.session_state["last_prediction"] = None
                    st.error(f"Não foi possível calcular: {exc}")

    with panel_result:
        with st.container(border=True):
            st.markdown(
                "<div class='churn-panel-heading'>Resultado da previsão</div>"
                "<p class='churn-panel-description'>Probabilidade estimada de cancelamento "
                "para o perfil informado, com limiar de classificação de 50%.</p>",
                unsafe_allow_html=True,
            )
            last = st.session_state.get("last_prediction")
            current = _form_data()
            if last is not None and last["customer"] != model_input(current):
                st.info("Os dados do cliente foram alterados. Calcule novamente para atualizar os resultados.")
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
                st.caption("Estimativas dos modelos para um perfil fictício. "
                           "Não representam garantias individuais de cancelamento.")
            else:
                st.info("Use **Calcular previsão** para comparar os dois modelos.")

        with st.container(border=True):
            report_path = RESULTS / "comparacao_modelos.json"
            if report_path.is_file():
                try:
                    _render_metrics(experiment_summary(cached_report(*_file_version(report_path))))
                except (ValueError, OSError, json.JSONDecodeError):
                    st.warning("O relatório experimental está incompleto. "
                               "Execute novamente `python -m scripts.compare_models`.")
            else:
                st.markdown("**Desempenho no conjunto de teste**")
                st.info("As métricas serão mostradas após a execução de "
                        "`python -m scripts.compare_models`.")

    st.caption("Telco Customer Churn · Dados de demonstração fictícios · "
               "Modelos executados localmente")


if __name__ == "__main__":
    main()
