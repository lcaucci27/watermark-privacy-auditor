"""Scarica esempi riproducibili dai portali open data di Bologna e Milano."""

from __future__ import annotations

import json
from io import BytesIO
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
BOLOGNA_OUTPUT = ROOT / "data" / "bologna_wifi_affollamento_sample.csv"
BOLOGNA_AREAS_OUTPUT = ROOT / "data" / "bologna_wifi_aree_sample.csv"
BOLOGNA_API = "https://opendata.comune.bologna.it/api/explore/v2.1/catalog/datasets/iperbole-wifi-affollamento/records"
BOLOGNA_AREAS_API = "https://opendata.comune.bologna.it/api/explore/v2.1/catalog/datasets/bolognawifi-elenco-aree-segnale/records"
MILANO_API = "https://dati.comune.milano.it/api/3/action/package_show?id={}"
MILANO_DATASETS = {
    "ds917-openwifimilano-uniqueuserzone": ROOT / "data" / "milano_wifi_utenti_sample.csv",
    "ds918-openwifimilano-logincountzone": ROOT / "data" / "milano_wifi_login_sample.csv",
}


def fetch_bologna(limit: int = 5000, page_size: int = 100) -> pd.DataFrame:
    rows: list[dict] = []
    for offset in range(0, limit, page_size):
        query = urllib.parse.urlencode({"limit": min(page_size, limit - offset), "offset": offset, "order_by": "data desc"})
        with urllib.request.urlopen(f"{BOLOGNA_API}?{query}", timeout=30) as response:
            payload = json.load(response)
        for row in payload.get("results", []):
            point = row.pop("geo_point_2d", None) or {}
            row.pop("geo_shape", None)
            row["longitudine"] = point.get("lon")
            row["latitudine"] = point.get("lat")
            rows.append(row)
    return pd.DataFrame(rows)


def fetch_milano(dataset_id: str) -> pd.DataFrame:
    """Risolve la risorsa CSV corrente via CKAN, senza fissare il nome datato del file."""
    with urllib.request.urlopen(MILANO_API.format(dataset_id), timeout=30) as response:
        resources = json.load(response)["result"]["resources"]
    csv_url = next(resource["url"] for resource in resources if resource.get("format", "").upper() == "CSV")
    with urllib.request.urlopen(csv_url, timeout=60) as response:
        raw = response.read()
    frame = pd.read_csv(BytesIO(raw), sep=";")
    # Il portale descrive la serie come giornaliera, ma conserva orari tecnici diversi negli anni.
    frame["Giorno"] = frame["Data"].astype("string").str.slice(0, 10)
    return frame


def fetch_bologna_areas() -> pd.DataFrame:
    with urllib.request.urlopen(f"{BOLOGNA_AREAS_API}?limit=100", timeout=30) as response:
        rows = json.load(response).get("results", [])
    cleaned = []
    for row in rows:
        point = row.get("geo_point_2d") or {}
        cleaned.append({
            "id": row.get("id"), "name": row.get("name"),
            "longitude": point.get("lon"), "latitude": point.get("lat"),
        })
    return pd.DataFrame(cleaned)


if __name__ == "__main__":
    frame = fetch_bologna()
    frame.to_csv(BOLOGNA_OUTPUT, index=False)
    print(f"Salvate {len(frame):,} righe in {BOLOGNA_OUTPUT}")
    areas = fetch_bologna_areas()
    areas.to_csv(BOLOGNA_AREAS_OUTPUT, index=False)
    print(f"Salvate {len(areas):,} righe in {BOLOGNA_AREAS_OUTPUT}")
    for dataset_id, output in MILANO_DATASETS.items():
        frame = fetch_milano(dataset_id)
        frame.to_csv(output, index=False)
        print(f"Salvate {len(frame):,} righe in {output}")
