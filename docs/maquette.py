"""Maquette de la page Synthèse : python docs/maquette.py -> docs/maquette.png"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

W, H = 16, 10.6
fig = plt.figure(figsize=(W, H), dpi=110)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
G, B, O, V, R, VIO = "#868e96", "#1971c2", "#e8590c", "#2f9e44", "#e03131", "#7048e8"

def box(x, y, w, h, fc="white", ec="#dee2e6", lw=1.2, r=0.12):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw))

def t(x, y, s, size=9, c="#212529", w="normal", ha="left"):
    ax.text(x, y, s, fontsize=size, color=c, fontweight=w, ha=ha, va="center")

box(0.15, 0.15, W - 0.3, H - 0.3, fc="#ffffff", ec="#495057", lw=1.8)
box(0.3, 0.3, 2.6, H - 0.6, fc="#f1f3f5", ec="#f1f3f5")
for k, (ic, s) in enumerate([("📋", "Synthèse"), ("📦", "Volumes LA & LB"), ("🌍", "Comparaison mondiale"), ("📡", "Temps réel"), ("📚", "Sources & méthode")]):
    y = H - 0.9 - k * 0.5
    if k == 0: box(0.45, y - 0.2, 2.3, 0.4, fc="#dbe4ff", ec="#dbe4ff")
    t(0.6, y, s, 10, B if k == 0 else "#495057", "bold" if k == 0 else "normal")
t(0.55, H - 3.7, "Navigation par pages", 8.5, G)

X0 = 3.2
t(X0, H - 0.65, "Terminal de Long Beach : les jours et le mois qui viennent", 16, w="bold")
t(X0, H - 1.05, "Chef des opérations d'un terminal : dimensionner équipes et postes à quai ; se situer face à LA, Vancouver, Prince Rupert, Busan, Djibouti", 8.5, G)
t(X0, H - 1.5, "Historique et comparaison", 11.5, w="bold")
tw, th, gap = 2.98, 1.45, 0.13
row1 = [("EVP Long Beach – sept. 2026", "981 k", "↑ +25,5 % sur un an", V, "Réf. sept. 2025 : 782 k EVP"),
        ("Part de LB dans San Pedro Bay (12 mois)", "48,7 %", "↑ +3,6 pt vs 2019", V, "Réf. 2019 : 45,1 %"),
        ("Prévision Long Beach – oct. 2026", "1 011 k", "↑ +22,6 % vs N-1", V, "Réf. oct. 2025 ; marge 80 %"),
        ("Rang CPPI 2025 : LB | Djibouti", "305 | 53", "↑ LB +13 places", V, "Réf. Vancouver 375 · P. Rupert 322 · Busan 24")]
for i, (a, v, d, c, r) in enumerate(row1):
    x, y = X0 + i * (tw + gap), H - 3.15
    box(x, y, tw, th); t(x + 0.15, y + th - 0.25, a, 7.8, G); t(x + 0.15, y + th - 0.65, v, 16, w="bold")
    t(x + 0.15, y + th - 0.98, d, 8.5, c, "bold"); t(x + 0.15, y + 0.18, r + " · MàJ", 6.8, G)
t(X0, H - 3.5, "Temps réel et actions  (bloc rafraîchi toutes les minutes)", 11.5, w="bold")
row2 = [("Temps médian au port – É.-U. (2023)", "1,54 j", "↑ 23 h de plus que le Canada", R, "Réf. Canada : 0,57 j"),
        ("Navires en route ou au mouillage (AIS)", "n", "écart au seuil", G, "Réf. seuil : 15 navires"),
        ("Heures d'arrêt probable des grues (48 h)", "x h", "y h en vigilance", G, "Réf. rafales ≥ 72 km/h ; 50 km/h ou 2 m")]
tw2 = (4 * tw + 3 * gap - 2 * gap) / 3
for i, (a, v, d, c, r) in enumerate(row2):
    x, y = X0 + i * (tw2 + gap), H - 5.15
    box(x, y, tw2, th); t(x + 0.15, y + th - 0.25, a, 7.8, G); t(x + 0.15, y + th - 0.65, v, 16, w="bold")
    t(x + 0.15, y + th - 0.98, d, 8.5, c, "bold"); t(x + 0.15, y + 0.18, r + " · MàJ", 6.8, G)
t(X0, H - 5.5, "Recommandations", 10.5, w="bold")
for k, (c, s) in enumerate([(O, "Renforcer les équipes en oct. 2026 (+23 % de postes) — déclencheur : prévision 1 011 k EVP"),
                            (R, "Prévoir l'arrêt des portiques à partir du jj/mm à hh:mm — déclencheur : rafales ≥ 72 km/h"),
                            (O, "Ouvrir un poste à quai supplémentaire — déclencheur : navires au-dessus du seuil"),
                            (B, "Étudier les pratiques de Los Angeles et de Busan — déclencheur : scores CPPI 2025")]):
    yy = H - 5.85 - k * 0.33
    ax.plot(X0 + 0.1, yy, "o", color=c, ms=7); t(X0 + 0.3, yy, s, 8.3)
# vignettes des autres pages
t(X0, 2.85, "Autres pages", 11, w="bold")
vw, vh, y0 = 4.1, 2.3, 0.45
titres = ["Volumes : barres annuelles par flux ; prévision STL + ARIMA\n(marges 80/95 %) ; mois atypiques ◆", "Comparaison : CPPI : pente 2024 → 2025 par port ;\nCNUCED : temps médian et escales par pays",
          "Temps réel : carte pydeck des navires (couleur = statut) ;\nvent, rafales et seuils sur 72 h ; vagues"]
for i, ti in enumerate(titres):
    x = X0 + i * (vw + 0.17)
    box(x, y0, vw, vh); ax.text(x + 0.12, y0 + vh - 0.12, ti, fontsize=7.6, fontweight="bold", va="top")
    if i == 0:
        for k in range(7):
            hh = [0.45, 0.25, 0.3]; base = y0 + 0.2
            for j, c in enumerate([B, V, "#adb5bd"]):
                ax.add_patch(plt.Rectangle((x + 0.2 + k * 0.27, base), 0.2, hh[j] * (0.8 + 0.05 * k), color=c)); base += hh[j] * (0.8 + 0.05 * k)
        xs = np.linspace(x + 2.25, x + vw - 0.2, 20); ys = y0 + 0.9 + 0.25 * np.sin(np.linspace(0, 6, 20))
        ax.plot(xs[:15], ys[:15], color="#495057"); ax.fill_between(xs[14:], ys[14] - np.linspace(0, .4, 6), ys[14] + np.linspace(0, .4, 6), color=B, alpha=.3)
        ax.plot(xs[5], ys[5], "D", color=R, ms=6)
    if i == 1:
        for k, (a, b, c) in enumerate([(-.5, .3, B), (-.2, -.25, O), (-.55, .6, V), (.9, .95, VIO), (-.5, -.3, "#c2255c"), (-1.0, -.9, G)]):
            ax.plot([x + 0.5, x + 1.6], [y0 + 1.0 + a * 0.6, y0 + 1.0 + b * 0.6], color=c, marker="o", ms=4)
        for k in range(6):
            ax.add_patch(plt.Rectangle((x + 2.2, y0 + 0.3 + k * 0.25), 0.4 + 0.25 * k, 0.17, color=O if k == 5 else B))
    if i == 2:
        box(x + 0.15, y0 + 0.2, 2.0, 1.6, fc="#f8f9fa"); rng = np.random.default_rng(4)
        ax.scatter(x + 0.3 + rng.random(22) * 1.7, y0 + 0.35 + rng.random(22) * 1.3, s=14, c=rng.choice([O, B, V], 22))
        xs = np.linspace(x + 2.3, x + vw - 0.2, 30)
        ax.plot(xs, y0 + 1.0 + 0.3 * np.sin(np.linspace(0, 5, 30)), color=B); ax.plot([xs[0], xs[-1]], [y0 + 1.5] * 2, ls=":", color=O)
        ax.plot([xs[0], xs[-1]], [y0 + 1.7] * 2, ls=":", color=R); ax.fill_between(xs, y0 + 0.25, y0 + 0.45, color="#1098ad", alpha=.5)
fig.savefig("docs/maquette.png", dpi=110)
print("ok")
