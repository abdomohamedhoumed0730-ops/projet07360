import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from lib import carte, commun, direct, graphes, style
from lib.donnees import nb

CONFIG = {"displayModeBar": False}

style.entete(
    "Temps réel : navires et météo",
    "Navires captés par AIS sur une carte satellite, et conditions de vent qui déterminent l'arrêt des portiques.",
    ["AIS en direct", "Satellite Esri", "Open-Meteo", "Mise à jour chaque minute"],
)

nom = st.segmented_control("Zone", list(direct.ZONES), default="Long Beach / Los Angeles") or "Long Beach / Los Angeles"
zone = direct.ZONES[nom]


@st.fragment(run_every="60s")
def bloc_navires():
    nav, msg, secours = commun.navires(nom)
    if not len(nav):
        style.encart("Aucun navire affiché pour le moment",
                     f"{msg or 'aucun message reçu'}."
                     + (" La couverture AIS gratuite est faible à Djibouti : les navires apparaissent surtout quand "
                        "ils arrivent dans les approches du golfe d'Aden." if zone["cle"] == "dji" else ""),
                     couleur="or")
        return

    k1, k2, k3, k4 = st.columns(4, gap="medium")
    k1.metric("Navires captés", len(nav))
    k2.metric("Au mouillage", int((nav.statut_code == 1).sum()))
    k3.metric("En route", int((nav.statut_code == 0).sum()))
    k4.metric("Amarrés", int((nav.statut_code == 5).sum()))

    mode = st.segmented_control("Affichage", ["Points", "Carte de chaleur", "Clusters"], default="Points",
                                key="mode_carte") or "Points"
    st_folium(carte.construire(zone, nav, mode), height=580, use_container_width=True, returned_objects=[])
    legende = {
        "Points": "Un rond par navire, coloré par statut, grossi avec la vitesse.",
        "Carte de chaleur": "Rouge : forte concentration de navires. Bleu : peu de navires.",
        "Clusters": "Cliquez sur un cercle pour le déployer et voir les navires qu'il regroupe.",
    }[mode]
    st.caption(legende + (f" ⚠️ {msg}." if secours else " Navires vus depuis moins de 20 minutes."))

    with st.expander("Détail par type et statut"):
        st.dataframe(nav.groupby(["type", "statut"]).size().unstack(fill_value=0), width="stretch")


bloc_navires()

style.section("Météo et contraintes sur les grues", "Les portiques s'arrêtent quand les rafales dépassent 72 km/h.")
m = commun.meteo(nom)
if not m["vent"]:
    style.encart("Météo indisponible", f"Open-Meteo ne répond pas ({m['erreur']}) et aucun relevé de secours n'existe.",
                 couleur="rouge")
else:
    if m["secours"]:
        style.encart("Relevé de secours", f"Open-Meteo ne répond pas ({m['erreur']}) : affichage du relevé du "
                                          f"{m['releve']}.", couleur="or")
    cur, cm = m["vent"]["current"], (m["mer"] or {}).get("current", {})
    k1, k2, k3 = st.columns(3, gap="medium")
    style.kpi("Vent", f"{nb(cur['wind_speed_10m'])} km/h", ref="Vitesse moyenne actuelle", maj=m["releve"] or "",
              accent="#22D3EE")
    style.kpi("Rafales", f"{nb(cur['wind_gusts_10m'])} km/h", ref="Pointes actuelles", maj=m["releve"] or "",
              accent="#FF8A3D")
    style.kpi("Vagues", f"{nb(cm.get('wave_height') or 0, 1)} m", ref="Hauteur significative", maj=m["releve"] or "",
              accent="#38BDF8")

    h = m["vent"]["hourly"]
    df_vent = pd.DataFrame({"heure": pd.to_datetime(h["time"]), "vent": h["wind_speed_10m"],
                            "rafales": h["wind_gusts_10m"]})
    st.plotly_chart(graphes.vent(df_vent, direct.VIGILANCE_KMH, direct.ARRET_GRUES_KMH), width="stretch", config=CONFIG)
    if (m["mer"] or {}).get("hourly"):
        df_vag = pd.DataFrame({"heure": pd.to_datetime(m["mer"]["hourly"]["time"]),
                               "vagues": m["mer"]["hourly"]["wave_height"]})
        st.plotly_chart(graphes.vagues(df_vag), width="stretch", config=CONFIG)

    g = direct.fenetre_grues(m)
    if g["heures_arret"]:
        style.encart("Arrêt probable des portiques", f"{g['heures_arret']} heures sur les 48 prochaines, rafales "
                     f"maximales {nb(g['rafales_max'])} km/h.", couleur="rouge",
                     pourquoi="Décaler les navires concernés et prévoir moins de cadence.")
    elif g["heures_vigilance"]:
        style.encart("Vigilance vent", f"{g['heures_vigilance']} heures sur les 48 prochaines au-dessus du seuil "
                     "de vigilance.", couleur="or", pourquoi="Réduire la cadence de levage.")
    else:
        style.encart("Pas de contrainte de vent", f"Rafales maximales {nb(g['rafales_max'])} km/h sur 48 heures.",
                     couleur="vert")
