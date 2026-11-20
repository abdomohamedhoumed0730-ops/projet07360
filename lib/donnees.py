"""Chargement et préparation des données historiques (lues dans data/raw/, jamais rappelées en ligne)."""
from pathlib import Path

import pandas as pd
import streamlit as st

RACINE = Path(__file__).resolve().parents[1]
RAW = RACINE / "data" / "raw"

# Pays retenus dans la base CNUCED (codes ONU M49)
PAYS = {"0000": "Monde", "842": "États-Unis", "124": "Canada", "036": "Australie",
        "251": "France", "926": "Royaume-Uni"}
MOIS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]


def mois_fr(d) -> str:
    d = pd.Timestamp(d)
    return f"{MOIS[d.month - 1]} {d.year}"


def nb(x, dec=0) -> str:
    """Nombre au format français (espace pour les milliers, virgule décimale)."""
    return f"{x:,.{dec}f}".replace(",", " ").replace(".", ",")


@st.cache_data
def volumes() -> pd.DataFrame:
    """Volumes mensuels de LA (site du port) et LB (BTS), au même format."""
    la = pd.read_csv(RAW / "la_official.csv")
    la["mois"] = pd.to_datetime(dict(year=la.year, month=la.month, day=1))
    lb = pd.read_csv(RAW / "bts_lb.csv")
    lb["mois"] = pd.to_datetime(lb.month + "-01")
    # Erreur du BTS : juillet 2020 répète la valeur de juin. Valeur du communiqué du port : 376 807 EVP.
    lb.loc[lb.mois == "2020-07-01", "loaded_imports"] = 376807

    def meme_format(df, port):
        return pd.DataFrame({"port": port, "mois": df.mois, "imports_pleins": df.loaded_imports,
                             "exports_pleins": df.loaded_exports, "vides_export": df.empty_exports})

    v = pd.concat([meme_format(la, "Los Angeles"), meme_format(lb, "Long Beach")], ignore_index=True)
    # total comparable : le BTS ne publie pas les vides à l'import de Long Beach (< 2 % du total)
    v["total"] = v.imports_pleins + v.exports_pleins + v.vides_export
    return v


@st.cache_data
def cppi() -> pd.DataFrame:
    return pd.read_csv(RAW / "cppi_ports.csv", sep=";").set_index("port")


@st.cache_data
def cnuced() -> pd.DataFrame:
    """Temps médian au port (fichier complet CNUCED) + nombre d'escales, par pays et par marché."""
    t = pd.read_csv(RAW / "US_PortCalls.csv", dtype={"Economy": str, "CommercialMarket": str})
    t = t[t.Economy.isin(PAYS) & t.CommercialMarket.isin(["00", "03"])]
    t = t[["Year", "Economy", "CommercialMarket", "Median time in port (days)"]]
    t.columns = ["annee", "code", "marche", "temps_median_j"]
    e = pd.read_csv(RAW / "cnuced_escales.csv", dtype={"economy_code": str, "market_code": str})
    e.columns = ["code", "marche", "annee", "escales"]
    d = t.merge(e, on=["code", "marche", "annee"], how="outer")
    d["pays"] = d.code.map(PAYS)
    d["marche"] = d.marche.map({"00": "Tous navires", "03": "Porte-conteneurs"})
    return d


@st.cache_data
def sources() -> pd.DataFrame:
    return pd.read_csv(RACINE / "data" / "sources.csv")


def serie(port: str, col: str = "total") -> pd.Series:
    v = volumes()
    return v[v.port == port].set_index("mois")[col].asfreq("MS")
