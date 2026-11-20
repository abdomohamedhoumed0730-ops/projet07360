"""
Système visuel du tableau de bord : palette, styles CSS et petits composants HTML réutilisables.
Tout passe par ces fonctions, pour que chaque page ait le même langage graphique.
"""
import streamlit as st

PALETTE = {
    "fond": "#07131F", "carte": "#0F2236", "carte2": "#132C45", "bord": "#1B3A55",
    "texte": "#E2EEF7", "muet": "#8AA4BA",
    "cyan": "#22D3EE", "orange": "#FF8A3D", "vert": "#34D399", "rouge": "#F43F5E",
    "violet": "#A78BFA", "bleu": "#38BDF8", "or": "#FBBF24",
}

CSS = """
#MainMenu, footer, [data-testid="stDecoration"] { visibility: hidden; height: 0; }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1400px; }

h1, h2, h3 { color: #E2EEF7; letter-spacing: -0.02em; }
h1 { font-weight: 800; }

/* ---- Bannière d'en-tête ---- */
.hero {
    position: relative; overflow: hidden; border-radius: 22px; padding: 28px 32px; margin-bottom: 22px;
    background: radial-gradient(1200px 300px at 85% -20%, rgba(34,211,238,0.35), transparent 60%),
                linear-gradient(120deg, #0B2A44 0%, #0E4A63 55%, #0F5E73 100%);
    border: 1px solid rgba(34,211,238,0.25); box-shadow: 0 18px 40px rgba(0,0,0,0.35);
}
.hero-kicker { font-size: 0.75rem; letter-spacing: 0.18em; color: #7DD3FC; font-weight: 700; }
.hero-titre { font-size: 2.1rem; font-weight: 800; color: #FFFFFF; line-height: 1.15; margin-top: 6px; }
.hero-sous { font-size: 1.02rem; color: #BFE7F4; margin-top: 8px; max-width: 880px; }
.chips { margin-top: 16px; }
.chips span {
    display: inline-block; padding: 4px 12px; margin: 0 8px 8px 0; border-radius: 999px;
    background: rgba(255,255,255,0.10); border: 1px solid rgba(255,255,255,0.18);
    font-size: 0.82rem; color: #E6F7FB; font-weight: 600;
}

/* ---- Cartes KPI ---- */
.kpi {
    position: relative; border-radius: 18px; padding: 18px 20px 16px 20px; min-height: 176px;
    background: linear-gradient(160deg, #132C45 0%, #0F2236 100%);
    border: 1px solid #1B3A55; box-shadow: 0 10px 26px rgba(0,0,0,0.25);
    transition: transform .15s ease, box-shadow .15s ease;
}
.kpi:hover { transform: translateY(-2px); box-shadow: 0 14px 32px rgba(0,0,0,0.35); }
.kpi::before {
    content: ""; position: absolute; left: 0; top: 16px; bottom: 16px; width: 4px; border-radius: 4px;
    background: var(--accent, #22D3EE);
}
.kpi-label { font-size: 0.82rem; color: #8AA4BA; font-weight: 600; text-transform: uppercase; letter-spacing: .06em; }
.kpi-valeur { font-size: 2.05rem; font-weight: 800; color: #FFFFFF; margin-top: 6px; line-height: 1.1; }
.kpi-unite { font-size: 1rem; color: #8AA4BA; font-weight: 600; margin-left: 4px; }
.delta { display: inline-block; margin-top: 8px; padding: 3px 10px; border-radius: 999px; font-size: .82rem; font-weight: 700; }
.delta.bon { background: rgba(52,211,153,0.15); color: #34D399; }
.delta.mauvais { background: rgba(244,63,94,0.15); color: #FB7185; }
.delta.neutre { background: rgba(138,164,186,0.15); color: #A9BCCB; }
.kpi-ref { font-size: .78rem; color: #8AA4BA; margin-top: 10px; }
.kpi-maj { font-size: .72rem; color: #5F7A90; margin-top: 2px; }

/* ---- Titres de section ---- */
.section { margin: 30px 0 12px 0; }
.section-titre { font-size: 1.35rem; font-weight: 800; color: #E2EEF7; }
.section-sous { font-size: .95rem; color: #8AA4BA; margin-top: 2px; }

/* ---- Encarts (conseils, recommandations, notes) ---- */
.encart {
    border-radius: 16px; padding: 16px 18px; margin-bottom: 12px;
    background: #0F2236; border: 1px solid #1B3A55; color: #CFE3EF; line-height: 1.5;
}
.encart b { color: #FFFFFF; }
.encart .titre { font-weight: 800; color: #FFFFFF; font-size: 1.02rem; }
.encart .why { font-size: .85rem; color: #8AA4BA; margin-top: 6px; }
.encart-cyan { border-left: 4px solid #22D3EE; }
.encart-orange { border-left: 4px solid #FF8A3D; }
.encart-vert { border-left: 4px solid #34D399; }
.encart-rouge { border-left: 4px solid #F43F5E; }
.encart-violet { border-left: 4px solid #A78BFA; }
.encart-or { border-left: 4px solid #FBBF24; }

/* ---- Barre latérale ---- */
[data-testid="stSidebar"] { background: linear-gradient(180deg, #0A1B2D 0%, #07131F 100%); border-right: 1px solid #1B3A55; }
[data-testid="stSidebar"] h3 { color: #E2EEF7; }
[data-testid="stSidebar"] [aria-current="page"] { background: rgba(34,211,238,0.12); border-radius: 10px; }

/* ---- Tableaux et boutons segmentés ---- */
[data-testid="stDataFrame"] { border-radius: 14px; overflow: hidden; border: 1px solid #1B3A55; }
[data-testid="stMetric"] { background: #0F2236; border-radius: 14px; padding: 12px 14px; border: 1px solid #1B3A55; }
[data-testid="stAlert"] { border-radius: 14px; }
"""


def appliquer() -> None:
    """À appeler une fois au début de app.py : injecte le style sur toutes les pages."""
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def entete(titre: str, sous: str, badges: list) -> None:
    """Bannière d'en-tête (une seule ligne HTML pour éviter les blocs de code)."""
    chips = "".join(f"<span>{b}</span>" for b in badges)
    st.markdown(
        f'<div class="hero"><div class="hero-kicker">TERMINAL · PORT DE LONG BEACH · SAN PEDRO BAY</div>'
        f'<div class="hero-titre">{titre}</div><div class="hero-sous">{sous}</div>'
        f'<div class="chips">{chips}</div></div>', unsafe_allow_html=True)


def kpi(label: str, valeur: str, delta: str = None, bon: bool = True, ref: str = "", maj: str = "",
        accent: str = "#22D3EE") -> None:
    """Carte indicateur : valeur, variation colorée, référence et date de mise à jour."""
    pastille = ""
    if delta:
        classe = "neutre" if bon is None else ("bon" if bon else "mauvais")
        pastille = f'<span class="delta {classe}">{delta}</span>'
    st.markdown(
        f'<div class="kpi" style="--accent:{accent}"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-valeur">{valeur}</div>{pastille}'
        f'<div class="kpi-ref">{ref}</div><div class="kpi-maj">{maj}</div></div>', unsafe_allow_html=True)


def section(titre: str, sous: str = "") -> None:
    st.markdown(f'<div class="section"><div class="section-titre">{titre}</div>'
                f'<div class="section-sous">{sous}</div></div>', unsafe_allow_html=True)


def encart(titre: str, texte: str, couleur: str = "cyan", pourquoi: str = "") -> None:
    """Encart coloré : une action, une explication, une source ou une limite."""
    bloc = f'<div class="why">{pourquoi}</div>' if pourquoi else ""
    st.markdown(f'<div class="encart encart-{couleur}"><div class="titre">{titre}</div>'
                f'<div>{texte}</div>{bloc}</div>', unsafe_allow_html=True)
