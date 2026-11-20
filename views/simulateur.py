import pandas as pd
import streamlit as st

from lib import commun, graphes, style
from lib.donnees import mois_fr, nb

CONFIG = {"displayModeBar": False}

style.entete(
    "Simulateur de scénarios de trafic",
    "Changez le trafic attendu et voyez l'effet sur la prévision, sur la jauge de tension et sur les mois à venir.",
    ["Scénario", "Comparaison à l'an dernier", "Indice de tension"],
)

i = commun.indicateurs_historiques()
prev, serie = i["prev"], i["lb_serie"]

style.section("Vos hypothèses", "Un seul curseur : la variation du trafic par rapport à la prévision de base.")
variation = st.slider("Variation du trafic par rapport à la prévision (%)", min_value=-30, max_value=30, value=0, step=1,
                      help="0 % = prévision de base. +10 % = dix pour cent de conteneurs en plus que prévu.")

scenario = prev.prevision * (1 + variation / 100)
ref = [serie[m - pd.DateOffset(years=1)] for m in prev.mois]
ecart_n1 = (scenario.values / ref - 1) * 100
score = graphes.score_tension(float((scenario.iloc[0] / i["ref_prev"] - 1) * 100))
score_base = graphes.score_tension(float((prev.prevision.iloc[0] / i["ref_prev"] - 1) * 100))

k1, k2, k3 = st.columns(3, gap="medium")
with k1:
    style.kpi(f"Scénario · {mois_fr(prev.mois.iloc[0])}", f"{nb(scenario.iloc[0] / 1e3)} k",
              f"{variation:+d} % vs prévision de base".replace("-", "−"),
              bon=None, ref=f"Prévision de base : {nb(prev.prevision.iloc[0] / 1e3)} k EVP",
              maj="calcul local, aucune donnée modifiée", accent="#FF8A3D")
with k2:
    ecart0 = ecart_n1[0]
    style.kpi("Écart avec l'an dernier", f"{ecart0:+.1f} %".replace(".", ",").replace("-", "−"),
              f"Même mois N-1 : {nb(ref[0] / 1e3)} k EVP", bon=None,
              ref="Positif = plus de trafic qu'un an plus tôt", maj="prévision sur 3 mois", accent="#22D3EE")
with k3:
    style.kpi("Indice de tension", f"{score:.0f} / 100", f"base : {score_base:.0f}", bon=None,
              ref="50 = même niveau qu'un an plus tôt", maj="indice maison, voir Sources & méthode",
              accent="#A78BFA")

style.section("Trois mois : base, an dernier et scénario", "Les barres orange suivent votre curseur.")
st.plotly_chart(graphes.comparaison_scenario(
    list(prev.mois), list(ref), list(prev.prevision), list(scenario),
    "Long Beach · EVP par mois selon le scénario"), width="stretch", config=CONFIG)

g1, g2 = st.columns([1, 1], gap="large")
with g1:
    st.plotly_chart(graphes.jauge(score, "Tension du scénario"), width="stretch", config=CONFIG)
with g2:
    tab = pd.DataFrame({
        "mois": [mois_fr(m) for m in prev.mois],
        "même mois N-1 (EVP)": [round(r) for r in ref],
        "scénario (EVP)": [round(s) for s in scenario],
        "écart vs N-1 (%)": [round(e, 1) for e in ecart_n1],
    })
    st.markdown("**Détail mois par mois**")
    st.dataframe(tab, hide_index=True, width="stretch")

style.encart("Ce que le simulateur fait",
             "Il multiplie la prévision de base par votre curseur, puis compare le résultat aux mêmes mois de l'an "
             "dernier. Il ne calcule ni les effectifs ni les cadences : c'est un outil pour tester une hypothèse de "
             "trafic avant de décider.", couleur="cyan")
style.encart("Ce qu'il ne fait pas",
             "Il ne prend pas en compte les chocs à venir (grève, panne, conflit, changement de route des armateurs). "
             "Les mois d'écart élevé demandent une vérification avec le terminal.", couleur="orange")
