"""Assistente: il DPO fa domande in italiano, l'IA locale sceglie ed esegue gli strumenti."""

import streamlit as st

from core import llm
from core.assistant import IntentRouter
from views.assistant_answers import ANSWERS
from views.dataset import sidebar_picker

INTENT_NAMES = {
    "verifica": "verifica del dataset", "correggi": "correzione automatica", "minacce": "minacce sui sistemi",
    "norme": "riferimenti del Garante", "spiega": "spiegazione", "rapporto": "rapporto per il DPO",
    "allarme": "valutazione di un allarme", "aiuto": "guida", "cerca": "ricerca nelle fonti",
}
SUGGESTIONS = {
    ":material/fact_check: Questo dataset è pubblicabile?": "Questo dataset è pubblicabile?",
    ":material/auto_fix_high: Correggilo sotto il 15%": "Correggilo sotto il 15%",
    ":material/security: Quali sistemi sono a rischio?": "Quali sistemi sono a rischio?",
    ":material/gavel: Cosa dice il Garante?": "Cosa dice il Garante sulla pubblicazione di dati anonimi?",
    ":material/help: Perché è un problema?": "Perché LOGINCOUNT è un problema?",
}


@st.cache_resource
def router() -> IntentRouter:
    return IntentRouter()


if "messages" not in st.session_state:
    st.session_state.messages = []

data = sidebar_picker()
with st.sidebar:
    use_llm = st.toggle(
        "Riformula con Claude", value=False, disabled=not llm.available(), key="use_llm",
        help="Facoltativo. Richiede il pacchetto anthropic e la variabile ANTHROPIC_API_KEY. "
             "Riceve solo i risultati aggregati, mai il dataset.",
    )
    st.caption("IA locale attiva · nessun dato lascia il computer" if not use_llm
               else "Claude riceve solo domanda e risultati aggregati")

if not st.session_state.messages:
    st.title("Il tuo dataset è davvero anonimo?")
    st.markdown(
        "Watermark è l'assistente del DPO comunale prima di pubblicare open data. "
        "Fai una domanda in italiano: l'IA sceglie i controlli, li esegue su questo computer e ti risponde."
    )
    with st.container(horizontal=True):
        for icon, title, text in (
            (":material/fingerprint:", "Verifica", "Trova le persone riconoscibili e le colonne che fanno da pseudonimo."),
            (":material/auto_fix_high:", "Correggi", "Prova 36 versioni del file e sceglie quella che conserva più informazione."),
            (":material/shield:", "Proteggi", "Collega bollettini CSIRT e provvedimenti del Garante ai sistemi coinvolti."),
        ):
            with st.container(border=True):
                st.markdown(f"**{icon} {title}**")
                st.caption(text)
if data is None:
    st.info("Scegli o carica un dataset nella barra laterale.", icon=":material/arrow_back:")
    st.stop()


def answer(message: dict, replay: bool) -> str:
    handler = ANSWERS[message["intent"]]
    st.caption(f":material/psychology: Ho capito: {INTENT_NAMES[message['intent']]} · confidenza {message['confidence']:.0%}")
    summary = handler(data, message["question"], message["threshold"], replay, key=str(message["id"]))
    if message.get("rewritten"):
        st.markdown(":violet-badge[:material/auto_awesome: Riformulato da Claude]")
        st.markdown(message["rewritten"])
    return summary


for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=":material/person:" if message["role"] == "user" else ":material/policy:"):
        if message["role"] == "user":
            st.markdown(message["question"])
        else:
            answer(message, replay=True)

prompt = st.chat_input("Fai una domanda o incolla il testo di un allarme CSIRT", submit_mode="disable")
if not st.session_state.messages and not prompt:
    picked = st.pills("Prova a chiedere", list(SUGGESTIONS), key="suggestion")
    if picked:
        prompt = SUGGESTIONS[picked]

if prompt:
    intent = router().route(prompt)
    st.session_state.messages.append({"role": "user", "question": prompt})
    with st.chat_message("user", avatar=":material/person:"):
        st.markdown(prompt)
    message = {
        "role": "assistant", "id": len(st.session_state.messages), "question": prompt,
        "intent": intent.name, "confidence": intent.confidence, "threshold": intent.threshold,
    }
    with st.chat_message("assistant", avatar=":material/policy:"):
        summary = answer(message, replay=False)
        if use_llm:
            with st.spinner("Claude riformula la risposta…"):
                message["rewritten"] = llm.rewrite(prompt, summary)
            if message.get("rewritten"):
                st.markdown(":violet-badge[:material/auto_awesome: Riformulato da Claude]")
                st.markdown(message["rewritten"])
            else:
                st.caption("Claude non disponibile: resta la risposta locale.")
    st.session_state.messages.append(message)
