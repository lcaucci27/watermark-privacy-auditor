"""Rapporto sintetico per il DPO sul dataset selezionato."""

import streamlit as st

from core.generic_privacy import audit_generic, infer_granularity, report_markdown, suggested_roles
from views import audit_tab
from views.dataset import sidebar_picker

data = sidebar_picker()
st.title("Audit completo", icon=":material/description:")

if data is None:
    st.info("Scegli un dataset nella barra laterale.", icon=":material/arrow_back:")
    st.stop()

if data.is_wifi:
    audit_tab.render(data.frame)
    st.stop()

direct, quasi, sensitive = suggested_roles(data.frame)
granularity = infer_granularity(data.frame)
row_kind = data.row_kind_hint or granularity.kind
measure = granularity.measures[0] if granularity.measures else None
audit = audit_generic(
    data.frame, row_kind, direct, quasi, sensitive[0] if sensitive else None,
    k=5, measure=measure, purpose="pubblicazione",
)

colour = "green" if audit.outcome == "Compatibile con pubblicazione" else "red"
st.markdown(f":{colour}-badge[{audit.outcome}]")
st.subheader("Valutazione pronta")
for reason in audit.reasons:
    st.markdown(f"- {reason}")
st.caption("Il DPO conferma scopo, significato delle colonne e decisione finale.")

st.download_button(
    "Scarica il rapporto", report_markdown(data.name, audit, 5).encode("utf-8"),
    "rapporto_watermark.md", "text/markdown", icon=":material/download:", type="primary",
)
