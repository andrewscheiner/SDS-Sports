"""End-to-end: load data -> features -> train/backtest -> walk-forward predictions -> MongoDB.

Run:  cd /app/backend && python -m nfl.pipeline [--season 2026] [--week 8]
"""
import argparse
import os
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient
from .features import (load_pbp, load_schedule, build_team_games, current_week, team_names,
                       FEATURE_LABELS, nan_to_none)
from .model import fit, predict, backtest, importance
from .odds import odds_docs

load_dotenv(Path(__file__).parent.parent / ".env")
TRAIN_START = 2018


def get_db():
    return MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]


def _f(v, nd=2):
    v = nan_to_none(v)
    return None if v is None else round(float(v), nd)


def game_docs(pred, sched):
    docs = []
    for gid, g in pred.groupby("game_id"):
        h, a = g[g["is_home"] == 1].iloc[0], g[g["is_home"] == 0].iloc[0]
        s = sched[sched["game_id"] == gid].iloc[0]
        played = nan_to_none(h["pts_q1"]) is not None
        docs.append({
            "game_id": gid, "season": int(h["season"]), "week": int(h["week"]),
            "gameday": h["gameday"], "gametime": h["gametime"],
            "home_team": h["team"], "away_team": a["team"],
            "spread_line": _f(s["spread_line"]), "total_line": _f(s["total_line"]),
            "home_moneyline": _f(s["home_moneyline"], 0), "away_moneyline": _f(s["away_moneyline"], 0),
            "roof": nan_to_none(s["roof"]), "home_qb": nan_to_none(s["home_qb_name"]), "away_qb": nan_to_none(s["away_qb_name"]),
            "pred": {"q1": [_f(h["pred_pts_q1"]), _f(a["pred_pts_q1"])],
                     "h1": [_f(h["pred_pts_h1"]), _f(a["pred_pts_h1"])]},
            "actual": {"q1": [int(h["pts_q1"]), int(a["pts_q1"])],
                       "h1": [int(h["pts_h1"]), int(a["pts_h1"])]} if played else None,
            "inputs": {t: {"epa": _f(r["r_off_epa"], 3), "plays": _f(r["r_off_plays"], 1),
                           "q1_plays": _f(r["r_off_q1_plays"], 1), "def_epa": _f(r["r_def_epa"], 3)}
                       for t, r in ((h["team"], h), (a["team"], a))},
        })
    return docs


def run(season=None, week=None, log=print):
    db = get_db()
    sched = load_schedule(list(range(TRAIN_START, 2027)))
    season = season or int(sched[sched["home_score"].isna()]["season"].min() if sched["home_score"].isna().any() else sched["season"].max())
    week = week or current_week(sched, season)
    log(f"Loading play-by-play {TRAIN_START}-{season}")
    pbp = load_pbp(list(range(TRAIN_START, season + 1)), season)
    tg = build_team_games(pbp, sched[sched["season"] <= season])
    log("Backtesting")
    metrics, residuals = backtest(tg, [season - 3, season - 2, season - 1])

    log(f"Walk-forward predictions {season} weeks 1-{week}")
    preds = []
    for w in range(1, week + 1):
        train = tg[(tg["season"] < season) | ((tg["season"] == season) & (tg["week"] < w))]
        models = fit(train)
        preds.append(predict(models, tg[(tg["season"] == season) & (tg["week"] == w)]))
    docs = game_docs(pd.concat(preds), sched)
    now = datetime.now(timezone.utc).isoformat()
    for d in docs:
        d["updated_at"] = now
        db.nfl_games.replace_one({"game_id": d["game_id"]}, d, upsert=True)

    names = team_names()
    for w in range(1, week + 1):
        wk = [d for d in docs if d["week"] == w]
        odocs, _ = odds_docs([{**d} for d in wk], names, live=(w == week))
        for o in odocs:
            db.nfl_odds.replace_one({"game_id": o["game_id"]}, o, upsert=True)

    db.nfl_meta.replace_one({"_id": "model"}, {
        "_id": "model", "season": season, "current_week": week, "train_start": TRAIN_START,
        "trained_at": now, "metrics": metrics,
        "residuals": {k: v.tolist() for k, v in residuals.items()},
        "importance": [{"feature": f, "label": FEATURE_LABELS.get(f, f), "value": round(v, 4)}
                       for f, v in importance(models)[:12]],
        "n_train_rows": int(tg["pts_q1"].notna().sum()),
        "backtest_seasons": [season - 3, season - 2, season - 1],
    }, upsert=True)
    db.nfl_games.create_index([("season", 1), ("week", 1)])
    log(f"Done: {len(docs)} games written")
    return {"season": season, "week": week, "games": len(docs), "metrics": metrics}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int)
    ap.add_argument("--week", type=int)
    a = ap.parse_args()
    print(run(a.season, a.week))
