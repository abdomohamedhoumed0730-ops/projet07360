"""Éléments partagés par les pages : récepteur AIS unique, météo en cache, indicateurs."""
import os
import time

import pandas as pd
import streamlit as st

from lib import direct
from lib.donnees import cppi, mois_fr, serie
from lib.modeles import prevoir, tester


def cle_ais() -> str:
    try:
        return st.secrets["AISSTREAM_API_KEY"]
    except Exception:
        return os.environ.get("AISSTREAM_API_KEY", "")


@st.cache_resource
def recepteur() -> direct.RecepteurAIS:
    """Un seul récepteur AIS pour toute l'application (créé à la première visite)."""
    return direct.RecepteurAIS(cle_ais())


@st.cache_data(ttl=3600, show_spinner="Lecture de la météo…")
def meteo(nom_zone: str) -> dict:
    return direct.meteo(direct.ZONES[nom_zone])


def _depuis_depart(r) -> float:
    return time.time() - r.depart


def navires(nom_zone: str) -> tuple:
    """Renvoie (DataFrame des navires, message, secours?)."""
    zone, r = direct.ZONES[nom_zone], recepteur()
    liste = r.navires(zone)
    if liste:
        return pd.DataFrame(liste), None, False
    s = r.secours(zone)
    if s and (r.erreur or _depuis_depart(r) > 600):
        return pd.DataFrame(s["navires"]), f"flux AIS indisponible, instantané du {s['releve']}", True
    if r.erreur:
        msg = f"connexion AIS en erreur : {r.erreur}"
    elif not r.connecte:
        msg = "connexion AIS en cours d'établissement, patientez une minute"
    elif _depuis_depart(r) < 120:
        msg = "connexion AIS active, premières positions en attente"
    else:
        msg = f"connexion AIS active, {r.recus} messages reçus, aucun navire dans cette zone pour l'instant"
    return pd.DataFrame(), msg, False


@st.cache_data
def indicateurs_historiques() -> dict:
    lb, la = serie("Long Beach"), serie("Los Angeles")
    commun = lb.dropna().index.intersection(la.dropna().index)
    dernier = commun.max()
    douze = commun[commun > dernier - pd.DateOffset(months=12)]
    an19 = commun[commun.year == 2019]
    prev = prevoir(lb.dropna(), 3)
    mois_prev = prev.mois.iloc[0]
    return {
        "dernier": dernier, "lb": lb[dernier], "lb_n1": lb[dernier - pd.DateOffset(years=1)],
        "part": lb[douze].sum() / (lb[douze].sum() + la[douze].sum()) * 100,
        "part19": lb[an19].sum() / (lb[an19].sum() + la[an19].sum()) * 100,
        "prev": prev, "mois_prev": mois_prev, "ref_prev": lb[mois_prev - pd.DateOffset(years=1)],
        "test": tester(lb.dropna(), 12), "cppi": cppi(), "lb_serie": lb.dropna(), "la_serie": la.dropna(),
        "maj": f"données à fin {mois_fr(dernier)}, récupérées le 19/11/2026",
    }
