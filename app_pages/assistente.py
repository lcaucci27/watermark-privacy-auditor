"""Assistente: il DPO fa domande in italiano, l'IA locale sceglie ed esegue gli strumenti."""

import streamlit as st

from core import local_ai
from core.assistant import IntentRouter
from views.assistant_answers import ANSWERS
from views.dataset import sidebar_picker

INTENT_NAMES = {
    "verifica": "verifica del dataset", "correggi": "correzione automatica", "minacce": "minacce sui sistemi",
    "norme": "riferimenti del Garante", "spiega": "spiegazione", "rapporto": "rapporto per il DPO",
    "allarme": "valutazione di un allarme", "aiuto": "guida", "cerca": "ricerca nelle fonti",
    "statistica": "analisi statistica", "chat": "conversazione",
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


def reset_agent() -> None:
    """Apre una conversazione pulita senza cambiare dataset o modello selezionato."""
    st.session_state.messages = []
    st.session_state.pop("suggestion", None)

data = sidebar_picker()
LOCAL_CHAT = "Watermark · chatbot locale"
NO_LLM = "Solo risultati calcolati"


@st.cache_data(ttl=30, show_spinner=False)
def language_models() -> list[str]:
    installed = local_ai.installed_models()
    available = local_ai.SPECIALIZED_MODEL in installed
    return [LOCAL_CHAT, NO_LLM] if available else [NO_LLM]


with st.sidebar:
    st.subheader("Modello linguistico", icon=":material/neurology:")
    writer = st.selectbox(
        "Chi scrive le risposte", language_models(), key="writer", label_visibility="collapsed",
        help="I modelli locali girano con Ollama su questo computer. Ricevono solo la domanda e i risultati aggregati.",
    )
    if writer == LOCAL_CHAT:
        st.caption("Qwen 2.5 3B · nessun dato lascia il computer")
    else:
        st.caption("Risposta immediata senza chatbot")
    st.button(
        "Pulisci e riavvia", icon=":material/restart_alt:", width="stretch",
        disabled=not st.session_state.messages, on_click=reset_agent,
        help="Cancella la cronologia di questa sessione e apre una nuova conversazione.",
    )

st.title("Chiedi a Watermark", icon=":material/forum:")
st.caption("L'agente sceglie il controllo adatto, lo esegue sui dati e spiega esito, azione e limite.")
with st.expander("Cosa fa e cosa puoi chiedere", icon=":material/help:"):
    st.markdown(
        "Watermark riconosce l'intento della domanda e usa controlli verificabili per valutare pubblicazione, "
        "correzioni, minacce, riferimenti del Garante e statistiche. Il modello linguistico serve soltanto a "
        "riscrivere i risultati aggregati in modo chiaro: non decide l'esito e non riceve le righe grezze.\n\n"
        "**Esempi:** «Questo dataset è pubblicabile?», «Correggilo sotto il 15%», "
        "«Quali sistemi sono a rischio?», «Cosa dice il Garante?»."
    )
def answer(message: dict, replay: bool) -> str:
    if message["intent"] == "chat":
        st.caption(":material/forum: Conversazione locale")
        if message.get("rewritten"):
            st.markdown(message["rewritten"])
            return message["rewritten"]
        return ""
    if data is None:
        text = "Per eseguire un controllo, scegli o carica un dataset nella barra laterale."
        st.info(text, icon=":material/arrow_back:")
        return text
    handler = ANSWERS[message["intent"]]
    st.caption(f":material/psychology: Ho capito: {INTENT_NAMES[message['intent']]} · confidenza {message['confidence']:.0%}")
    summary = handler(data, message["question"], message["threshold"], replay, key=str(message["id"]))
    if replay and message.get("rewritten"):
        st.markdown(f":violet-badge[:material/neurology: Scritto da {message.get('writer', 'LLM')}]")
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
    previous_chat = []
    for previous in st.session_state.messages[-6:]:
        if previous["role"] == "user":
            previous_chat.append({"role": "user", "content": previous["question"]})
        elif previous.get("rewritten"):
            previous_chat.append({"role": "assistant", "content": previous["rewritten"]})
    intent = router().route(prompt)
    st.session_state.messages.append({"role": "user", "question": prompt})
    with st.chat_message("user", avatar=":material/person:"):
        st.markdown(prompt)
    message = {
        "role": "assistant", "id": len(st.session_state.messages), "question": prompt,
        "intent": intent.name, "confidence": intent.confidence, "threshold": intent.threshold,
    }
    with st.chat_message("assistant", avatar=":material/policy:"):
        if intent.name == "chat" and writer == LOCAL_CHAT:
            st.caption(":material/forum: Conversazione locale · risposta generata sul computer")
            message["rewritten"] = st.write_stream(
                local_ai.casual_chat_stream(prompt, previous_chat, local_ai.SPECIALIZED_MODEL)
            )
            message["writer"] = "Watermark locale"
        elif intent.name == "chat":
            message["rewritten"] = local_ai.casual_fallback(prompt)
            message["writer"] = "Risposta locale"
            st.markdown(message["rewritten"])
        else:
            summary = answer(message, replay=False)
        if intent.name != "chat" and writer == LOCAL_CHAT:
            st.markdown(":violet-badge[:material/neurology: Scritto da Watermark sul tuo computer]")
            message["rewritten"] = st.write_stream(
                local_ai.chat_stream(prompt, summary, local_ai.SPECIALIZED_MODEL)
            )
            message["writer"] = "Watermark locale"
    st.session_state.messages.append(message)
