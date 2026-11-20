"""
Graphiques Plotly du tableau de bord. Chaque fonction renvoie une figure déjà mise en forme
(fond transparent, grille discrète, info-bulles unifiées) pour garder une cohérence visuelle.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from lib.style import PALETTE as P

POLICE = "Inter, Segoe UI, Helvetica, Arial, sans-serif"


def _mise_en_forme(fig: go.Figure, hauteur: int = 380, titre: str = None) -> go.Figure:
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=POLICE, color=P["texte"], size=13), height=hauteur,
        margin=dict(l=8, r=8, t=56 if titre else 24, b=8), hovermode="x unified",
        hoverlabel=dict(bgcolor=P["carte2"], bordercolor=P["bord"], font=dict(family=POLICE)),
        legend=dict(orientation="h", y=1.1, x=0, bgcolor="rgba(0,0,0,0)", title=None),
    )
    if titre:
        fig.update_layout(title=dict(text=titre, x=0, xanchor="left", font=dict(size=16, color=P["texte"])))
    fig.update_xaxes(showgrid=False, linecolor=P["bord"], zeroline=False, tickfont=dict(color=P["muet"]))
    fig.update_yaxes(gridcolor="rgba(138,164,186,0.13)", zeroline=False, tickfont=dict(color=P["muet"]))
    return fig


def sparkline(valeurs: pd.Series, couleur: str = None) -> go.Figure:
    """Mini-courbe sans axes, à placer sous une carte KPI."""
    couleur = couleur or P["cyan"]
    fig = go.Figure(go.Scatter(x=valeurs.index, y=valeurs.values, mode="lines", line=dict(color=couleur, width=2.5),
                               fill="tozeroy", fillcolor="rgba(34,211,238,0.12)", hoverinfo="skip"))
    fig.update_layout(height=70, margin=dict(l=0, r=0, t=4, b=0), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(visible=False), yaxis=dict(visible=False),
                      showlegend=False)
    return fig


def prevision(hist: pd.Series, prev: pd.DataFrame, atypiques: pd.DataFrame, titre: str) -> go.Figure:
    """Historique, prévision à 3 mois, marges à 80 et 95 %, et mois atypiques en losange rouge."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist.index, y=hist.values, name="Réel (total comparable)", mode="lines",
                             line=dict(color=P["bleu"], width=2.6), fill="tozeroy",
                             fillcolor="rgba(56,189,248,0.08)",
                             hovertemplate="%{y:,.0f} EVP<extra></extra>"))
    x_bande = list(prev.mois) + list(prev.mois[::-1])
    fig.add_trace(go.Scatter(x=x_bande, y=list(prev.haut95) + list(prev.bas95[::-1]), fill="toself",
                             fillcolor="rgba(251,191,36,0.10)", line=dict(width=0), name="Marge 95 %",
                             hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=x_bande, y=list(prev.haut80) + list(prev.bas80[::-1]), fill="toself",
                             fillcolor="rgba(251,191,36,0.22)", line=dict(width=0), name="Marge 80 %",
                             hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=prev.mois, y=prev.prevision, name="Prévision", mode="lines+markers",
                             line=dict(color=P["or"], width=2.6, dash="dash"), marker=dict(size=8),
                             hovertemplate="%{y:,.0f} EVP<extra>prévision</extra>"))
    if atypiques is not None and len(atypiques):
        fig.add_trace(go.Scatter(x=atypiques.index, y=atypiques.valeur, name="Mois atypique", mode="markers",
                                 marker=dict(symbol="diamond", size=13, color=P["rouge"],
                                             line=dict(color="#FFFFFF", width=1)),
                                 hovertemplate="%{y:,.0f} EVP<extra>atypique</extra>"))
    return _mise_en_forme(fig, 420, titre)


def composition(annuel: pd.DataFrame, titre: str) -> go.Figure:
    """Barres empilées : importations, exportations et vides, par année."""
    couleurs = {"Importations (pleins)": P["cyan"], "Exportations (pleins)": P["vert"], "Vides à l'export": "#64748B"}
    fig = go.Figure()
    for flux, couleur in couleurs.items():
        d = annuel[annuel.flux == flux]
        fig.add_trace(go.Bar(x=d.annee.astype(str), y=d.EVP, name=flux, marker=dict(color=couleur, line=dict(width=0)),
                             hovertemplate="%{y:,.0f} EVP<extra>" + flux + "</extra>"))
    fig.update_layout(barmode="stack", bargap=0.35)
    return _mise_en_forme(fig, 360, titre)


def comparaison_ports(lb: pd.Series, la: pd.Series, titre: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=la.index, y=la.values, name="Los Angeles", mode="lines",
                             line=dict(color=P["cyan"], width=2.2), hovertemplate="%{y:,.0f}<extra>LA</extra>"))
    fig.add_trace(go.Scatter(x=lb.index, y=lb.values, name="Long Beach", mode="lines",
                             line=dict(color=P["orange"], width=2.2), hovertemplate="%{y:,.0f}<extra>LB</extra>"))
    return _mise_en_forme(fig, 340, titre)


def cppi_pente(c: pd.DataFrame, titre: str) -> go.Figure:
    """Graphique en haltères : score CPPI 2024 (creux) → 2025 (plein) pour chaque port."""
    c = c.sort_values("cppi2025")
    fig = go.Figure()
    for port, ligne in c.iterrows():
        surligne = port in ("Long Beach", "Djibouti")
        couleur = P["orange"] if port == "Long Beach" else (P["cyan"] if port == "Djibouti" else "#4B6A82")
        fig.add_trace(go.Scatter(x=[ligne.cppi2024, ligne.cppi2025], y=[port, port], mode="lines",
                                 line=dict(color=couleur, width=4 if surligne else 2), hoverinfo="skip",
                                 showlegend=False))
    fig.add_trace(go.Scatter(x=c.cppi2024, y=c.index, mode="markers", name="Édition 2024",
                             marker=dict(size=10, color="rgba(0,0,0,0)", line=dict(color=P["muet"], width=2)),
                             hovertemplate="%{x:.1f}<extra>2024</extra>"))
    fig.add_trace(go.Scatter(x=c.cppi2025, y=c.index, mode="markers", name="Édition 2025",
                             marker=dict(size=13, color=[P["orange"] if p == "Long Beach" else
                                                         P["cyan"] if p == "Djibouti" else "#E2EEF7" for p in c.index],
                                         line=dict(color="#07131F", width=1)),
                             hovertemplate="%{x:.1f}<extra>2025</extra>"))
    fig.add_vline(x=0, line=dict(color=P["muet"], dash="dot", width=1))
    fig.update_layout(xaxis_title="score CPPI (0 = port médian)")
    return _mise_en_forme(fig, 360, titre)


def cnuced_temps(d: pd.DataFrame, titre: str) -> go.Figure:
    """Barres horizontales : temps médian au port par pays (États-Unis en orange)."""
    d = d.sort_values("temps_median_j")
    couleurs = [P["orange"] if p == "États-Unis" else P["bleu"] for p in d.pays]
    fig = go.Figure(go.Bar(x=d.temps_median_j, y=d.pays, orientation="h", marker=dict(color=couleurs),
                           text=[f"{v:.2f} j" for v in d.temps_median_j], textposition="outside",
                           textfont=dict(color=P["texte"]), hovertemplate="%{x:.2f} jours<extra></extra>"))
    fig.update_layout(xaxis_title="temps médian au port (jours)", bargap=0.35)
    return _mise_en_forme(fig, 320, titre)


def jauge(valeur: float, titre: str) -> go.Figure:
    """Jauge 0 à 100 : 50 = même niveau que l'an dernier."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=valeur, number=dict(font=dict(size=46, color="#FFFFFF"), suffix=""),
        gauge=dict(axis=dict(range=[0, 100], tickcolor=P["muet"]), bar=dict(color=P["cyan"], thickness=0.28),
                   bgcolor="rgba(0,0,0,0)", borderwidth=0,
                   steps=[dict(range=[0, 35], color="rgba(52,211,153,0.35)"),
                          dict(range=[35, 65], color="rgba(138,164,186,0.25)"),
                          dict(range=[65, 100], color="rgba(244,63,94,0.35)")])))
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=40, b=0), paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(family=POLICE, color=P["texte"]),
                      title=dict(text=titre, x=0.5, xanchor="center", font=dict(size=15, color=P["muet"])))
    return fig


def vent(h: pd.DataFrame, seuil_vigilance: float, seuil_arret: float) -> go.Figure:
    """Vent et rafales sur 72 h, avec les seuils de vigilance et d'arrêt des grues."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=h.heure, y=h.rafales, name="Rafales", mode="lines", line=dict(color=P["orange"], width=2),
                             fill="tozeroy", fillcolor="rgba(255,138,61,0.10)", hovertemplate="%{y:.0f} km/h<extra>rafales</extra>"))
    fig.add_trace(go.Scatter(x=h.heure, y=h.vent, name="Vent", mode="lines", line=dict(color=P["cyan"], width=2),
                             hovertemplate="%{y:.0f} km/h<extra>vent</extra>"))
    fig.add_hline(y=seuil_vigilance, line=dict(color=P["or"], dash="dash", width=1.5),
                  annotation_text="vigilance", annotation_font=dict(color=P["or"]))
    fig.add_hline(y=seuil_arret, line=dict(color=P["rouge"], dash="dash", width=1.5),
                  annotation_text="arrêt des grues", annotation_font=dict(color=P["rouge"]))
    fig.update_layout(yaxis_title="km/h")
    return _mise_en_forme(fig, 320, "Vent et rafales, 72 heures (heure locale)")


def vagues(h: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Scatter(x=h.heure, y=h.vagues, mode="lines", line=dict(color=P["bleu"], width=2),
                               fill="tozeroy", fillcolor="rgba(56,189,248,0.15)",
                               hovertemplate="%{y:.2f} m<extra>vagues</extra>"))
    fig.update_layout(yaxis_title="mètres")
    return _mise_en_forme(fig, 240, "Hauteur des vagues")


def cppi_serie(c: pd.DataFrame, titre: str) -> go.Figure:
    """Évolution du score CPPI de 2020 à 2025 pour chaque port (Long Beach et Djibouti mis en avant)."""
    annees = [f"cppi{a}" for a in range(2020, 2026)]
    fig = go.Figure()
    for port, ligne in c.iterrows():
        mis_en_avant = port in ("Long Beach", "Djibouti")
        couleur = P["orange"] if port == "Long Beach" else (P["cyan"] if port == "Djibouti" else "#4B6A82")
        fig.add_trace(go.Scatter(x=[int(a[-4:]) for a in annees], y=[float(ligne[a]) for a in annees], name=port,
                                 mode="lines+markers", line=dict(color=couleur, width=3.2 if mis_en_avant else 1.6),
                                 marker=dict(size=7 if mis_en_avant else 5, color=couleur),
                                 opacity=1 if mis_en_avant else 0.7))
    fig.update_layout(yaxis_title="score CPPI", xaxis=dict(dtick=1))
    return _mise_en_forme(fig, 380, titre)


def escales(d: pd.DataFrame, titre: str) -> go.Figure:
    """Nombre d'escales par pays et par année (hors Monde, qui écraserait les autres courbes)."""
    fig = go.Figure()
    for pays, g in d.groupby("pays"):
        g = g.sort_values("annee")
        fig.add_trace(go.Scatter(x=g.annee, y=g.escales, name=pays, mode="lines+markers",
                                 line=dict(width=2.4), marker=dict(size=7),
                                 hovertemplate="%{y:,.0f} escales<extra>" + pays + "</extra>"))
    fig.update_layout(yaxis_title="nombre d'escales", xaxis=dict(dtick=1))
    return _mise_en_forme(fig, 320, titre)


def comparaison_scenario(mois: list, reference: list, prevision_: list, scenario: list, titre: str) -> go.Figure:
    """Barres groupées : an dernier, prévision de base et scénario, pour les 3 prochains mois."""
    etiquettes = [pd.Timestamp(m).strftime("%b %Y") for m in mois]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=etiquettes, y=reference, name="Même mois l'an dernier", marker=dict(color="#4B6A82")))
    fig.add_trace(go.Bar(x=etiquettes, y=prevision_, name="Prévision de base", marker=dict(color=P["bleu"])))
    fig.add_trace(go.Bar(x=etiquettes, y=scenario, name="Scénario", marker=dict(color=P["orange"])))
    fig.update_layout(barmode="group", bargap=0.3, bargroupgap=0.08, yaxis_title="EVP")
    return _mise_en_forme(fig, 360, titre)


def score_tension(prevision_vs_n1_pct: float) -> float:
    """Indice maison 0 à 100 : 50 = même niveau qu'un an plus tôt ; ±30 % = bord de l'échelle."""
    return float(np.clip(50 + prevision_vs_n1_pct * (50 / 30), 0, 100))
