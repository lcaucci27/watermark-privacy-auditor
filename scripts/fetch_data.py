"""Scarica le fonti pubbliche in `data/` prima della demo; l'app poi lavora offline.

Fonti: bollettini CSIRT Italia (ACN), provvedimenti del Garante (docweb),
sessioni WiFi di Roma Capitale (open data CC-BY). Solo libreria standard.

Uso:
    python scripts/fetch_data.py --csirt-pages 30 --wifi-days 14
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import logging
import re
import time
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
USER_AGENT = "Mozilla/5.0 (compatible; Watermark-hackathon/1.0; uso didattico)"
PAUSE_SECONDS = 0.8

CSIRT_LIST = "https://www.acn.gov.it/portale/csirt-italia/alert-e-bollettini?start={page}"
CSIRT_ITEM = "https://www.acn.gov.it/portale/web/guest/-/{slug}"
GARANTE_DOC = "https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/{doc_id}"
GARANTE_TOPICS = ("videosorveglianza", "biometria")
# Documenti scelti a mano: la ricerca del sito non è interrogabile via HTTP semplice.
GARANTE_SEED_IDS = (
    "1712680",   # videosorveglianza, 8 aprile 2010
    "3134436",   # linee guida trasparenza e pubblicazione sul web, anonimizzazione
    "9487928",   # parere sulle linee guida AgID per il Wi-Fi pubblico gratuito
    "5217175",   # localizzazione di dispositivi smartphone
    "1895719",   # parere 12/2011 sui contatori intelligenti
    "10085707",  # parere ARERA sui dati di misura di energia e gas
    "4877134",   # Internet delle cose
)
ROMA_WIFI_PACKAGE = (
    "https://dati.comune.roma.it/catalog/api/3/action/package_show?id=de455e3a-d8ef-48a0-a725-832234c7217c"
)

CSIRT_HEADERS = (
    "Sintesi", "Tipologia", "Descrizione e potenziali impatti", "Prodotti e/o versioni affette", "Azioni di mitigazione", "CVE",
    "Riferimenti", "Change log", "Impatto sistemico", "Argomenti", "Data pubblicazione",
    "Data Ultimo Aggiornamento", "Informazioni su",
)
CODE_PATTERN = re.compile(r"^[A-Z]{2}\d{2}/\d{6}/CSIRT-ITA$")
CVE_PATTERN = re.compile(r"^CVE-\d{4}-\d{4,7}$")
IMPACT_PATTERN = re.compile(r"^(\w+)\s*\(([\d.,]+)\)")


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    time.sleep(PAUSE_SECONDS)
    return payload


def page_lines(raw: bytes) -> list[str]:
    text = raw.decode("utf-8", errors="ignore")
    text = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", text, flags=re.S)
    text = html.unescape(re.sub(r"<[^>]+>", "\n", text))
    return [line.strip() for line in text.split("\n") if line.strip()]


def _header_of(line: str) -> str | None:
    for header in CSIRT_HEADERS:
        if line == header or line.startswith(f"{header} ("):
            return header
    return None


def parse_bulletin(lines: list[str], slug: str) -> dict[str, object] | None:
    """Estrae i campi strutturati dalla pagina di un bollettino CSIRT."""
    code_index = next((i for i, line in enumerate(lines) if CODE_PATTERN.match(line)), None)
    if code_index is None:
        return None
    sections: dict[str, list[str]] = {}
    current = None
    for line in lines[code_index + 1:]:
        header = _header_of(line)
        if header == "Informazioni su":
            break
        if header:
            current = header
            sections.setdefault(current, [])
        elif current:
            sections[current].append(line)

    cve_lines = [line for line in sections.get("CVE", []) if not line.startswith(":")]
    cves, poc, exploited = [], 0, 0
    for i, line in enumerate(cve_lines):
        if CVE_PATTERN.match(line):
            cves.append(line)
            # Dopo l'identificativo la tabella riporta le colonne POC ed EXPLOITATION.
            flags = cve_lines[i + 1:i + 3]
            poc += len(flags) > 0 and flags[0] != "-"
            exploited += len(flags) > 1 and flags[1] != "-"

    impact = " ".join(sections.get("Impatto sistemico", [])[:1])
    match = IMPACT_PATTERN.match(impact)
    return {
        "slug": slug,
        "codice": lines[code_index],
        "tipo": lines[code_index - 1],
        "titolo": lines[code_index - 2],
        "data": " ".join(sections.get("Data pubblicazione", [])[:1]),
        "sintesi": " ".join(sections.get("Sintesi", [])),
        # Le voci di tassonomia sono etichette brevi; il testo lungo appartiene ad altre sezioni.
        "tipologia": "; ".join(line for line in sections.get("Tipologia", []) if len(line) <= 60),
        "descrizione": " ".join(sections.get("Descrizione e potenziali impatti", [])),
        "prodotti": " ".join(sections.get("Prodotti e/o versioni affette", [])),
        "mitigazione": " ".join(sections.get("Azioni di mitigazione", [])),
        "cve": ", ".join(cves),
        "n_cve": len(cves),
        "n_cve_con_poc": int(poc),
        "n_cve_sfruttate": int(exploited),
        "impatto_classe": match.group(1) if match else "",
        "impatto_punteggio": float(match.group(2).replace(",", ".")) if match else "",
        "argomenti": "; ".join(sections.get("Argomenti", [])),
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        logger.warning("Nessuna riga per %s", path.name)
        return
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    logger.info("Scritto %s: %d righe", path.relative_to(DATA_DIR.parent), len(rows))


def fetch_csirt(pages: int) -> None:
    slugs: list[str] = []
    empty_pages = 0
    for page in range(1, pages + 1):
        found = re.findall(r"/portale/web/guest/-/([a-z0-9-]+)", fetch(CSIRT_LIST.format(page=page)).decode("utf-8", "ignore"))
        new = [slug for slug in dict.fromkeys(found) if slug not in slugs]
        # Il portale a volte restituisce una pagina senza risultati nuovi: si esce solo dopo tre di fila.
        empty_pages = 0 if new else empty_pages + 1
        if empty_pages >= 3:
            break
        if not new:
            continue
        slugs.extend(new)
        logger.info("CSIRT elenco pagina %d: %d nuovi, totale %d", page, len(new), len(slugs))
    rows = []
    for i, slug in enumerate(slugs, 1):
        try:
            row = parse_bulletin(page_lines(fetch(CSIRT_ITEM.format(slug=slug))), slug)
        except OSError as exc:
            logger.warning("Bollettino %s non scaricato: %s", slug, exc)
            continue
        if row:
            rows.append(row)
        if i % 25 == 0:
            logger.info("CSIRT bollettini: %d/%d", i, len(slugs))
    write_csv(DATA_DIR / "csirt_bollettini.csv", rows)


def fetch_garante() -> None:
    ids = list(GARANTE_SEED_IDS)
    for topic in GARANTE_TOPICS:
        try:
            page = fetch(f"https://www.garanteprivacy.it/temi/{topic}").decode("utf-8", "ignore")
        except OSError as exc:
            logger.warning("Tema %s non scaricato: %s", topic, exc)
            continue
        ids.extend(re.findall(r"docweb/(\d+)", page))
    rows = []
    for doc_id in dict.fromkeys(ids):
        raw = fetch(GARANTE_DOC.format(doc_id=doc_id))
        title = re.search(r"<title>(.*?)</title>", raw.decode("utf-8", "ignore"), re.S)
        paragraphs = [line for line in page_lines(raw) if len(line) > 120]
        if not paragraphs:
            continue
        rows.append({
            "docweb": doc_id,
            "titolo": html.unescape(title.group(1)).split(" - Garante")[0].strip() if title else doc_id,
            "url": GARANTE_DOC.format(doc_id=doc_id),
            "testo": "\n".join(paragraphs),
        })
    write_csv(DATA_DIR / "garante_provvedimenti.csv", rows)


def fetch_roma_wifi(days: int) -> None:
    resources = json.loads(fetch(ROMA_WIFI_PACKAGE))["result"]["resources"]
    urls = sorted((r["url"] for r in resources if r["url"].endswith(".csv")), key=lambda url: url.rsplit("/", 1)[-1])
    header, rows = None, []
    for url in urls[-days:]:
        lines = fetch(url).decode("utf-8", "ignore").splitlines()
        if not lines:
            continue
        header = header or lines[0]
        rows.extend(line for line in lines[1:] if line.strip())
    target = DATA_DIR / "romawifi_sessioni.csv"
    target.write_text("\n".join([header or "", *rows]) + "\n", encoding="utf-8")
    logger.info("Scritto %s: %d sessioni da %d file", target.name, len(rows), min(days, len(urls)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csirt-pages", type=int, default=30)
    parser.add_argument("--wifi-days", type=int, default=14)
    parser.add_argument("--only", choices=["csirt", "garante", "wifi"])
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    DATA_DIR.mkdir(exist_ok=True)
    if args.only in (None, "wifi"):
        fetch_roma_wifi(args.wifi_days)
    if args.only in (None, "garante"):
        fetch_garante()
    if args.only in (None, "csirt"):
        fetch_csirt(args.csirt_pages)


if __name__ == "__main__":
    main()
