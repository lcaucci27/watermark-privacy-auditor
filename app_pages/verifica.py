"""Percorso principale: esito, prove e correzione in linguaggio non tecnico."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from core.linkability import CounterEvidence, test_counter
from core.privacy import DIRECT, QUASI, SENSITIVE, classify_columns
from core.roma_privacy import aggregate_for_publication, findings, knowledge_ladder, report_markdown
from core.stats_analysis import CrossDayEvidence, DailyOrderEvidence, cross_day_evidence, daily_order_evidence
from views.dataset import sidebar_picker

SOURCE_URL = "https://dati.comune.roma.it/catalog/dataset/wifi2026"


@st.cache_data(show_spinner="Controllo se LOGINCOUNT conserva memoria nel tempo…", max_entries=3)
def login_evidence(frame: pd.DataFrame) -> CounterEvidence:
    return test_counter(frame, "LOGINCOUNT", frame["inizio"], ["sede", "DTLN"], location="sede")


@st.cache_data(show_spinner="Valido il segnale su giorni diversi e contro dati permutati…", max_entries=3)
def robust_login_evidence(frame: pd.DataFrame) -> tuple[DailyOrderEvidence, CrossDayEvidence]:
    return daily_order_evidence(frame), cross_day_evidence(frame)


data = sidebar_picker()

st.title("Verifica prima di pubblicare", icon=":material/fact_check:")
st.markdown(
    "Una risposta chiara per chi deve autorizzare un open data: **è davvero anonimo, quali rischi crea e come va corretto**."
)

if data is None:
    st.info("Scegli l'esempio oppure carica un CSV dalla barra laterale.", icon=":material/upload_file:")
    st.stop()

if not data.is_wifi:
    scan = classify_columns(data.frame)
    counts = scan["categoria"].value_counts()
    st.info("Questo non è il dataset WiFi di Roma: applico il controllo tabellare generale.", icon=":material/info:")
    cards = st.columns(4)
    cards[0].metric("Righe", f"{len(data.frame):,}", border=True)
    cards[1].metric("Identificativi", int(counts.get(DIRECT, 0)), border=True)
    cards[2].metric("Quasi-identificativi", int(counts.get(QUASI, 0)), border=True)
    cards[3].metric("Dati sensibili", int(counts.get(SENSITIVE, 0)), border=True)
    with st.container(border=True):
        st.subheader("Colonne da verificare", icon=":material/table_view:")
        st.dataframe(scan, hide_index=True, width="stretch")
    st.warning(
        "Per un file diverso servono la scelta dei quasi-identificativi e del dato da proteggere. "
        "Usa l'assistente per guidare il controllo.",
        icon=":material/warning:",
    )
    st.stop()

frame = data.frame
ladder = knowledge_ladder(frame)
issues = findings(frame)
session_risk = float(ladder.loc[ladder["informazioni conosciute"] == "Più lingua", "sessioni individuabili"].iloc[0])

with st.container(border=True):
    st.markdown(":red-badge[:material/error: DA CORREGGERE PRIMA DELLA PUBBLICAZIONE]")
    st.subheader("Il file è dichiarato anonimizzato, ma quasi ogni sessione è riconoscibile")
    st.markdown(
        "Non servono nome o e-mail: conoscere **giorno, ora, sede e lingua del dispositivo** basta quasi sempre "
        "a trovare una sola riga. Questo consente di vedere anche durata e traffico di quella sessione."
    )

cards = st.columns(4)
cards[0].metric("Sessioni analizzate", f"{len(frame):,}", border=True)
cards[1].metric("Sessioni individuabili", f"{session_risk:.1%}", border=True)
cards[2].metric("Precisione temporale", "1 secondo", border=True)
cards[3].metric("Sedi al civico", frame["sede"].nunique(), border=True)

st.header("Come può avvenire l'individuazione", icon=":material/person_search:")
st.caption("Ogni informazione aggiunta restringe il gruppo fino a lasciare, quasi sempre, una sola sessione.")
st.bar_chart(
    ladder.set_index("informazioni conosciute"),
    y="sessioni individuabili",
    y_label="Quota di sessioni individuabili",
    color="#A63F2E",
    horizontal=True,
)

with st.container(border=True):
    st.subheader("Un esempio semplice", icon=":material/key:")
    st.markdown(
        "Se qualcuno sa che una persona si è collegata il **9 settembre alle 11:54**, in **Via della Stamperia 86**, "
        "con il telefono impostato in **italiano**, può cercare quella combinazione. Se esiste una sola riga, "
        "vede anche quanto è durata la sessione e quanti dati ha trasferito."
    )
    st.caption("Watermark misura quante combinazioni sono uniche; non cerca né mostra l'identità delle persone.")

st.header("Le falle da correggere", icon=":material/report:")
for item in issues[:4]:
    with st.container(border=True):
        color = "red" if item.severity == "Critica" else "orange"
        st.markdown(f":{color}-badge[{item.severity}] **{item.title}**")
        st.markdown(item.evidence)
        st.caption(f"Perché conta: {item.consequence}")
        st.markdown(f"**Cosa fare:** {item.remedy}")

with st.expander("Altre criticità documentate", icon=":material/format_list_bulleted:"):
    for item in issues[4:]:
        st.markdown(f"**{item.title} · {item.severity}**")
        st.markdown(f"{item.evidence} {item.consequence}")
        st.caption(f"Intervento: {item.remedy}")

st.header("Il caso LOGINCOUNT", icon=":material/fingerprint:")
with st.container(border=True):
    st.markdown(
        "`LOGINCOUNT` è presente nel CSV ufficiale ma **Roma Capitale non ne documenta il significato**. "
        "Non è corretto trattarlo automaticamente come ID della persona. Possiamo però verificare se si comporta "
        "come un contatore che conserva memoria nel tempo."
    )
    evidence = login_evidence(frame)
    evidence_cards = st.columns(3)
    evidence_cards[0].metric("Valore più alto arriva dopo", f"{evidence.ordered_share:.1%}", border=True)
    evidence_cards[1].metric("Dopo mescolamento casuale", f"{evidence.null_share:.1%}", border=True)
    evidence_cards[2].metric("Coppie confrontate", f"{evidence.pairs:,}", border=True)
    st.warning(
        "Il segnale è compatibile con un contatore persistente, ma non dimostra da solo che due righe appartengano "
        "alla stessa persona. Finché l'ente non chiarisce il campo, la scelta prudente è non pubblicarlo.",
        icon=":material/warning:",
    )
    details = st.expander("Validazione statistica", icon=":material/science:", on_change="rerun")
    if details.open:
        with details:
            daily_order, cross_day = robust_login_evidence(frame)
            st.markdown(
                "Il test viene ripetuto separatamente per giorno, usando il giorno — non le singole coppie — "
                "come unità di replica. Un secondo test cerca continuità soltanto fra giornate consecutive."
            )
            d1, d2, d3 = st.columns(3)
            d1.metric("Ordine nei giorni reali", f"{daily_order.observed_mean:.1%}", border=True)
            d2.metric("Ordine dopo permutazione", f"{daily_order.null_mean:.1%}", border=True)
            d3.metric("Wilcoxon appaiato", f"p = {daily_order.wilcoxon_p:.5f}", border=True)
            c1, c2, c3 = st.columns(3)
            c1.metric("Continuità tra giorni", f"{cross_day.observed_share:.1%}", border=True)
            c2.metric("Attesa casuale", f"{cross_day.null_mean:.1%}", border=True)
            c3.metric("Test a permutazione", f"p = {cross_day.empirical_p:.3f}", border=True)
            st.caption(
                f"{len(daily_order.days)} giornate nel confronto appaiato; {cross_day.day_pairs} coppie di giorni "
                f"consecutivi e {cross_day.comparisons:,} valori nel test di continuità. "
                "Questi risultati rifiutano casualità e contatore di sede, non dimostrano l'identità dell'utente."
            )
            st.dataframe(
                daily_order.days,
                hide_index=True,
                width="stretch",
                column_config={
                    "osservato": st.column_config.ProgressColumn("Osservato", min_value=0, max_value=1, format="percent"),
                    "permutato": st.column_config.ProgressColumn("Permutato", min_value=0, max_value=1, format="percent"),
                },
            )

st.header("Versione consigliata", icon=":material/shield:")
safe, suppressed = aggregate_for_publication(frame, k=5)
with st.container(border=True):
    st.success(
        "Pubblicare conteggi aggregati per fascia di tre ore e municipio, rimuovendo LOGINCOUNT, orari esatti, civici "
        "e misure della singola sessione.",
        icon=":material/verified_user:",
    )
    before, after, third = st.columns(3)
    before.metric("Prima", f"{len(frame):,} righe individuali", border=True)
    after.metric("Dopo", f"{len(safe):,} gruppi", border=True)
    third.metric("Soglia minima", "5 sessioni", border=True)
    st.caption(
        f"Sono escluse {suppressed:,} sessioni appartenenti a gruppi troppo piccoli. Anche gli aggregati richiedono "
        "una verifica contro attacchi per differenza tra pubblicazioni successive."
    )
    with st.container(horizontal=True):
        st.download_button(
            "Scarica la versione aggregata",
            safe.to_csv(index=False).encode("utf-8"),
            "roma_wifi_aggregato_k5.csv",
            "text/csv",
            icon=":material/download:",
            type="primary",
        )
        st.download_button(
            "Scarica la valutazione",
            report_markdown(frame).encode("utf-8"),
            "valutazione_privacy_wifi_roma.md",
            "text/markdown",
            icon=":material/description:",
        )

with st.expander("Fonte e dati analizzati", icon=":material/source:"):
    st.markdown(f"[Apri il dataset ufficiale di Roma Capitale]({SOURCE_URL})")
    st.markdown(f"File locale: `{data.name}` · {len(frame):,} righe · {frame['giorno'].nunique()} giornate")
    st.dataframe(frame.head(20), hide_index=True, width="stretch")
