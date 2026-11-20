# Tableau de bord portuaire – vu depuis un terminal de Long Beach

Application **Streamlit multipage** qui montre comment se porte le complexe de San Pedro Bay
(Port of Los Angeles + Port of Long Beach) et comment Long Beach se situe face aux autres ports, dont Djibouti.

- **Pour qui :** le chef des opérations d'un terminal à conteneurs du Port of Long Beach.
- **Pour quelle décision :** dimensionner les équipes (dockers, grutiers) et les postes à quai pour les jours et le mois
  qui viennent, et se comparer aux concurrents (Los Angeles, Vancouver, Prince Rupert), à Busan et à Djibouti.
- **Fiche de conception et maquette :** `docs/fiche_conception.md`, `docs/maquette.png`.

## Lancer

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # puis coller sa clé aisstream.io
streamlit run app.py
```

En ligne (Streamlit Community Cloud) : dépôt GitHub → *Create app* → fichier `app.py` → *Advanced settings → Secrets* :
`AISSTREAM_API_KEY = "…"`. **Aucune clé n'est dans le code** ; `.gitignore` exclut le fichier de secrets local.

## Organisation

| Fichier | Rôle |
|---|---|
| `app.py` | Déclare les 5 pages (`st.navigation`) |
| `views/synthese.py` | 7 tuiles (valeur, référence, tendance, date) et recommandations ; bloc temps réel rafraîchi chaque minute (`st.fragment`) |
| `views/volumes.py` | Composition annuelle des flux, série mensuelle, prévision à 3 mois, mois atypiques (Altair) |
| `views/benchmark.py` | CPPI 2024 → 2025 (graphique de pente), série 2020-2025 ; CNUCED par pays |
| `views/temps_reel.py` | Carte des navires (pydeck), vent, rafales, vagues et heures d'arrêt des grues |
| `views/sources.py` | Sources, méthode, limites |
| `lib/donnees.py` | Lecture et préparation des CSV de `data/raw/` (aucun appel réseau) |
| `lib/modeles.py` | Prévision STL + ARIMA, test, forêt d'isolement |
| `lib/direct.py` | Météo Open-Meteo avec relevé de secours ; récepteur AIS continu (asyncio + websockets) |
| `lib/regles.py` | Règles de recommandation |
| `lib/commun.py` | Récepteur AIS unique (`st.cache_resource`), météo en cache 1 h, tuiles, indicateurs |
| `collect/actualiser.py` | Retélécharge les sources historiques dans `data/raw/` (une fois par mois) |
| `data/sources.csv` | Adresse et date de récupération de chaque source |

## Sources (adresse et date de récupération)

| Donnée | Source | Adresse | Récupérée le |
|---|---|---|---|
| Volumes mensuels Los Angeles, janv. 2019 → oct. 2026 | Port of Los Angeles | https://www.portoflosangeles.org/business/statistics/container-statistics/historical-teu-statistics-2019 (… à 2026) | 19/11/2026 |
| Volumes mensuels Long Beach, janv. 2019 → sept. 2026 | BTS, d'après le Port of Long Beach | https://data.bts.gov/resource/y5ut-ibwt.json | 19/11/2026 |
| Correction Long Beach juillet 2020 | Port of Long Beach, repris par S&P Global | https://www.spglobal.com/commodity-insights/en/news-research/latest-news/shipping/081720-port-of-long-beach-handles-record-container-volume-in-july-as-rates-escalate | 19/11/2026 |
| CPPI 2024 et 2025 : LA, LB, Djibouti, Busan, Vancouver, Prince Rupert | Banque mondiale & S&P Global | https://www.worldbank.org/en/topic/transport/publication/cppi (annexes Excel 2020-2024 et 2020-2025) | 19/11/2026 |
| Temps médian au port | CNUCED, UNCTADstat US.PortCalls | https://unctadstat-api.unctad.org/bulkdownload/US.PortCalls/US_PortCalls | 19/11/2026 |
| Nombre d'escales : Monde, États-Unis, Canada, Australie, France, Royaume-Uni | CNUCED, UNCTADstat US.PortCallsArrivals | https://unctadstat-api.unctad.org/datamart-api/US.PortCallsArrivals/10002/Facts | 19/11/2026 |
| Navires en direct | aisstream.io | wss://stream.aisstream.io/v0/stream | en continu |
| Vent, rafales, vagues | Open-Meteo | https://api.open-meteo.com/v1/forecast · https://marine-api.open-meteo.com/v1/marine | à l'affichage (cache 1 h) |

## Traitements

- **Total comparable** = imports pleins + exports pleins + vides à l'export (le BTS ne publie pas les vides à l'import de Long Beach).
- Long Beach, juillet 2020 : le BTS répète la valeur de juin ; remplacée par celle du communiqué du port (376 807 EVP).
- **Part de Long Beach** = total LB ÷ (total LA + total LB) sur les 12 derniers mois communs.

## Méthode

- **Prévision avec marge d'incertitude :** décomposition STL de log(EVP) (saisonnalité de 12 mois, lissage 13),
  ARIMA(1,1,0) sur la partie sans saisonnalité, puis saisonnalité remise. Horizon 3 mois, marges à 80 % et 95 %.
  **Test** sur les 12 derniers mois connus de Long Beach (oct. 2025 → sept. 2026) : erreur moyenne **7,4 %**,
  contre **9,4 %** pour « même mois l'an dernier ».
- **Mois atypiques :** forêt d'isolement (scikit-learn, 500 arbres, graine fixe) sur deux variables, la variation sur
  un an et la variation sur un mois ; on retient les 5 % de mois les plus faciles à isoler.
  Long Beach : mars 2021, juin 2023, mai 2025, juillet 2025.
- **Alerte météo :** nombre d'heures, sur les 48 prochaines, où les rafales atteignent 72 km/h (arrêt probable des
  portiques) ou 50 km/h ou 2 m de vagues (vigilance).
- **Recommandations :** 4 règles dans `lib/regles.py` (équipes du mois prochain, arrêt des grues, poste à quai
  supplémentaire, comparaison CPPI), chacune avec son déclencheur.

## Ne pas rappeler les API à chaque actualisation

- Historique : lu dans `data/raw/` ; mise à jour manuelle avec `collect/actualiser.py`.
- Météo : `st.cache_data(ttl=3600)` → au plus un appel par heure et par zone.
- AIS : un seul récepteur pour toute l'application (`st.cache_resource`) écoute en continu ; un navire reste affiché
  20 min après son dernier message ; le bloc temps réel relit ce registre chaque minute (`st.fragment(run_every="60s")`).
- Source indisponible : dernier relevé sauvegardé dans `data/cache/` affiché avec sa date, ou message clair.

## Limites

- Long Beach : BTS (polb.com inaccessible depuis Djibouti), jusqu'à sept. 2026, sans vides à l'import.
- CNUCED : 22 économies en accès libre, 2018-2023 ; **Djibouti absent** (comparaison par le CPPI).
- CPPI et CNUCED ne mesurent pas la même chose : jamais sur le même axe.
- AIS gratuit : couverture faible à Djibouti ; « en route » compte aussi les navires qui partent.
- Seuils (15 navires, 50 / 72 km/h, 2 m) : hypothèses de travail à valider avec le terminal.
- La prévision prolonge le passé et ne connaît pas les chocs à venir.

## Utilisation de l'IA

Le code a été écrit avec l'aide d'une IA ; chaque module est commenté pour pouvoir être expliqué.
