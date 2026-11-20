"""Recommandations pour le chef des opérations du terminal : règles lisibles, chacune avec son déclencheur."""
from lib.direct import ARRET_GRUES_KMH, SEUIL_NAVIRES, VIGILANCE_KMH
from lib.donnees import nb


def _date(iso: str) -> str:
    """'2026-11-20T02:00' -> '20/11 à 02:00'"""
    j, h = iso.split("T")
    return f"{j[8:10]}/{j[5:7]} à {h}"


def recommandations(c: dict) -> list:
    r = []
    # 1) Équipes du mois prochain, d'après la prévision
    ev = c["prevision_vs_n1"]
    if ev > 10:
        r.append(("🟠", f"Renforcer les équipes en {c['mois_prev']} : prévoir environ {ev:.0f} % de postes en plus "
                       "qu'il y a un an (dockers, grutiers, caristes de nuit).",
                  f"prévision {nb(c['prevision'] / 1e3)} k EVP contre {nb(c['ref_prev'] / 1e3)} k un an plus tôt"))
    elif ev < -10:
        r.append(("🟢", f"Trafic en baisse attendu en {c['mois_prev']} : programmer la maintenance des portiques.",
                  f"prévision {ev:+.0f} % sur un an"))
    else:
        r.append(("🟢", f"Effectifs en {c['mois_prev']} : reconduire le planning de l'an dernier.", f"prévision {ev:+.0f} % sur un an"))
    # 2) Vent : arrêt des grues
    g = c.get("grues")
    if g is None:
        r.append(("🟠", "Météo indisponible : vérifier le bulletin avant d'affecter les grutiers.", "Open-Meteo ne répond pas"))
    elif g["heures_arret"] > 0:
        r.append(("🔴", f"Prévoir l'arrêt des portiques à partir du {_date(g['premiere'])} et décaler les "
                       "navires concernés.", f"{g['heures_arret']} h de rafales ≥ {ARRET_GRUES_KMH:.0f} km/h dans les 48 h"))
    elif g["heures_vigilance"] > 0:
        r.append(("🟠", f"Vigilance à partir du {_date(g['premiere'])} : réduire la cadence de levage.",
                  f"{g['heures_vigilance']} h au-dessus de {VIGILANCE_KMH:.0f} km/h ou 2 m de vagues"))
    else:
        r.append(("🟢", "Aucune contrainte de vent sur 48 h pour les portiques.", f"rafales max {nb(g['rafales_max'])} km/h"))
    # 3) Navires attendus (AIS)
    n = c.get("navires_attendus")
    if n is None:
        r.append(("🟠", "AIS indisponible : confirmer les arrivées auprès de la capitainerie.", "pas de flux AIS"))
    elif n >= SEUIL_NAVIRES:
        r.append(("🟠", "Charge élevée à venir : ouvrir un poste à quai supplémentaire ou une équipe de nuit.",
                  f"{n} navires en route ou au mouillage dans la zone (seuil {SEUIL_NAVIRES})"))
    else:
        r.append(("🟢", "Charge normale : planning à quai inchangé.", f"{n} navires en route ou au mouillage dans la zone"))
    # 4) Se comparer (CPPI)
    r.append(("🔵", "Étudier les pratiques de Los Angeles et de Busan, plus rapides à quai que Long Beach.",
              f"CPPI 2025 : Long Beach {c['score_lb']:.0f}, Los Angeles {c['score_la']:.0f}, Busan {c['score_busan']:.0f}"))
    return r
