from core.assistant import IntentRouter


def lexical_router() -> IntentRouter:
    router = IntentRouter()
    router._semantic = lambda text: None
    return router


def test_router_recognises_core_requests_without_ollama() -> None:
    router = lexical_router()

    assert router.route("questo dataset è pubblicabile?").name == "verifica"
    assert router.route("correggilo sotto il 12%").name == "correggi"
    assert router.route("cosa dice il garante?").name == "norme"
    assert router.route("mostrami l'analisi statistica").name == "statistica"


def test_router_extracts_risk_threshold() -> None:
    intent = lexical_router().route("correggilo sotto il 12%")

    assert intent.threshold == 0.12


def test_strong_keyword_match_wins_over_misleading_semantics() -> None:
    router = IntentRouter()
    router._semantic = lambda text: ("verifica", 0.99)

    assert router.route("Cosa dice il Garante sulla pubblicazione di dati anonimi?").name == "norme"


def test_long_security_notice_is_an_alert() -> None:
    notice = "CVE-2026-12345 vulnerabilità critica sfruttata. " + "Aggiornare subito i sistemi esposti. " * 5

    assert lexical_router().route(notice).name == "allarme"
