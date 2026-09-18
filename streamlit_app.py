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
        st.Page("app_pages/incrocio.py", title="Incrocia", icon=":material/join:"),
        st.Page("app_pages/assistente.py", title="Assistente", icon=":material/forum:"),
        st.Page("app_pages/rapporto.py", title="Audit completo", icon=":material/description:"),
    ],
    position="top",
)

page.run()

with st.sidebar:
    st.caption(":material/lock: Analisi locale · nessun dato inviato")
