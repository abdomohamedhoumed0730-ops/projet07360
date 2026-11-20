"""
Fonctions « intelligentes » :
  - prévision avec marge d'incertitude : décomposition STL + ARIMA (STLForecast de statsmodels)
  - test de cette prévision sur les 12 derniers mois
  - détection d'anomalies : forêt d'isolement (Isolation Forest, scikit-learn)
"""
import warnings

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.ensemble import IsolationForest
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.forecasting.stl import STLForecast


def _ajuster(y: pd.Series):
    """1) STL sépare log(y) en saisonnalité + reste ; 2) un ARIMA(1,1,0) prévoit le reste ;
    3) la saisonnalité est ajoutée de nouveau à la prévision. seasonal=13 : saisonnalité qui évolue lentement."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return STLForecast(np.log(y), ARIMA, model_kwargs={"order": (1, 1, 0)},
                           period=12, seasonal=13, robust=True).fit()


@st.cache_data
def prevoir(y: pd.Series, horizon: int = 3) -> pd.DataFrame:
    y = y.dropna().asfreq("MS")
    p = _ajuster(y).get_prediction(start=len(y), end=len(y) + horizon - 1)
    out = pd.DataFrame({"mois": pd.date_range(y.index[-1] + pd.offsets.MonthBegin(), periods=horizon, freq="MS"),
                        "prevision": np.exp(np.asarray(p.predicted_mean))})
    for niveau in (80, 95):
        ci = np.exp(np.asarray(p.conf_int(alpha=1 - niveau / 100)))
        out[f"bas{niveau}"], out[f"haut{niveau}"] = ci[:, 0], ci[:, 1]
    return out


@st.cache_data
def tester(y: pd.Series, h: int = 12) -> dict:
    """Réentraîne sans les h derniers mois et compare : modèle contre « même mois l'an dernier »."""
    y = y.dropna().asfreq("MS")
    p = prevoir(y[:-h], h)
    reel = y[-h:].values
    return {"debut": y.index[-h], "fin": y.index[-1],
            "erreur_modele": float(np.mean(np.abs(reel - p.prevision.values) / reel) * 100),
            "erreur_naive": float(np.mean(np.abs(reel - y[-h - 12:-12].values) / reel) * 100),
            "dans_marge80": int(((reel >= p.bas80.values) & (reel <= p.haut80.values)).sum()), "h": h}


@st.cache_data
def anomalies(y: pd.Series, part: float = 0.05) -> pd.DataFrame:
    """Forêt d'isolement sur deux variables : variation sur un an et variation sur un mois (en log).
    L'algorithme isole les points par des coupes au hasard ; un mois qui s'isole en peu de coupes est atypique.
    On garde les 5 % de mois les plus atypiques (part=0.05). random_state fixe = résultat reproductible."""
    y = y.dropna().asfreq("MS")
    X = pd.DataFrame({"var_an": np.log(y).diff(12), "var_mois": np.log(y).diff(1)}).dropna()
    modele = IsolationForest(n_estimators=500, contamination=part, random_state=42).fit(X)
    X["atypique"] = modele.predict(X) == -1
    X["valeur"] = y.reindex(X.index)
    return X
