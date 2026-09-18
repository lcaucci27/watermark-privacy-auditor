"""Catalogo degli esempi comunali: metadati e abbinamenti, separati dalla UI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


@dataclass(frozen=True)
class MunicipalSource:
    key: str
    short_label: str
    name: str
    municipality: str
    filename: str
    url: str
    row_kind: str

    @property
    def path(self) -> Path:
        return DATA_DIR / self.filename


@dataclass(frozen=True)
class LinkageExample:
    auxiliary: MunicipalSource
    key_pairs: tuple[tuple[str, str], ...]


ROMA_WIFI = MunicipalSource(
    "roma_wifi", "Roma · sessioni WiFi", "WiFi Roma Capitale · ultimi 14 giorni", "Roma",
    "romawifi_sessioni.csv", "https://dati.comune.roma.it/catalog/dataset/wifi2026", "individuale",
)
BOLOGNA_CROWDING = MunicipalSource(
    "bologna_crowding", "Bologna · affollamento", "WiFi Bologna · affollamento aggregato", "Bologna",
    "bologna_wifi_affollamento_sample.csv",
    "https://opendata.comune.bologna.it/explore/dataset/iperbole-wifi-affollamento/", "aggregato",
)
BOLOGNA_AREAS = MunicipalSource(
    "bologna_areas", "Bologna · aree WiFi", "Bologna · elenco aree WiFi (ufficiale)", "Bologna",
    "bologna_wifi_aree_sample.csv",
    "https://opendata.comune.bologna.it/explore/dataset/bolognawifi-elenco-aree-segnale/", "anagrafica",
)
MILANO_USERS = MunicipalSource(
    "milano_users", "Milano · utenti WiFi", "WiFi Milano · utenti unici per zona", "Milano",
    "milano_wifi_utenti_sample.csv",
    "https://dati.comune.milano.it/dataset/ds917-openwifimilano-uniqueuserzone", "aggregato",
)
MILANO_LOGINS = MunicipalSource(
    "milano_logins", "Milano · login WiFi", "Milano · login giornalieri per zona (ufficiale)", "Milano",
    "milano_wifi_login_sample.csv",
    "https://dati.comune.milano.it/dataset/ds918-openwifimilano-logincountzone", "aggregato",
)

PRIMARY_SOURCES = (ROMA_WIFI, BOLOGNA_CROWDING, MILANO_USERS)
PRIMARY_BY_LABEL = {source.short_label: source for source in PRIMARY_SOURCES}
LINKAGE_BY_PRIMARY = {
    BOLOGNA_CROWDING.key: LinkageExample(BOLOGNA_AREAS, (("codice_zona", "id"),)),
    MILANO_USERS.key: LinkageExample(MILANO_LOGINS, (("Giorno", "Giorno"), ("Zona", "Zona"))),
}
