#!/usr/bin/env python3
"""Genere data/previsions_orages.json depuis les GRIB2 ICON-EU du DWD (MVP sans vent).

Dépendances Python:
    pip install requests numpy eccodes

Le paquet système ecCodes doit aussi être installé. Sous Ubuntu/Debian:
    sudo apt-get update && sudo apt-get install -y libeccodes0

Cette version MVP ignore le cisaillement (DLS = 0) et utilise uniquement:
  - MLCAPE
  - Précipitations horaires (déduites de TOT_PREC cumulé)
  - Hauteur du sommet convectif (HTOP_CON) pour le top CB en FL.
"""

from __future__ import annotations

import bz2
import json
import logging
import os
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import eccodes
import numpy as np
import requests

GRIB_BASE_URL = "https://opendata.dwd.de/weather/nwp/icon-eu/grib"
ZONE = {"lon_min": -10.0, "lon_max": 15.0, "lat_min": 40.0, "lat_max": 56.0}
ECHEANCES = list(range(13))
TEMP_DIR = Path("tmp_grib")
OUTPUT_FILE = Path("data/previsions_orages.json")
GRID_STEP = 2  # 0.125 degree après sous-échantillonnage, environ 14 km
REQUEST_TIMEOUT = 180
RETRIES = 3

CHAMPS = {
    "cape": {"directory": "cape_ml", "suffixes": ("CAPE_ML",)},
    "precip_total": {"directory": "tot_prec", "suffixes": ("TOT_PREC",)},
    "cth": {"directory": "htop_con", "suffixes": ("HTOP_CON",)},
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
LOG = logging.getLogger("icon-eu")
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "ICON-EU-thunderstorm-map/1.0"})


def listing(cycle: str, directory: str) -> list[str]:
    """Lit l'index HTML DWD et renvoie les noms de GRIB2 compressés."""
    url = f"{GRIB_BASE_URL}/{cycle}/{directory}/"
    response = SESSION.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    names = re.findall(r'href=["\']([^"\']+\.grib2\.bz2)["\']', response.text, flags=re.I)
    return sorted({name.rsplit("/", 1)[-1] for name in names})


def run_from_name(name: str) -> tuple[str, str] | None:
    match = re.search(r"_(\d{8})(\d{2})_\d{3}_", name)
    if not match:
        return None
    return match.group(1), match.group(2)


def latest_run() -> tuple[str, str]:
    """Trouve le dernier run effectivement publié dans le dossier CAPE."""
    candidates: list[tuple[datetime, str, str]] = []
    for cycle in ("00", "03", "06", "09", "12", "15", "18", "21"):
        try:
            for name in listing(cycle, CHAMPS["cape"]["directory"]):
                parsed = run_from_name(name)
                if parsed:
                    date, run_cycle = parsed
                    dt = datetime.strptime(date + run_cycle, "%Y%m%d%H").replace(tzinfo=timezone.utc)
                    candidates.append((dt, date, run_cycle))
        except requests.RequestException as exc:
            LOG.warning("Index inaccessible (%sZ): %s", cycle, exc)
    if not candidates:
        raise RuntimeError("Aucun run ICON-EU trouvé sur le serveur DWD.")
    _, date, cycle = max(candidates, key=lambda item: item[0])
    return date, cycle


def select_file(names: list[str], date: str, cycle: str, lead: int, suffixes: tuple[str, ...]) -> str:
    """Choisit exactement le fichier du run, de l'échéance et du niveau voulus."""
    marker = f"_{date}{cycle}_{lead:03d}_"
    valid = [name for name in names if marker in name]
    for suffix in suffixes:
        suffix_re = re.compile(rf"_{re.escape(suffix)}\.grib2\.bz2$", re.I)
        matches = [name for name in valid if suffix_re.search(name)]
        if matches:
            return matches[0]
    raise FileNotFoundError(
        f"Fichier absent: run {date}{cycle}Z, H+{lead}, suffixes {suffixes}. "
        f"Exemples disponibles: {valid[:5]}"
    )


def fetch_and_unpack(url: str, destination: Path) -> None:
    """Télécharge un .bz2 puis le décompresse sans conserver l'archive."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    compressed = destination.with_suffix(destination.suffix + ".bz2")
    last_error: Exception | None = None
    for attempt in range(1, RETRIES + 1):
        try:
            LOG.info("Téléchargement [%s/%s]: %s", attempt, RETRIES, url)
            with SESSION.get(url, stream=True, timeout=REQUEST_TIMEOUT) as response:
                response.raise_for_status()
                with open(compressed, "wb") as out:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            out.write(chunk)
            with bz2.open(compressed, "rb") as source, open(destination, "wb") as out:
                shutil.copyfileobj(source, out, length=1024 * 1024)
            compressed.unlink(missing_ok=True)
            return
        except (OSError, requests.RequestException) as exc:
            last_error = exc
            compressed.unlink(missing_ok=True)
            destination.unlink(missing_ok=True)
            if attempt < RETRIES:
                time.sleep(attempt * 4)
    raise RuntimeError(f"Échec de téléchargement/décompression de {url}: {last_error}")


def read_grib(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Retourne tableau (lat, lon), latitudes 1D et longitudes 1D."""
    with open(path, "rb") as handle:
        gid = eccodes.codes_grib_new_from_file(handle)
        if gid is None:
            raise ValueError(f"Aucun message GRIB dans {path}")
        try:
            ni = int(eccodes.codes_get(gid, "Ni"))
            nj = int(eccodes.codes_get(gid, "Nj"))
            values = np.asarray(eccodes.codes_get_values(gid), dtype=np.float32).reshape(nj, ni)
            lats = np.asarray(eccodes.codes_get_array(gid, "latitudes"), dtype=np.float64).reshape(nj, ni)
            lons = np.asarray(eccodes.codes_get_array(gid, "longitudes"), dtype=np.float64).reshape(nj, ni)
        finally:
            eccodes.codes_release(gid)

    lat_1d = lats[:, 0]
    lon_1d = lons[0, :]
    # Certains GRIB sont rangés nord -> sud et/ou est -> ouest: on les remet en ordre croissant.
    if lat_1d[0] > lat_1d[-1]:
        lat_1d = lat_1d[::-1]
        values = values[::-1, :]
    if lon_1d[0] > lon_1d[-1]:
        lon_1d = lon_1d[::-1]
        values = values[:, ::-1]
    return values, lat_1d, lon_1d


def crop(data: np.ndarray, lat: np.ndarray, lon: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    lat_mask = (lat >= ZONE["lat_min"]) & (lat <= ZONE["lat_max"])
    lon_mask = (lon >= ZONE["lon_min"]) & (lon <= ZONE["lon_max"])
    if not lat_mask.any() or not lon_mask.any():
        raise ValueError("La zone demandée ne recoupe pas la grille ICON-EU.")
    return data[np.ix_(lat_mask, lon_mask)], lat[lat_mask], lon[lon_mask]


def load_field(key: str, date: str, cycle: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Télécharge puis lit les 13 échéances d'un champ."""
    config = CHAMPS[key]
    names = listing(cycle, config["directory"])
    fields: list[np.ndarray] = []
    saved_lat: np.ndarray | None = None
    saved_lon: np.ndarray | None = None
    for lead in ECHEANCES:
        name = select_file(names, date, cycle, lead, config["suffixes"])
        url = f"{GRIB_BASE_URL}/{cycle}/{config['directory']}/{name}"
        local = TEMP_DIR / f"{key}_{lead:03d}.grib2"
        fetch_and_unpack(url, local)
        data, lat, lon = read_grib(local)
        data, lat, lon = crop(data, lat, lon)
        if saved_lat is None:
            saved_lat, saved_lon = lat, lon
        elif data.shape != fields[0].shape or not np.allclose(lat, saved_lat) or not np.allclose(lon, saved_lon):
            raise ValueError(f"Grille incohérente pour {key}, H+{lead}.")
        fields.append(data)
    assert saved_lat is not None and saved_lon is not None
    return np.stack(fields), saved_lat, saved_lon


def risk(cape: np.ndarray, hourly_precip: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    # Formule MVP sans DLS: 60% CAPE, 40% precip
    cape_n = np.clip(np.nan_to_num(cape, nan=0.0) / 2500.0, 0.0, 1.0)
    precip_n = np.clip(np.nan_to_num(hourly_precip, nan=0.0) / 10.0, 0.0, 1.0)
    score = cape_n * 60.0 + precip_n * 40.0
    classes = np.select([score >= 75, score >= 55, score >= 35, score >= 15], [4, 3, 2, 1], default=0).astype(np.int8)
    return score, classes


def finite_number(value: float, digits: int = 1) -> float | None:
    return round(float(value), digits) if np.isfinite(value) else None


def build_geojson(fields: dict[str, np.ndarray], lat: np.ndarray, lon: np.ndarray, date: str, cycle: str) -> dict[str, Any]:
    # tot_prec est cumulé depuis le run: la différence entre deux pas est la pluie sur 1 h.
    total_precip = np.maximum(fields["precip_total"], 0.0)
    hourly_precip = np.empty_like(total_precip)
    hourly_precip[0] = total_precip[0]
    hourly_precip[1:] = np.maximum(total_precip[1:] - total_precip[:-1], 0.0)

    score, classes = risk(fields["cape"], hourly_precip)
    # 1 FL = 100 ft = 30.48 m. Valeur arrondie à la dizaine de FL.
    top_fl = np.rint(np.maximum(fields["cth"], 0.0) / 30.48 / 10.0).astype(np.int16) * 10

    features: list[dict[str, Any]] = []
    for index, lead in enumerate(ECHEANCES):
        for iy in range(0, len(lat), GRID_STEP):
            for ix in range(0, len(lon), GRID_STEP):
                level = int(classes[index, iy, ix])
                # Ne pas écrire les dizaines de milliers de points sans risque dans le JSON.
                if level == 0:
                    continue
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [round(float(lon[ix]), 5), round(float(lat[iy]), 5)]},
                    "properties": {
                        "echeance_h": lead,
                        "cape_ml_jkg": finite_number(fields["cape"][index, iy, ix], 0),
                        "precip_mm_h": finite_number(hourly_precip[index, iy, ix], 1),
                        "score": finite_number(score[index, iy, ix], 1),
                        "risque": level,
                        "top_cb_fl": int(top_fl[index, iy, ix]),
                    },
                })

    return {
        "type": "FeatureCollection",
        "metadata": {
            "genere_le": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "modele": "ICON-EU (DWD Open Data)",
            "cycle_icon_eu": f"{cycle}Z",
            "date_run": date,
            "zone": ZONE,
            "echeances": ECHEANCES,
            "grid_step": GRID_STEP,
            "formule": "score = 60% MLCAPE + 40% précipitation horaire (DLS ignoré dans ce MVP)",
            "avertissement": "Prévision expérimentale: ne remplace pas les vigilances météorologiques officielles.",
        },
        "features": features,
    }


def main() -> None:
    forced_cycle = os.getenv("CYCLE_ICON_EU")
    forced_date = os.getenv("DATE_ICON_EU")
    if (forced_cycle is None) != (forced_date is None):
        raise ValueError("Définir DATE_ICON_EU et CYCLE_ICON_EU ensemble, ou aucun des deux.")
    date, cycle = (forced_date, forced_cycle) if forced_date else latest_run()
    assert date is not None and cycle is not None
    LOG.info("Run ICON-EU retenu: %s %sZ", date, cycle)

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    try:
        fields: dict[str, np.ndarray] = {}
        reference_lat: np.ndarray | None = None
        reference_lon: np.ndarray | None = None
        for key in CHAMPS:
            LOG.info("Traitement: %s", key)
            values, lat, lon = load_field(key, date, cycle)
            if reference_lat is None:
                reference_lat, reference_lon = lat, lon
            elif values.shape[1:] != fields["cape"].shape[1:] or not np.allclose(lat, reference_lat) or not np.allclose(lon, reference_lon):
                raise ValueError(f"La grille de {key} ne correspond pas à celle de CAPE.")
            fields[key] = values

        assert reference_lat is not None and reference_lon is not None
        geojson = build_geojson(fields, reference_lat, reference_lon, date, cycle)
        # Écriture atomique: le dernier fichier valide est conservé en cas de panne.
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        temporary_output = OUTPUT_FILE.with_suffix(".json.tmp")
        with open(temporary_output, "w", encoding="utf-8") as handle:
            json.dump(geojson, handle, ensure_ascii=False, separators=(",", ":"))
        temporary_output.replace(OUTPUT_FILE)
        LOG.info("GeoJSON généré: %s (%s points à risque)", OUTPUT_FILE, len(geojson["features"]))
    finally:
        shutil.rmtree(TEMP_DIR, ignore_errors=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        LOG.exception("Génération échouée: %s", exc)
        sys.exit(1)