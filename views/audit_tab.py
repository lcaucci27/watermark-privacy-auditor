"""Scheda audit: l'agente esegue tutti i controlli in sequenza e produce il rapporto per il DPO."""

from __future__ import annotations

import streamlit as st

from core.audit_agent import run_audit
from views.shared import WIFI_FILE, csirt_corpus, frontier_chart, garante_corpus, impact_model, load_wifi, variants

STEPS_EXPLAINED = """
1. **Individuazione**: quante sessioni sono uniche, cioè riconoscibili da chi sa giorno, ora, luogo e lingua.
2. **Pseudonimi nascosti**: quali colonne numeriche si comportano come un contatore personale e collegano le sessioni.
3. **Minacce**: quali bollettini CSIRT riguardano i sistemi che producono questi dati, con l'impatto stimato dal modello.
4. **Norme**: i passaggi del Garante che si applicano, citati parola per parola.
5. **Correzione**: l'ottimizzatore prova 36 versioni del dataset e sceglie la più utile sotto la soglia di rischio.
"""


def render() -> None:
    st.caption("AGENTE DI AUDIT · UN CLIC, CINQUE CONTROLLI")
    if not WIFI_FILE.exists():
        st.info("Esegui `python scripts/fetch_data.py` per scaricare i dati in `data/`.", icon=":material/download:")
        return
    wifi, _ = load_wifi(WIFI_FILE.read_bytes())
    csirt, csirt_index = csirt_corpus()
    garante, garante_index = garante_corpus()

    with st.container(border=True):
        st.subheader("Prima di pubblicare un dataset", icon=":material/policy:")
        st.markdown(
            "Il DPO del Comune carica il file che sta per diventare open data. "
            "Watermark verifica se è davvero anonimo, se i sistemi che lo producono sono esposti, "
            "cosa dice il Garante e come correggerlo senza buttare via l'informazione utile."
        )
        with st.expander("Cosa controlla l'agente", icon=":material/help:"):
            st.markdown(STEPS_EXPLAINED)
        left, right = st.columns([2, 1], vertical_alignment="bottom")
        max_risk = left.slider(
            "Rischio massimo accettabile (quota di sessioni uniche)", 0.02, 0.50, 0.15, 0.01, format="%.2f",
            key="audit_risk",
        )
        run = right.button("Esegui audit", type="primary", icon=":material/play_arrow:", width="stretch")

    if run:
        table = variants(wifi)
        model = impact_model(csirt) if csirt is not None else None
        with st.status("Audit in corso…", expanded=True) as status:
            report = run_audit(wifi, table, max_risk, csirt, csirt_index, model, garante, garante_index)
            for step in report.steps:
                icon = ":material/check_circle:" if step.ok else ":material/error:"
                st.markdown(f"{icon} **{step.title}**: {step.outcome}")
            status.update(label="Audit completato", state="complete")
        st.session_state["audit"] = (report, table, max_risk)

    saved = st.session_state.get("audit")
    if not saved:
        return
    report, table, max_risk = saved
    rec = report.recommendation

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Sessioni uniche oggi", f"{report.published_risk:.1%}", border=True)
    k2.metric("Pseudonimi nascosti", len(report.flagged) if report.flagged is not None else 0, border=True)
    if rec is not None:
        k3.metric("Dopo la correzione", f"{rec['rischio']:.1%}", delta=f"{(rec['rischio'] - report.published_risk) * 100:.1f} punti",
                  delta_color="inverse", border=True)
        k4.metric("Utilità conservata", f"{rec['utilità relativa']:.0%}", border=True)

    with st.container(border=True):
        st.plotly_chart(frontier_chart(table, max_risk, rec), width="stretch")
        st.caption(
            "Utilità: quanto bene un modello (gradient boosting, validazione incrociata) stima ancora il traffico "
            "di una sessione usando solo le colonne pubblicate. Rischio: quota di sessioni uniche su tutte le colonne pubblicate. "
            "Le versioni con il contatore pubblicato sono escluse anche se poco uniche, perché collegano le sessioni tra loro."
        )

    left, right = st.columns(2)
    if report.bulletins is not None:
        with left.container(border=True, height="stretch"):
            st.subheader("Minacce collegate", icon=":material/security:")
            st.dataframe(report.bulletins, width="stretch", hide_index=True)
    if report.passages:
        with right.container(border=True, height="stretch"):
            st.subheader("Cosa dice il Garante", icon=":material/gavel:")
            for title, passage in report.passages:
                st.caption(title)
                st.markdown(f"> {passage}")

    st.download_button(
        "Scarica il rapporto per il DPO", report.markdown.encode("utf-8"), "rapporto_watermark.md",
        "text/markdown", icon=":material/description:", type="primary",
    )
