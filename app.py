"""
Terminal de Long Beach – tableau de bord portuaire.
Lancer :  streamlit run app.py
Clé aisstream.io : dans .streamlit/secrets.toml (local) ou dans Settings → Secrets (Streamlit Cloud),
sous le nom AISSTREAM_API_KEY. Elle n'est jamais écrite dans le code.
"""
import streamlit as st

from lib import style

st.set_page_config(page_title="Terminal Long Beach · tableau de bord", page_icon="⚓",
                   layout="wide", initial_sidebar_state="expanded")
style.appliquer()

with st.sidebar:
    st.markdown("### ⚓ Terminal Long Beach")
    st.caption("Pilotage des équipes, des postes à quai et de la concurrence portuaire.")
    st.divider()
    st.markdown(
        "**Par où commencer ?**\n\n"
        "1. **Synthèse** : l'essentiel et les actions du moment.\n"
        "2. **Simulateur** : testez un scénario de trafic.\n"
        "3. **Volumes** : historique, prévision et mois atypiques.\n"
        "4. **Comparaison** : Long Beach face au monde, dont Djibouti.\n"
        "5. **Temps réel** : navires en carte satellite et météo.\n"
        "6. **Sources** : d'où viennent les chiffres, et leurs limites."
    )
    st.divider()
    st.caption("Projet M2 IAMD · Université de Djibouti")

pages = [
    st.Page("views/synthese.py", title="Synthèse", icon="📋", default=True),
    st.Page("views/simulateur.py", title="Simulateur", icon="🧪"),
    st.Page("views/volumes.py", title="Volumes LA & LB", icon="📦"),
    st.Page("views/benchmark.py", title="Comparaison mondiale", icon="🌍"),
    st.Page("views/temps_reel.py", title="Temps réel", icon="📡"),
    st.Page("views/sources.py", title="Sources & méthode", icon="📚"),
]
st.navigation(pages).run()
