import pandas as pd

from core.dataset_linkage import mapped_exact_linkage
from core.municipal_catalog import LINKAGE_BY_PRIMARY, BOLOGNA_CROWDING, MILANO_USERS


def _report(source):
    example = LINKAGE_BY_PRIMARY[source.key]
    return mapped_exact_linkage(
        pd.read_csv(source.path),
        pd.read_csv(example.auxiliary.path),
        list(example.key_pairs),
    )


def test_milano_official_pair_is_ready_without_upload():
    report = _report(MILANO_USERS)
    assert report.primary_rows == 13_793
    assert report.matched_rows == 12_638
    assert report.unique_matches == 12_205


def test_bologna_official_pair_enriches_every_observation():
    report = _report(BOLOGNA_CROWDING)
    assert report.primary_rows == 5_000
    assert report.matched_rows == report.unique_matches == 5_000
    assert {"name", "longitude", "latitude"}.issubset(report.auxiliary_attributes)
