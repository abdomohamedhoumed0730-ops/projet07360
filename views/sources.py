import streamlit as st

from lib.donnees import sources

st.title("📚 Sources et méthode")
st.dataframe(sources(), hide_index=True, width="stretch")
st.subheader("Méthode")
st.markdown("""
- **Total comparable** = imports pleins + exports pleins + vides à l'export (le BTS ne publie pas les vides à l'import de Long Beach).
- **Prévision** : la saisonnalité est retirée par une décomposition STL ; le reste est prévu par un ARIMA(1,1,0) ;
  la saisonnalité est ensuite remise. Horizon 3 mois, marges à 80 % et 95 %. Testée sur les 12 derniers mois connus.
- **Mois atypiques** : forêt d'isolement (scikit-learn) sur deux variables, la variation sur un an et la variation sur un mois.
  On retient les 5 % de mois les plus faciles à isoler.
- **Alerte météo** : heures des 48 prochaines où les rafales atteignent 72 km/h (arrêt probable des portiques) ou 50 km/h
  ou 2 m de vagues (vigilance).
- **AIS** : un récepteur unique écoute aisstream.io en continu ; un navire reste affiché 20 min après son dernier message.
- **Ne pas rappeler les API** : historique lu dans des CSV ; météo en cache 1 h ; la page du direct relit seulement le registre AIS.
""")
st.subheader("Limites")
st.markdown("""
- Long Beach : BTS (polb.com inaccessible depuis Djibouti), jusqu'à septembre 2026, sans vides à l'import ; une erreur corrigée (juillet 2020).
- CNUCED : 22 économies en accès libre, 2018-2023 ; **Djibouti absent** (comparaison par le CPPI).
- CPPI : score relatif (0 = port médian de l'année) ; 403 ports classés en 2024, 400 en 2025.
- AIS gratuit : couverture faible à Djibouti ; type de navire parfois inconnu ; « en route » inclut les navires qui partent.
- Seuils (15 navires, 50 / 72 km/h, 2 m) : hypothèses de travail à valider avec le terminal.
- La prévision prolonge le passé et ne connaît pas les chocs à venir.
""")
