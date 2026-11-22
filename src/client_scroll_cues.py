"""Observador visual do painel Cliente (Streamlit custom components v2).

Acompanha a rolagem local do formulário sem atualizar o estado do Python.
O componente não contém conteúdo visível nem interfere na grade do dashboard.
"""
from pathlib import Path

_JS = Path(__file__).with_suffix(".mjs").read_text(encoding="utf-8")


def mount_client_scroll_cues(st) -> None:
    observer = st.components.v2.component("n3_client_scroll_cues", js=_JS)
    observer(key="n3-client-scroll-cues")
