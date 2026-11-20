import streamlit as st

from lib import graphes, style
from lib.donnees import cnuced, cppi

CONFIG = {"displayModeBar": False}

style.entete(
    "Long Beach face aux autres ports",
    "Deux sources qui ne mesurent pas la même chose, présentées séparément : un score par port (CPPI), "
    "et des chiffres par pays (CNUCED).",
    ["CPPI 2020 à 2025", "CNUCED 2018 à 2023", "Djibouti via le CPPI"],
)

c = cppi()
lb, dj, bu = c.loc["Long Beach"], c.loc["Djibouti"], c.loc["Busan"]

k1, k2, k3 = st.columns(3, gap="medium")
with k1:
    gain = lb.cppi2025 - lb.cppi2024
    style.kpi("Score CPPI · Long Beach", f"{lb.cppi2025:.1f}".replace(".", ","),
              f"{gain:+.1f} pt vs 2024".replace(".", ","), bon=gain >= 0,
              ref=f"Rang 2025 : {int(lb.rang2025)}e sur 400 · rang 2024 : {int(lb.rang2024)}e",
              maj="Banque mondiale & S&P Global, édition 2025", accent="#FF8A3D")
with k2:
    gain_dj = int(dj.rang2024 - dj.rang2025)
    style.kpi("Rang CPPI · Djibouti", f"{int(dj.rang2025)}e",
              f"+{gain_dj} places vs 2024", bon=gain_dj > 0,
              ref=f"Score 2025 : {dj.cppi2025:.1f} · 2024 : rang {int(dj.rang2024)}e".replace(".", ","),
              maj="même source, même méthode", accent="#22D3EE")
with k3:
    ecart = bu.cppi2025 - lb.cppi2025
    style.kpi("Écart avec Busan", f"{ecart:.0f} pts",
              f"Busan : {bu.cppi2025:.1f} · rang {int(bu.rang2025)}e".replace(".", ","), bon=None,
              ref="Hub transpacifique à comparer au terminal", maj="CPPI 2025", accent="#A78BFA")

style.section("Le score CPPI, port par port",
              "Chaque cercle plein est l'édition 2025, chaque cercle creux l'édition 2024. Plus le point est à droite, "
              "plus le port repart vite à quai.")
st.plotly_chart(graphes.cppi_pente(c[["cppi2024", "cppi2025"]], "Édition 2024 → édition 2025"),
                width="stretch", config=CONFIG)

style.section("Évolution 2020 à 2025", "Long Beach et Djibouti mis en avant ; les autres ports restent en arrière-plan.")
st.plotly_chart(graphes.cppi_serie(c, "Score CPPI annuel par port"), width="stretch", config=CONFIG)

style.section("CNUCED : temps au port et escales, par pays",
              "Base en accès libre : 22 économies et le monde, 2018 à 2023. Les États-Unis sont en orange.")
marche = st.segmented_control("Type de navires", ["Tous navires", "Porte-conteneurs"],
                              default="Tous navires") or "Tous navires"
u = cnuced()
u = u[u.marche == marche]
annee = int(u.annee.max())
dern = u[u.annee == annee].dropna(subset=["temps_median_j"])
g1, g2 = st.columns(2, gap="large")
with g1:
    st.plotly_chart(graphes.cnuced_temps(dern, f"Temps médian au port · {marche.lower()} · {annee}"),
                    width="stretch", config=CONFIG)
with g2:
    esc = u[(u.pays != "Monde")].dropna(subset=["escales"])
    st.plotly_chart(graphes.escales(esc, "Nombre d'escales par pays"), width="stretch", config=CONFIG)

style.encart("Pourquoi deux sources ?",
             "Le CPPI donne un score par port, la CNUCED des chiffres par pays. Elles ne se lisent jamais sur le "
             "même axe, sinon on comparerait des choses différentes.", couleur="cyan")
style.encart("Limite importante",
             "Djibouti n'est pas dans la base CNUCED en accès libre. Sa position vient donc du CPPI uniquement, "
             "et ne doit pas être comparée directement aux temps médians par pays.", couleur="rouge")
