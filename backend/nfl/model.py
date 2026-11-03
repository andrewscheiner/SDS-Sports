"""XGBoost models for team Q1 and 1H points, with walk-forward backtest.

- Two regressors: one predicts a team's Q1 points, one its 1H points (each row = one team in one game).
- Objective count:poisson because points are non-negative counts with a right skew; in a quick
  comparison it matched or beat squared-error/absolute-error.
- Shallow trees (depth 2) + low learning rate + subsampling = strong regularization; football
  scoring is very noisy and deeper trees overfit.
- Final projection = 50% XGBoost + 50% Vegas-implied share. In backtests the raw model alone was
  not better than the market, so shrinking toward the market keeps edges realistic.
"""
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from .features import FEATURES

TARGETS = ["pts_q1", "pts_h1"]
PARAMS = dict(objective="count:poisson", n_estimators=300, max_depth=2, learning_rate=0.03, subsample=0.8,
              colsample_bytree=0.8, min_child_weight=10, reg_lambda=2.0, n_jobs=4)


MARKET_WEIGHT = 0.5  # shrink XGBoost projection toward the Vegas-implied share


def fit(train):
    models = {}
    for t in TARGETS:
        d = train[train[t].notna()]
        m = XGBRegressor(**PARAMS)
        m.fit(d[FEATURES], d[t])
        # Typical fraction of the Vegas team total scored in this period (Q1 ~0.2, 1H ~0.5).
        m.share_ = float((d[t] / d["implied_total"]).median())
        models[t] = m
    return models


def predict(models, df):
    out = df.copy()
    for t, m in models.items():
        raw = np.clip(m.predict(df[FEATURES]), 0, None)
        market = (df["implied_total"] * m.share_).fillna(pd.Series(raw, index=df.index)).to_numpy()
        out[f"pred_{t}"] = (1 - MARKET_WEIGHT) * raw + MARKET_WEIGHT * market
    return out


def backtest(tg, test_seasons):
    """Train on all prior seasons, test each season. Returns metrics + paired game residuals."""
    # e.g. test 2023 with a model trained on 2018-22, 2024 on 2018-23, 2025 on 2018-24.
    # baseline_mae = just using implied_total * share, the bar the model has to beat.
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
    # Residual = actual - predicted, kept as (home, away) PAIRS from the same game so the
    # correlation between both teams' errors is preserved; edges.py simulates with them.
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
