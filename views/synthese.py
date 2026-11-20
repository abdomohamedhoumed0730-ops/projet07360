import pandas as pd
import streamlit as st

from lib import commun, direct, graphes, regles, style
from lib.donnees import mois_fr, nb
from lib.modeles import anomalies

ZONE = "Long Beach / Los Angeles"
CONFIG = {"displayModeBar": False}
COULEUR_ACTION = {"🔴": "rouge", "🟠": "orange", "🟢": "vert", "🔵": "cyan"}

style.entete(
    "Long Beach : décider pour les jours et le mois qui viennent",
    "Dimensionner les équipes et les postes à quai, et situer le terminal face à Los Angeles, Vancouver, "
    "Busan et Djibouti.",
    ["EVP mensuels", "Prévision à 3 mois", "CPPI 2025", "CNUCED", "AIS en direct", "Météo"],
)

i = commun.indicateurs_historiques()
c, p1 = i["cppi"], i["prev"].iloc[0]
pct_an = (i["lb"] / i["lb_n1"] - 1) * 100
ecart_part = i["part"] - i["part19"]
pct_prev = (p1.prevision / i["ref_prev"] - 1) * 100
rang_dj = int(c.loc["Djibouti", "rang2025"])
gain_dj = int(c.loc["Djibouti", "rang2024"] - c.loc["Djibouti", "rang2025"])
histo_24 = i["lb_serie"].tail(24)

# ---- Quatre indicateurs clés, chacun avec sa courbe ----
style.section("L'essentiel", "Quatre indicateurs à lire d'un coup d'œil. Chaque carte donne sa référence et sa date.")
k1, k2, k3, k4 = st.columns(4, gap="medium")
with k1:
    style.kpi(f"EVP Long Beach · {mois_fr(i['dernier'])}", f"{nb(i['lb'] / 1e3)} k",
              f"{pct_an:+.1f} % sur un an".replace(".", ","), bon=pct_an >= 0,
              ref=f"Réf. {mois_fr(i['dernier'] - pd.DateOffset(years=1))} : {nb(i['lb_n1'] / 1e3)} k EVP",
              maj=i["maj"], accent="#22D3EE")
    st.plotly_chart(graphes.sparkline(histo_24), width="stretch", config=CONFIG)
with k2:
    style.kpi("Part de Long Beach (12 mois)", f"{nb(i['part'], 1)} %",
              f"{ecart_part:+.1f} pt vs 2019".replace(".", ","), bon=ecart_part >= 0,
              ref=f"2019 : {nb(i['part19'], 1)} % de San Pedro Bay", maj=i["maj"], accent="#FF8A3D")
    st.plotly_chart(graphes.sparkline(i["lb_serie"].tail(24) / (i["lb_serie"].tail(24) + i["la_serie"].tail(24)) * 100,
                                      couleur="#FF8A3D"), width="stretch", config=CONFIG)
with k3:
    style.kpi(f"Prévision · {mois_fr(i['mois_prev'])}", f"{nb(p1.prevision / 1e3)} k",
              f"{pct_prev:+.1f} % vs an dernier".replace(".", ","), bon=None,
              ref=f"Marge 80 % : {nb(p1.bas80 / 1e3)} – {nb(p1.haut80 / 1e3)} k · erreur test {nb(i['test']['erreur_modele'], 1)} %",
              maj="modèle STL + ARIMA", accent="#FBBF24")
    st.plotly_chart(graphes.sparkline(i["lb_serie"].tail(12) / 1e3, couleur="#FBBF24"),
                    width="stretch", config=CONFIG)
with k4:
    style.kpi("Rang CPPI 2025 · Djibouti", f"{rang_dj}e",
              f"+{gain_dj} places vs 2024", bon=gain_dj > 0,
              ref=f"Long Beach : {int(c.loc['Long Beach', 'rang2025'])}e · Busan : {int(c.loc['Busan', 'rang2025'])}e",
              maj="Banque mondiale & S&P Global, édition 2025", accent="#A78BFA")
    st.plotly_chart(graphes.sparkline(c.loc["Djibouti", ["cppi2020", "cppi2021", "cppi2022", "cppi2023", "cppi2024", "cppi2025"]]
                                      .astype(float).rename(lambda x: x[-4:]), couleur="#A78BFA"),
                    width="stretch", config=CONFIG)

# ---- Tension et prévision ----
style.section("Tension prévue", "La jauge compare la prévision au niveau de l'an dernier. 50 = identique ; "
                                "au-dessus de 65, renforcer les équipes.")
g1, g2 = st.columns([1, 2], gap="large")
with g1:
    st.plotly_chart(graphes.jauge(graphes.score_tension(pct_prev), f"Prévision {mois_fr(i['mois_prev'])}"),
                    width="stretch", config=CONFIG)
    style.encart("Comment lire la jauge",
                 "Indice maison, de 0 à 100. Il ne mesure ni les effectifs ni la productivité : il indique seulement "
                 "si le trafic prévu est au-dessus ou au-dessous de l'an dernier.", couleur="violet")
with g2:
    hist = i["lb_serie"].tail(36)
    atypiques = anomalies(i["lb_serie"])
    atypiques = atypiques[atypiques.atypique]
    atypiques = atypiques[atypiques.index >= hist.index[0]]
    st.plotly_chart(graphes.prevision(hist, i["prev"], atypiques, "Long Beach · 36 derniers mois et prévision à 3 mois"),
                    width="stretch", config=CONFIG)
    t = i["test"]
    st.caption(f"Test sur {mois_fr(t['debut'])} – {mois_fr(t['fin'])} : erreur moyenne {nb(t['erreur_modele'], 1)} % "
               f"contre {nb(t['erreur_naive'], 1)} % pour « même mois l'an dernier ». "
               f"{t['dans_marge80']} mois sur {t['h']} tombent dans la marge à 80 %.")

# ---- Actions : temps réel + règles ----
style.section("Actions recommandées", "Calculées à partir de la prévision, de la météo et des navires captés. "
                                      "Chaque action indique le seuil qui la déclenche.")


@st.fragment(run_every="60s")
def actions():
    nav, msg, secours = commun.navires(ZONE)
    n = None
    if len(nav):
        n = int(((nav.statut_code == 1) | ((nav.statut_code == 0) & (nav.vitesse_noeuds.fillna(0) > 0.5))).sum())
    m = commun.meteo(ZONE)
    g = direct.fenetre_grues(m)
    ctx = {"prevision_vs_n1": pct_prev, "mois_prev": mois_fr(i["mois_prev"]), "prevision": p1.prevision,
           "ref_prev": i["ref_prev"], "grues": g, "navires_attendus": n,
           "score_lb": c.loc["Long Beach", "cppi2025"], "score_la": c.loc["Los Angeles", "cppi2025"],
           "score_busan": c.loc["Busan", "cppi2025"]}
    colonnes = st.columns(2, gap="medium")
    for idx, (icone, action, pourquoi) in enumerate(regles.recommandations(ctx)):
        with colonnes[idx % 2]:
            style.encart(f"{icone} {action}", "", COULEUR_ACTION.get(icone, "cyan"), pourquoi=f"Déclencheur : {pourquoi}")
    if m["secours"] or secours:
        st.caption("Une source temps réel est en secours : les actions ci-dessus s'appuient sur le dernier relevé disponible.")


actions()
