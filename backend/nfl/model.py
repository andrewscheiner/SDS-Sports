"""XGBoost models for team Q1 and 1H points, with walk-forward backtest."""
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from .features import FEATURES

TARGETS = ["pts_q1", "pts_h1"]
PARAMS = dict(objective="count:poisson", n_estimators=300, max_depth=2, learning_rate=0.03, subsample=0.8,
              colsample_bytree=0.8, min_child_weight=10, reg_lambda=2.0, n_jobs=4)


def fit(train):
    models = {}
    for t in TARGETS:
        d = train[train[t].notna()]
        m = XGBRegressor(**PARAMS)
        m.fit(d[FEATURES], d[t])
        models[t] = m
    return models


def predict(models, df):
    out = df.copy()
    for t, m in models.items():
        out[f"pred_{t}"] = np.clip(m.predict(df[FEATURES]), 0, None)
    return out


def backtest(tg, test_seasons):
    """Train on all prior seasons, test each season. Returns metrics + paired game residuals."""
    preds = []
    for s in test_seasons:
        models = fit(tg[(tg["season"] < s) & tg["season"].ge(2018)])
        preds.append(predict(models, tg[(tg["season"] == s) & tg["pts_q1"].notna()]))
    p = pd.concat(preds)
    metrics = {}
    for t in TARGETS:
        share = (tg[t] / tg["implied_total"]).median()
        metrics[t] = {
            "mae": round(float((p[t] - p[f"pred_{t}"]).abs().mean()), 3),
            "baseline_mae": round(float((p[t] - p["implied_total"] * share).abs().mean()), 3),
            "n": int(len(p)),
        }
    home = p[p["is_home"] == 1].set_index("game_id")
    away = p[p["is_home"] == 0].set_index("game_id").reindex(home.index)
    residuals = {
        "q1": np.column_stack([home["pts_q1"] - home["pred_pts_q1"], away["pts_q1"] - away["pred_pts_q1"]]),
        "h1": np.column_stack([home["pts_h1"] - home["pred_pts_h1"], away["pts_h1"] - away["pred_pts_h1"]]),
    }
    residuals = {k: v[~np.isnan(v).any(axis=1)] for k, v in residuals.items()}
    return metrics, residuals


def importance(models):
    m = models["pts_h1"]
    imp = dict(zip(FEATURES, m.feature_importances_.tolist()))
    return sorted(imp.items(), key=lambda x: -x[1])
