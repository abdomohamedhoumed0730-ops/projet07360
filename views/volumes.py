import pandas as pd
import streamlit as st

from lib import commun, graphes, style
from lib.donnees import mois_fr, nb, serie, volumes
from lib.modeles import anomalies, prevoir, tester

style.entete(
    "Volumes de Los Angeles et Long Beach",
    "Historique de 2019 à 2026, prévision à 3 mois avec ses marges d'incertitude, et mois atypiques repérés "
    "automatiquement.",
    ["Total comparable", "STL + ARIMA", "Forêt d'isolement", "Sources : port de LA, BTS"],
)

port = st.segmented_control("Port", ["Long Beach", "Los Angeles"], default="Long Beach") or "Long Beach"
v = volumes()
d = v[v.port == port]
y = serie(port).dropna()
prev = prevoir(y, 3)
test = tester(y, 12)
atyp_tout = anomalies(y)
atyp = atyp_tout[atyp_tout.atypique]
dernier = y.index.max()

t12, t12p = y.iloc[-12:].sum(), y.iloc[-24:-12].sum()
variation = (t12 / t12p - 1) * 100

k1, k2, k3 = st.columns(3, gap="medium")
with k1:
    style.kpi(f"{port} · 12 derniers mois", f"{nb(t12 / 1e6, 2)} M",
              f"{variation:+.1f} % vs 12 mois précédents".replace(".", ","), bon=variation >= 0,
              ref=f"Fin de série : {mois_fr(dernier)} · total comparable en EVP",
              maj="port de LA ; BTS pour Long Beach", accent="#22D3EE")
with k2:
    style.kpi("Erreur moyenne de la prévision", f"{nb(test['erreur_modele'], 1)} %",
              f"{nb(test['erreur_naive'] - test['erreur_modele'], 1)} pt de mieux que « même mois N-1 »",
              bon=True, ref=f"Test sur les 12 derniers mois réels ({test['dans_marge80']}/{test['h']} dans la marge 80 %)",
              maj="STL + ARIMA(1,1,0)", accent="#34D399")
with k3:
    dernier_atyp = mois_fr(atyp.index.max()) if len(atyp) else "aucun"
    style.kpi("Mois atypiques repérés", f"{len(atyp)}", "5 % des mois", bon=None,
              ref=f"Le plus récent : {dernier_atyp}", maj="forêt d'isolement, 500 arbres, graine fixe",
              accent="#F43F5E")

style.section("Historique et prévision", "Trait bleu : données réelles. Pointillés dorés : prévision. "
                                         "Losanges rouges : mois qui sortent de l'ordinaire.")
st.plotly_chart(graphes.prevision(y, prev, atyp, f"{port} · volumes mensuels, prévision à 3 mois et anomalies"),
                width="stretch", config={"displayModeBar": False})

style.section("Composition et comparaison", "À gauche, la part des imports, des exports et des vides. "
                                            "À droite, les deux ports sur le même axe.")
g1, g2 = st.columns(2, gap="large")
annuel = d.assign(annee=d.mois.dt.year).groupby("annee")[["imports_pleins", "exports_pleins", "vides_export"]].sum()
annuel = (annuel.rename(columns={"imports_pleins": "Importations (pleins)", "exports_pleins": "Exportations (pleins)",
                                 "vides_export": "Vides à l'export"})
          .reset_index().melt("annee", var_name="flux", value_name="EVP"))
with g1:
    st.plotly_chart(graphes.composition(annuel, f"{port} · flux par année"), width="stretch",
                    config={"displayModeBar": False})
with g2:
    st.plotly_chart(graphes.comparaison_ports(commun.indicateurs_historiques()["lb_serie"],
                                              commun.indicateurs_historiques()["la_serie"],
                                              "Long Beach et Los Angeles · total comparable"),
                    width="stretch", config={"displayModeBar": False})

style.section("Détail", "Les chiffres derrière les graphiques, prêts à vérifier.")
c1, c2 = st.columns(2, gap="large")
with c1:
    st.markdown("**Prévision à 3 mois**")
    tab = prev.assign(mois=prev.mois.map(mois_fr)).set_index("mois")
    st.dataframe(tab.round(0).rename(columns={"prevision": "prévision", "bas80": "bas 80 %", "haut80": "haut 80 %",
                                              "bas95": "bas 95 %", "haut95": "haut 95 %"}),
                 width="stretch")
with c2:
    st.markdown("**Mois atypiques**")
    if len(atyp):
        tab_a = pd.DataFrame({"mois": [mois_fr(m) for m in atyp.index], "EVP": atyp.valeur.round(0).values,
                              "variation sur un an": (atyp.var_an * 100).round(0).values,
                              "variation sur un mois": (atyp.var_mois * 100).round(0).values})
        st.dataframe(tab_a, hide_index=True, width="stretch")
    else:
        st.info("Aucun mois atypique sur cette série.")

style.encart("Méthode",
             f"Prévision : décomposition STL de log(EVP), puis ARIMA(1,1,0) sur la partie sans saisonnalité, "
             f"puis saisonnalité remise. Anomalies : forêt d'isolement sur la variation annuelle et mensuelle. "
             f"Test : {mois_fr(test['debut'])} à {mois_fr(test['fin'])}.",
             couleur="violet")
style.encart("Limites",
             "Long Beach vient du BTS, qui ne publie pas les vides à l'import (moins de 2 % du total) ; "
             "juillet 2020 est corrigé d'après le communiqué du port. La prévision prolonge le passé et ne "
             "connaît pas les chocs à venir.", couleur="orange")
