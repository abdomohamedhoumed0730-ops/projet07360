"""
Temps réel : météo (Open-Meteo) et navires (AIS, aisstream.io).

- Météo : un appel au plus par heure (st.cache_data(ttl=3600) dans les pages) ; chaque réponse est
  sauvegardée dans data/cache/ pour servir de secours si l'API ne répond plus.
- AIS : un récepteur unique tourne en arrière-plan (asyncio + bibliothèque websockets) et tient un
  registre « dernière position par navire ». Les pages ne font que lire ce registre.
"""
import asyncio
import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

CACHE = Path(__file__).resolve().parents[1] / "data" / "cache"
CACHE.mkdir(parents=True, exist_ok=True)

ZONES = {
    "Long Beach / Los Angeles": {"cle": "lb", "vent": (33.75, -118.21), "vagues": (33.68, -118.22),
                                 "fuseau": "America/Los_Angeles", "boite": [[33.40, -118.50], [33.80, -117.95]],
                                 "centre": (33.68, -118.20), "zoom": 9.6},
    "Djibouti": {"cle": "dji", "vent": (11.60, 43.13), "vagues": (11.70, 43.15), "fuseau": "Africa/Djibouti",
                 # zone élargie : la rade de Djibouti et les approches du golfe d'Aden (navires qui arrivent)
                 "boite": [[10.9, 42.2], [12.7, 43.9]], "centre": (11.70, 43.10), "zoom": 8.6},
}

# Seuils (hypothèses de travail, à valider avec le terminal)
ARRET_GRUES_KMH = 72.0     # rafales ≥ 72 km/h (≈ 20 m/s) : arrêt probable des portiques
VIGILANCE_KMH = 50.0
VAGUES_M = 2.0
SEUIL_NAVIRES = 15         # navires en approche ou au mouillage : renforcer les équipes au-delà


def _maintenant():
    return datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")


# ----------------------------------------------------------------------------- météo
def meteo(zone: dict) -> dict:
    f = CACHE / f"meteo_{zone['cle']}.json"
    try:
        vent = requests.get("https://api.open-meteo.com/v1/forecast", timeout=15, params={
            "latitude": zone["vent"][0], "longitude": zone["vent"][1],
            "current": "wind_speed_10m,wind_gusts_10m", "hourly": "wind_speed_10m,wind_gusts_10m",
            "forecast_days": 3, "timezone": zone["fuseau"], "wind_speed_unit": "kmh"}).json()
        mer = requests.get("https://marine-api.open-meteo.com/v1/marine", timeout=15, params={
            "latitude": zone["vagues"][0], "longitude": zone["vagues"][1], "current": "wave_height",
            "hourly": "wave_height", "forecast_days": 3, "timezone": zone["fuseau"]}).json()
        if "error" in vent or "error" in mer:
            raise RuntimeError(vent.get("reason") or mer.get("reason"))
        d = {"vent": vent, "mer": mer, "releve": _maintenant()}
        f.write_text(json.dumps(d), encoding="utf-8")
        return {**d, "secours": False, "erreur": None}
    except Exception as e:
        if f.exists():
            return {**json.loads(f.read_text(encoding="utf-8")), "secours": True, "erreur": str(e)[:120]}
        return {"vent": None, "mer": None, "releve": None, "secours": True, "erreur": str(e)[:120]}


def fenetre_grues(m: dict, heures: int = 48) -> dict:
    """Compte les heures des 48 prochaines où les rafales dépassent les seuils (arrêt grues, vigilance)."""
    if not m.get("vent"):
        return None
    h = m["vent"]["hourly"]
    t, raf = h["time"][:heures], [x or 0 for x in h["wind_gusts_10m"][:heures]]
    vag = [x or 0 for x in ((m.get("mer") or {}).get("hourly", {}).get("wave_height") or [0] * heures)[:heures]]
    arret = [ti for ti, r in zip(t, raf) if r >= ARRET_GRUES_KMH]
    vigil = [ti for ti, r, v in zip(t, raf, vag) if r >= VIGILANCE_KMH or v >= VAGUES_M]
    return {"heures_arret": len(arret), "heures_vigilance": len(vigil), "rafales_max": max(raf),
            "vagues_max": max(vag), "premiere": (arret or vigil or [None])[0], "derniere": (arret or vigil or [None])[-1]}


# ----------------------------------------------------------------------------- AIS
STATUTS = {0: "En route", 1: "Au mouillage", 5: "Amarré", 3: "Manœuvre restreinte", 15: "Non défini"}


def categorie(code) -> str:
    if code is None:
        return "Inconnu"
    c = int(code)
    if 70 <= c <= 79:
        return "Cargo / porte-conteneurs"
    if 80 <= c <= 89:
        return "Pétrolier"
    if 60 <= c <= 69:
        return "Passagers"
    if c in (31, 32, 52, 50):
        return "Remorqueur / pilote"
    return "Autre"


def _dans(boite, lat, lon):
    (a1, o1), (a2, o2) = boite
    return lat is not None and lon is not None and min(a1, a2) <= lat <= max(a1, a2) and min(o1, o2) <= lon <= max(o1, o2)


class RecepteurAIS:
    """Écoute aisstream.io en continu dans un fil d'exécution séparé (asyncio).
    Un navire au mouillage n'émet que toutes les 3 min : seule une écoute continue les voit tous."""

    def __init__(self, cle: str, duree_vie_min: int = 20):
        self.cle, self.duree_vie = cle, duree_vie_min * 60
        self.registre, self.types = {}, {}
        self.verrou = threading.Lock()
        self.depart, self.dernier, self.erreur = time.time(), None, None
        self.connecte, self.recus = False, 0          # diagnostic : connexion active, nombre de messages reçus
        if not cle:
            self.erreur = "clé aisstream absente (à mettre dans les secrets Streamlit)"
        else:
            threading.Thread(target=lambda: asyncio.run(self._boucle()), daemon=True).start()

    async def _boucle(self):
        import websockets
        abonnement = {"APIKey": self.cle, "BoundingBoxes": [z["boite"] for z in ZONES.values()],
                      "FilterMessageTypes": ["PositionReport", "ShipStaticData", "StandardClassBPositionReport"]}
        while True:
            try:
                async with websockets.connect("wss://stream.aisstream.io/v0/stream", open_timeout=20) as ws:
                    await ws.send(json.dumps(abonnement))
                    with self.verrou:
                        self.connecte = True
                    async for brut in ws:
                        msg = json.loads(brut)
                        if "error" in msg:
                            raise RuntimeError(msg["error"])
                        self._noter(msg)
            except Exception as e:
                with self.verrou:
                    self.erreur, self.connecte = str(e)[:120], False
                if "Api Key" in str(e):
                    return                      # clé refusée : inutile de réessayer
                await asyncio.sleep(30)         # coupure : nouvelle tentative dans 30 s

    def _noter(self, msg):
        meta, kind = msg.get("MetaData", {}), msg.get("MessageType")
        corps = msg.get("Message", {}).get(kind, {})
        mmsi = str(meta.get("MMSI"))
        with self.verrou:
            self.erreur, self.dernier = None, time.time()
            self.recus += 1
            if kind == "ShipStaticData":
                self.types[mmsi] = corps.get("Type")
            else:
                self.registre[mmsi] = {"mmsi": mmsi, "nom": (meta.get("ShipName") or "").strip() or "(sans nom)",
                                       "lat": corps.get("Latitude"), "lon": corps.get("Longitude"),
                                       "vitesse_noeuds": corps.get("Sog"), "statut_code": corps.get("NavigationalStatus"),
                                       "vu": time.time()}

    def navires(self, zone: dict) -> list:
        with self.verrou:
            now = time.time()
            out = []
            for n in self.registre.values():
                if now - n["vu"] <= self.duree_vie and _dans(zone["boite"], n["lat"], n["lon"]):
                    d = dict(n, type=categorie(self.types.get(n["mmsi"])),
                             statut=STATUTS.get(n["statut_code"], "Autre / non transmis"),
                             vu_il_y_a_min=round((now - n["vu"]) / 60, 1))
                    out.append(d)
            if out:  # instantané de secours
                (CACHE / f"ais_{zone['cle']}.json").write_text(json.dumps({"releve": _maintenant(), "navires": out}),
                                                                encoding="utf-8")
            return out

    def secours(self, zone: dict):
        f = CACHE / f"ais_{zone['cle']}.json"
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
