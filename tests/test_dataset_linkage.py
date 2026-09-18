import pandas as pd

from core.dataset_linkage import (
    exact_linkage, mapped_exact_linkage, suggested_common_keys, suggested_mapped_keys, temporal_linkage,
)


def test_exact_linkage_counts_unique_and_multiple_candidates() -> None:
    primary = pd.DataFrame({"giorno": ["lun", "mar", "mer"], "zona": ["A", "B", "C"]})
    auxiliary = pd.DataFrame({
        "giorno": ["lun", "mar", "mar"], "zona": ["A", "B", "B"], "evento": ["x", "y", "z"]
    })

    report = exact_linkage(primary, auxiliary, ["giorno", "zona"])

    assert report.matched_rows == 2
    assert report.unique_matches == 1
    assert report.multiple_matches == 1


def test_suggested_keys_prefer_date_and_zone_over_measure_or_type() -> None:
    columns = ["Tipologia_API", "Zona", "Data", "Valore"]
    primary = pd.DataFrame(columns=columns)
    auxiliary = pd.DataFrame(columns=columns)

    assert suggested_common_keys(primary, auxiliary) == ["Zona", "Data"]


def test_mapped_keys_support_different_municipal_schemas() -> None:
    primary = pd.DataFrame({"codice_zona": ["centro", "stazione"]})
    auxiliary = pd.DataFrame({"id": ["centro", "periferia"], "nome": ["Centro", "Periferia"]})

    assert suggested_mapped_keys(primary, auxiliary) == [("codice_zona", "id")]
    report = mapped_exact_linkage(primary, auxiliary, [("codice_zona", "id")])

    assert report.unique_matches == 1
    assert report.keys == ("codice_zona ↔ id",)


def test_temporal_linkage_uses_place_and_symmetric_window() -> None:
    primary = pd.DataFrame({
        "quando": ["2026-01-01T10:00:00Z", "2026-01-01T12:00:00Z"], "luogo": ["Centro", "Centro"]
    })
    auxiliary = pd.DataFrame({
        "ora": ["2026-01-01T10:08:00Z", "2026-01-01T10:12:00Z"], "posto": ["centro", "centro"]
    })

    report = temporal_linkage(primary, auxiliary, "quando", "ora", "luogo", "posto", 10)

    assert report.unique_matches == 1
    assert report.matched_rows == 1
