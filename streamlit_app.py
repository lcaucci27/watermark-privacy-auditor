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
        st.Page("app_pages/assistente.py", title="Fai una domanda", icon=":material/forum:"),
        st.Page("app_pages/rapporto.py", title="Rapporto", icon=":material/description:"),
    ],
    position="top",
)

page.run()

with st.sidebar:
    with st.expander("Chi siamo e come funziona", icon=":material/info:"):
        st.markdown(
            "Watermark aiuta Comune, DPO, responsabile open data e RTD a controllare un dataset prima "
            "della pubblicazione o dell'uso interno.\n\n"
            "L'identificazione necessaria a erogare un servizio non è trattata come un errore: il controllo cambia "
            "in base allo scopo, agli accessi e alla conservazione.\n\n"
            "I calcoli avvengono su questo computer e non cercano l'identità delle persone.\n\n"
            "**Fonti:** Roma Capitale, Comune di Bologna, CSIRT Italia e Garante privacy."
        )
    st.caption(CHALLENGE.event_line)
