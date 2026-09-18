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
        st.Page("app_pages/assistente.py", title="Assistente", icon=":material/forum:", default=True),
        st.Page("app_pages/rapporto.py", title="Rapporto per il DPO", icon=":material/description:"),
        st.Page("app_pages/avanzate.py", title="Strumenti avanzati", icon=":material/tune:"),
    ],
    position="top",
)

page.run()

with st.sidebar:
    with st.expander("Chi siamo e come funziona", icon=":material/info:"):
        st.markdown(
            "**Committente**: il Comune titolare dei dati; utente: il suo DPO.\n\n"
            "**Frontend**: Streamlit. **Backend**: Python, pandas, scikit-learn, nello stesso processo.\n\n"
            "**IA**: tutta locale. Claude è un'estensione facoltativa.\n\n"
            "**Fonti**: CSIRT Italia (ACN), Garante privacy, open data di Roma Capitale."
        )
    st.caption(CHALLENGE.event_line)
