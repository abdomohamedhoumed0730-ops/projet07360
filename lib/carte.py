"""
Carte satellite des navires : imagerie Esri (sans clé), noms des lieux, points colorés par statut,
regroupement en clusters et carte de chaleur. Construite avec folium, affichée par streamlit-folium.
"""
import html

import folium
import pandas as pd
from folium.plugins import HeatMap, MarkerCluster

SATELLITE = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
LIBELLES = ("https://server.arcgisonline.com/ArcGIS/rest/services/Reference/"
            "World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}")
ATTRIBUTION = "Imagerie © Esri, Maxar, Earthstar Geographics"

COULEURS = {"Au mouillage": "#F76707", "En route": "#1C7ED6", "Amarré": "#2F9E44"}
COULEUR_DEFAUT = "#ADB5BD"
DEGRADE_CHALEUR = {0.2: "#1C7ED6", 0.5: "#FAB005", 0.8: "#F76707", 1.0: "#E03131"}

LEGENDE = """
<div style="position: fixed; bottom: 26px; left: 12px; z-index: 9999; background: rgba(11,60,93,0.92);
            color: #fff; padding: 10px 14px; border-radius: 12px; font: 13px/1.5 sans-serif;
            box-shadow: 0 4px 14px rgba(0,0,0,0.35);">
  <div style="font-weight: 700; margin-bottom: 4px;">Statut des navires</div>
  <div><span style="color:#F76707">●</span> Au mouillage</div>
  <div><span style="color:#1C7ED6">●</span> En route</div>
  <div><span style="color:#2F9E44">●</span> Amarré</div>
  <div><span style="color:#ADB5BD">●</span> Autre / non transmis</div>
  <div style="margin-top:4px; opacity:.85;">Cadre pointillé : zone suivie</div>
</div>
"""


def _point(n: pd.Series) -> folium.CircleMarker:
    """Un navire = un rond coloré par statut, taille selon la vitesse, infobulle détaillée."""
    vitesse = float(n.get("vitesse_noeuds") or 0)
    rayon = max(5.0, min(11.0, 5.0 + vitesse / 3))
    info = (f"<div style='font-family:sans-serif'><b>{html.escape(str(n.get('nom', '')))}</b><br>"
            f"{html.escape(str(n.get('type', '')))} · {html.escape(str(n.get('statut', '')))}<br>"
            f"Vitesse : {vitesse:.1f} nœuds<br>MMSI : {html.escape(str(n.get('mmsi', '')))}</div>")
    return folium.CircleMarker(
        location=[float(n["lat"]), float(n["lon"])], radius=rayon, color="#FFFFFF", weight=1.5,
        fill=True, fill_color=COULEURS.get(n.get("statut"), COULEUR_DEFAUT), fill_opacity=0.95,
        tooltip=info,
    )


def construire(zone: dict, navires: pd.DataFrame, mode: str) -> folium.Map:
    """Renvoie la carte prête à afficher. `mode` : 'Points', 'Carte de chaleur' ou 'Clusters'."""
    carte = folium.Map(location=zone["centre"], zoom_start=zone["zoom"], tiles=None,
                       control_scale=True, zoom_control=True)
    folium.TileLayer(SATELLITE, name="Satellite", attr=ATTRIBUTION, max_zoom=19).add_to(carte)
    folium.TileLayer(LIBELLES, name="Noms", attr=ATTRIBUTION, overlay=True, control=False).add_to(carte)
    folium.Rectangle(bounds=zone["boite"], color="#22B8CF", weight=2, fill=False, dash_array="6 6",
                     tooltip="Zone AIS suivie").add_to(carte)

    if navires is not None and len(navires):
        navires = navires.dropna(subset=["lat", "lon"])
        if mode == "Carte de chaleur":
            HeatMap(navires[["lat", "lon"]].values.tolist(), radius=30, blur=24, min_opacity=0.4,
                    gradient=DEGRADE_CHALEUR, name="Chaleur").add_to(carte)
        elif mode == "Clusters":
            grappe = MarkerCluster(name="Clusters", options={"maxClusterRadius": 45, "showCoverageOnHover": False})
            grappe.add_to(carte)
            for _, n in navires.iterrows():
                _point(n).add_to(grappe)
        else:
            for _, n in navires.iterrows():
                _point(n).add_to(carte)

    carte.get_root().html.add_child(folium.Element(LEGENDE))
    folium.LayerControl(collapsed=True).add_to(carte)
    return carte
