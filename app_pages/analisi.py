"""Analisi statistica: prove formali della falla e della correzione (metodi della performance analysis)."""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from core.stats_analysis import anova_three_factors, describe, factorial_responses, flaw_evidence, paired_comparison
from views.assistant_answers import _scan
from views.dataset import sidebar_picker
from views.shared import AQUA, CORAL, GOLD, INK

MARGIN = dict(l=20, r=20, t=50, b=20)


@st.cache_data(show_spinner="Eseguo l'esperimento fattoriale: 36 versioni × 13 giorni…", max_entries=2)
def experiment(frame: pd.DataFrame) -> pd.DataFrame:
    return factorial_responses(frame)


data = sidebar_picker()
st.title("Analisi statistica")
st.markdown(
    "Le affermazioni dell'assistente, dimostrate con i metodi della performance analysis: "
    "statistica descrittiva, intervalli di confidenza, test di ipotesi, disegno degli esperimenti e ANOVA."
)
if data is None or not data.is_wifi:
    st.info("L'analisi completa è disponibile per il dataset WiFi di Roma Capitale.", icon=":material/info:")
    st.stop()
frame = data.frame

st.header("1. Com'è fatto il dataset", divider="gray")
left, right = st.columns(2)
with left.container(border=True):
    stats_table = pd.DataFrame({name: describe(frame[name]) for name in ("DURATION", "DOWNLOAD", "UPLOAD")}).T
    st.dataframe(stats_table.round(2), width="stretch")
    st.caption(
        "Durata e traffico sono molto asimmetrici (media molto più alta della mediana): "
        "per questo usiamo mediana e SIQR, non la media."
    )
with right.container(border=True):
    box = px.box(frame.assign(traffico_MB=(frame["DOWNLOAD"] + frame["UPLOAD"]) / 1e6 + 1e-3),
                 x="MUNICIPIO", y="traffico_MB", log_y=True, points=False,
                 title="Traffico per sessione e municipio (scala logaritmica)", color_discrete_sequence=[AQUA])
    box.update_layout(margin=MARGIN, xaxis_title="", yaxis_title="MB")
    st.plotly_chart(box, width="stretch")

st.header("2. La falla è reale?", divider="gray")
row = _scan(frame).query("colonna == 'LOGINCOUNT'").iloc[0]
evidence = flaw_evidence(frame, float(row["ordine nel tempo"]), int(row["coppie vicine"]))
c1, c2, c3 = st.columns(3)
c1.metric("Test binomiale su LOGINCOUNT", "p < 10⁻³⁰⁰" if evidence.binomial_p == 0 else f"p = {evidence.binomial_p:.1e}", border=True)
c2.metric("Sedi con trend crescente (Mann-Kendall)", f"{evidence.sites_increasing} su {evidence.sites_tested}", border=True)
mean, low, high = evidence.daily_ci
c3.metric("Sessioni uniche, IC 95%", f"{mean:.1%}", f"da {low:.1%} a {high:.1%}", delta_color="off", border=True)
st.markdown(
    f"- **Ipotesi nulla H₀**: tra due valori vicini di LOGINCOUNT non esiste un ordine temporale, quindi il più alto "
    f"arriva dopo nel 50% dei casi. Osservato: **{evidence.ordered_share:.1%}** su {evidence.pairs:,} coppie. "
    "H₀ rigettata: esiste memoria temporale, ma questo test non attribuisce le righe alla stessa persona.\n"
    f"- **Mann-Kendall** (trend non parametrico): se fosse un contatore della sede crescerebbe in ogni sede. "
    f"Succede solo in {evidence.sites_increasing} sedi su {evidence.sites_tested}.\n"
    f"- **Intervallo di confidenza** (t di Student, {len(evidence.daily_unique)} giorni): la quota di sessioni uniche "
    f"è stabile tra un giorno e l'altro, non è un caso di una singola giornata."
)
daily = evidence.daily_unique.rename("quota").reset_index()
line = px.line(daily, x="giorno", y="quota", markers=True, title="Sessioni uniche giorno per giorno",
               color_discrete_sequence=[CORAL], range_y=[0.9, 1.0])
line.add_hrect(y0=low, y1=high, fillcolor=GOLD, opacity=0.2, line_width=0, annotation_text="IC 95% della media")
line.update_layout(margin=MARGIN, yaxis_tickformat=".0%", xaxis_title="", yaxis_title="")
st.plotly_chart(line, width="stretch")

st.header("3. La correzione funziona? Un esperimento", divider="gray")
st.markdown(
    "Disegno fattoriale completo **4 × 3 × 3**: orario (secondo, 15 minuti, 1 ora, 3 ore), luogo (civico, via, municipio), "
    "contatore (pubblicato, in fasce, rimosso). Ogni giorno è una **replica**. Risposta: quota di sessioni uniche."
)
responses = experiment(frame)
anova = anova_three_factors(responses)
left, right = st.columns([3, 2])
with left.container(border=True):
    st.dataframe(
        anova, hide_index=True, width="stretch",
        column_config={
            "importanza": st.column_config.ProgressColumn("Importanza (SS/SST)", min_value=0, max_value=1, format="percent"),
            "SS": st.column_config.NumberColumn(format="%.3f"), "F": st.column_config.NumberColumn(format="%.1f"),
            "p-value": st.column_config.NumberColumn(format="%.1e"),
        },
    )
    top = anova.iloc[0]
    st.caption(
        f"Il fattore **{top['fonte']}** spiega il {top['importanza']:.0%} della variabilità del rischio. "
        "Importanza (quanto pesa) e significatività (F-test, p-value) sono due cose diverse: qui i fattori principali hanno entrambe."
    )
with right.container(border=True):
    means = responses.groupby(["orario", "contatore"], as_index=False)["rischio"].mean()
    means["orario"] = pd.Categorical(means["orario"], ["secondo", "15 minuti", "1 ora", "3 ore"], ordered=True)
    interaction = px.line(means.sort_values("orario"), x="orario", y="rischio", color="contatore", markers=True,
                          title="Grafico di interazione", color_discrete_sequence=[CORAL, GOLD, AQUA])
    interaction.update_layout(margin=MARGIN, yaxis_tickformat=".0%", xaxis_title="", yaxis_title="sessioni uniche",
                              legend=dict(orientation="h", y=-0.3))
    st.plotly_chart(interaction, width="stretch")
    st.caption("Linee non parallele: l'effetto dell'orario dipende da cosa si fa con il contatore (interazione).")

chosen = {"orario": "3 ore", "luogo": "civico", "contatore": "in fasce"}
paired = paired_comparison(responses, chosen)
st.subheader("Prima e dopo, sugli stessi giorni")
p1, p2, p3 = st.columns(3)
p1.metric("Riduzione media delle sessioni uniche", f"{paired['differenza media'] * 100:.1f} punti",
          f"IC 95% {paired['IC basso'] * 100:.1f} – {paired['IC alto'] * 100:.1f}", delta_color="off", border=True)
p2.metric("Normalità delle differenze (Shapiro)", f"p = {paired['Shapiro p-value (normalità)']:.4f}", border=True)
p3.metric("Wilcoxon signed-rank", f"p = {paired['Wilcoxon p-value']:.5f}", border=True)
st.caption(
    f"Osservazioni appaiate su {paired['giorni']} giorni (versione scelta: 3 ore · civico · contatore in fasce). "
    "Le differenze non sono normali, quindi usiamo il test non parametrico di Wilcoxon. "
    "L'intervallo non contiene lo zero: la correzione riduce il rischio in modo significativo."
)

with st.expander("Metodo e limiti", icon=":material/science:"):
    st.markdown(
        "- Le repliche sono i giorni disponibili (file giornalieri del portale con almeno 200 sessioni).\n"
        "- L'F-test presuppone residui normali e varianze omogenee; con differenze non normali il confronto "
        "prima/dopo usa Wilcoxon.\n"
        "- Rigettare H₀ non dimostra quale sia il significato ufficiale di LOGINCOUNT: dimostra che non è casuale "
        "e che non è un contatore di sede.\n"
        "- Correlazione non è causalità: le misure descrivono questo dataset, non tutti gli open data."
    )
