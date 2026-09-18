import pandas as pd

from core.generic_privacy import audit_generic, infer_granularity, protect_generic


def test_aggregate_dataset_checks_small_cells() -> None:
    frame = pd.DataFrame({"zona": ["A", "B", "C"], "utenti_unici": [12, 3, 0]})

    inferred = infer_granularity(frame)
    audit = audit_generic(frame, "aggregato", [], ["zona"], None, k=5, measure="utenti_unici")
    protected, _ = protect_generic(frame, "aggregato", [], ["zona"], 5, "utenti_unici")

    assert inferred.kind == "aggregato"
    assert audit.outcome == "Da correggere"
    assert audit.metrics["Celle sotto soglia"] == 1
    assert pd.isna(protected.loc[1, "utenti_unici"])


def test_internal_identification_is_governed_not_called_anonymisation_failure() -> None:
    frame = pd.DataFrame({"account_id": ["u1", "u2"], "servizio": ["wifi", "wifi"]})

    audit = audit_generic(
        frame, "individuale", ["account_id"], ["servizio"], None, purpose="interno"
    )

    assert audit.outcome == "Uso interno da governare"
    assert "base giuridica" in " ".join(audit.reasons)
