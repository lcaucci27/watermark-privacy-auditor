"""Watermark: auditor locale di privacy e sicurezza per open data e servizi urbani."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from core.challenge_config import CHALLENGE

ASSETS = Path(__file__).resolve().parent / "assets"

st.set_page_config(page_title=CHALLENGE.page_title, page_icon=str(ASSETS / "favicon.png"), layout="wide")
st.logo(str(ASSETS / "logo.svg"), icon_image=str(ASSETS / "logo_mark.svg"), size="large")

page = st.navigation(
    [
        st.Page("app_pages/verifica.py", title="Verifica", icon=":material/fact_check:", default=True),
        st.Page("app_pages/assistente.py", title="Fai una domanda", icon=":material/forum:"),
        st.Page("app_pages/rapporto.py", title="Rapporto", icon=":material/description:"),
    ],
    position="top",
)

page.run()

with st.sidebar:
    with st.expander("Chi siamo e come funziona", icon=":material/info:"):
        st.markdown(
            "Watermark aiuta il Comune a controllare un dataset prima della pubblicazione.\n\n"
            "I calcoli avvengono su questo computer e non cercano l'identità delle persone.\n\n"
            "**Fonti:** Roma Capitale, CSIRT Italia e Garante privacy."
        )
    st.caption(CHALLENGE.event_line)
