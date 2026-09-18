from core.local_ai import (
    LocalAnswer, _remove_unsupported_citations, _restore_supported_citations, validate_answer,
)


def test_local_answer_rejects_numbers_not_present_in_facts() -> None:
    answer = LocalAnswer("Da correggere", "Il rischio privacy calcolato è 98%", "Aggregare a 5", "Nessuna identità")

    assert validate_answer(answer, "Rischio 99,5%; soglia 5") == ["numeri non presenti nei risultati: 98%"]


def test_local_answer_accepts_grounded_numbers() -> None:
    answer = LocalAnswer("Da correggere", "Il rischio privacy calcolato è 99,5%", "Aggregare a 5", "Nessuna identità")

    assert validate_answer(answer, "Rischio 99,5%; soglia 5") == []


def test_local_answer_removes_only_unsupported_citations() -> None:
    answer = LocalAnswer("Esito", "Secondo [1] e [2] il dato è necessario", "Verificare", "Limite")

    cleaned = _remove_unsupported_citations(answer, "[2] Fonte disponibile")

    assert cleaned.reason == "Secondo e [2] il dato è necessario"


def test_local_answer_requires_available_citations() -> None:
    answer = LocalAnswer("Esito", "Il dato è necessario e proporzionato", "Verificare", "Limite")

    assert validate_answer(answer, "[1] Il dato è necessario e proporzionato") == ["fonti mancanti: [1]"]


def test_local_answer_restores_citation_from_facts() -> None:
    answer = LocalAnswer("Esito", "Il dato è necessario e proporzionato", "Verificare", "Limite")

    restored = _restore_supported_citations(answer, "[1] Il dato è necessario e proporzionato")

    assert restored.reason.startswith("[1]")
    assert validate_answer(restored, "[1] Il dato è necessario e proporzionato") == []
