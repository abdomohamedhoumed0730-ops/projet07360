"""
Met à jour les fichiers de data/raw/ depuis les sources officielles (à lancer une fois par mois).
L'application ne rappelle jamais ces sources : elle lit les CSV.

    pip install requests pandas openpyxl py7zr lxml
    python collect/actualiser.py              # tout
    python collect/actualiser.py cppi cnuced  # seulement certaines sources

Penser ensuite à noter la date de récupération dans data/sources.csv.
"""
import io
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
UA = {"User-Agent": "Mozilla/5.0 (exercice tableau de bord portuaire)"}
MOIS_EN = ["January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"]


def _nombre(s):
    s = str(s).replace(",", "").strip()
    if s.count(".") > 1:                       # coquille du site LA : « 889.,748.15 »
        p = s.split(".")
        s = "".join(p[:-1]) + "." + p[-1]
    return float(s)


def los_angeles():
    url = "https://www.portoflosangeles.org/business/statistics/container-statistics/historical-teu-statistics-{}"
    lignes = []
    for annee in range(2019, datetime.now().year + 1):
        r = requests.get(url.format(annee), headers=UA, timeout=30)
        r.raise_for_status()
        for _, row in pd.read_html(io.StringIO(r.text))[0].iterrows():
            if str(row.iloc[0]) in MOIS_EN and pd.notna(row.iloc[1]):
                v = [_nombre(x) for x in row.iloc[1:8]]
                lignes.append(dict(year=annee, month=MOIS_EN.index(row.iloc[0]) + 1, loaded_imports=v[0],
                                   empty_imports=v[1], total_imports=v[2], loaded_exports=v[3],
                                   empty_exports=v[4], total_exports=v[5], total_teu=v[6]))
    pd.DataFrame(lignes).to_csv(RAW / "la_official.csv", index=False)


def long_beach():
    ind = {"Loaded Import Containers at Select U.S. Ports in TEUs": "loaded_imports",
           "Loaded Export Containers at Select U.S. Ports in TEUs": "loaded_exports",
           "Empty Export Containers at Select U.S. Ports in TEUs": "empty_exports"}
    liste = ",".join(f"'{k}'" for k in ind)
    r = requests.get("https://data.bts.gov/resource/y5ut-ibwt.json", headers=UA, timeout=30, params={
        "$select": "date,indicator,value1", "$limit": 5000,
        "$where": f"measure1='Long Beach' AND indicator in({liste}) AND date >= '2019-01-01'"})
    r.raise_for_status()
    d = pd.DataFrame(r.json())
    d["month"], d["col"], d["value1"] = d.date.str[:7], d.indicator.map(ind), pd.to_numeric(d.value1)
    t = d.pivot_table(index="month", columns="col", values="value1", aggfunc="first").reset_index()
    t.insert(0, "port", "LB")
    t[["port", "month", "loaded_imports", "loaded_exports", "empty_exports"]].to_csv(RAW / "bts_lb.csv", index=False)


def cppi():
    base = "https://openknowledge.worldbank.org/server/api/core/bitstreams/{}/content"
    ports = {"USLAX": "Los Angeles", "USLGB": "Long Beach", "DJJIB": "Djibouti", "KRPUS": "Busan",
             "CAPRR": "Prince Rupert", "CAVAN": "Vancouver"}
    x25 = pd.read_excel(io.BytesIO(requests.get(base.format("9cf20807-7dcd-4de7-9de2-fdb2d0589a73"), headers=UA, timeout=60).content))
    x24 = pd.read_excel(io.BytesIO(requests.get(base.format("6d1086f0-13ed-4d69-92ad-11d93f3e7df6"), headers=UA, timeout=60).content))
    x25 = x25[x25["UN/LOCODE"].isin(ports)].set_index("UN/LOCODE").reindex(list(ports))
    x24 = x24[x24["LOCODE"].isin(ports)].set_index("LOCODE").reindex(list(ports))
    out = pd.DataFrame({"port": list(ports.values()), "locode": list(ports), "pays": x25["Territory"].values,
                        **{f"cppi{a}": x25[f"CPPI {a}"].values for a in range(2020, 2026)},
                        "rang2025": x25["Rank 2025"].values, "escales2025": x25["Number of calls in sample"].values,
                        "rang2024": x24["Rank"].values})
    out.to_csv(RAW / "cppi_ports.csv", sep=";", index=False)


def cnuced():
    import py7zr
    contenu = requests.get("https://unctadstat-api.unctad.org/bulkdownload/US.PortCalls/US_PortCalls", headers=UA, timeout=60).content
    with py7zr.SevenZipFile(io.BytesIO(contenu)) as a:
        a.extractall(RAW)                      # -> US_PortCalls.csv
    lignes = []
    for code in ["0000", "842", "124", "036", "251", "926"]:
        r = requests.get("https://unctadstat-api.unctad.org/datamart-api/US.PortCallsArrivals/10002/Facts",
                         params={"$filter": f"Economy/Code eq '{code}'", "culture": "en"}, headers=UA, timeout=60)
        r.raise_for_status()
        for v in r.json()["value"]:
            if v["CommercialMarket"]["Code"] in ("00", "03") and (v.get("M3760") or {}).get("Value") is not None:
                lignes.append({"economy_code": code, "market_code": v["CommercialMarket"]["Code"],
                               "year": v["Year"], "port_calls": v["M3760"]["Value"]})
    pd.DataFrame(lignes).to_csv(RAW / "cnuced_escales.csv", index=False)


if __name__ == "__main__":
    taches = {"la": los_angeles, "lb": long_beach, "cppi": cppi, "cnuced": cnuced}
    for nom in sys.argv[1:] or taches:
        try:
            taches[nom]()
            print(f"{nom} : mis à jour le {datetime.now():%d/%m/%Y %H:%M}")
        except Exception as e:
            print(f"{nom} : ÉCHEC ({e}) — l'ancien fichier est conservé")
