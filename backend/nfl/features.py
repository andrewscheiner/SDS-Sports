"""Feature engineering: nflreadpy play-by-play -> one row per team per game."""
from pathlib import Path
import numpy as np
import pandas as pd
import nflreadpy as nfl

DATA_DIR = Path(__file__).parent / "data"
PBP_COLS = [
    "game_id", "play_id", "season", "week", "posteam", "defteam", "qtr", "play_type",
    "epa", "success", "pass", "rush", "interception", "fumble_lost", "yards_gained",
    "wp", "total_home_score", "total_away_score",
]
OFF_STATS = ["plays", "epa", "success", "pass_rate_neutral", "explosive", "turnovers",
             "q1_plays", "h1_plays", "epa_q1", "epa_h1", "succ_q1"]
DEF_STATS = ["plays", "epa", "success", "explosive", "epa_q1", "epa_h1"]
PTS = ["pts_q1", "pts_h1", "pts_q1_allowed", "pts_h1_allowed"]


def load_pbp(seasons, current_season):
    frames = []
    for s in seasons:
        f = DATA_DIR / f"pbp_{s}.parquet"
        if s != current_season and f.exists():
            frames.append(pd.read_parquet(f))
            continue
        df = nfl.load_pbp([s]).select(PBP_COLS).to_pandas()
        if s != current_season:
            DATA_DIR.mkdir(exist_ok=True)
            df.to_parquet(f)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def load_schedule(seasons):
    return nfl.load_schedules(seasons).to_pandas()


def team_names():
    t = nfl.load_teams().to_pandas()
    return dict(zip(t["team_abbr"], t["team_name"]))


def _play_stats(pbp):
    p = pbp[pbp["play_type"].isin(["pass", "run"]) & pbp["posteam"].notna() & pbp["epa"].notna()].copy()
    q1, h1 = p["qtr"] == 1, p["qtr"] <= 2
    neutral = p["wp"].between(0.2, 0.8) & (p["qtr"] <= 3)
    p["q1"], p["h1"] = q1.astype(int), h1.astype(int)
    p["explosive"] = (((p["pass"] == 1) & (p["yards_gained"] >= 20)) | ((p["rush"] == 1) & (p["yards_gained"] >= 10))).astype(int)
    p["to"] = p["interception"].fillna(0) + p["fumble_lost"].fillna(0)
    p["epa_q1"], p["epa_h1"] = p["epa"].where(q1), p["epa"].where(h1)
    p["succ_q1"] = p["success"].where(q1)
    p["pass_neutral"] = p["pass"].where(neutral)
    off = p.groupby(["game_id", "posteam"]).agg(
        plays=("epa", "size"), epa=("epa", "mean"), success=("success", "mean"),
        pass_rate_neutral=("pass_neutral", "mean"), explosive=("explosive", "mean"),
        turnovers=("to", "sum"), q1_plays=("q1", "sum"), h1_plays=("h1", "sum"),
        epa_q1=("epa_q1", "mean"), epa_h1=("epa_h1", "mean"), succ_q1=("succ_q1", "mean"),
    ).reset_index().rename(columns={"posteam": "team"})
    dfn = p.groupby(["game_id", "defteam"]).agg(
        plays=("epa", "size"), epa=("epa", "mean"), success=("success", "mean"),
        explosive=("explosive", "mean"), epa_q1=("epa_q1", "mean"), epa_h1=("epa_h1", "mean"),
    ).reset_index().rename(columns={"defteam": "team"})
    off.columns = ["game_id", "team"] + [f"off_{c}" for c in OFF_STATS]
    dfn.columns = ["game_id", "team"] + [f"def_{c}" for c in DEF_STATS]
    return off.merge(dfn, on=["game_id", "team"], how="outer")


def game_scores(pbp):
    s = pbp.dropna(subset=["total_home_score"]).sort_values(["game_id", "play_id"])
    cols = ["total_home_score", "total_away_score"]
    q1 = s[s["qtr"] == 1].groupby("game_id")[cols].last()
    h1 = s[s["qtr"] <= 2].groupby("game_id")[cols].last()
    out = pd.DataFrame({"home_q1": q1[cols[0]], "away_q1": q1[cols[1]],
                        "home_h1": h1[cols[0]], "away_h1": h1[cols[1]]})
    return out.reset_index()


def build_team_games(pbp, sched):
    """Long table: 2 rows per game with pre-game rolling features + targets."""
    sched = sched[sched["game_type"].isin(["REG", "WC", "DIV", "CON", "SB"])].copy()
    sched = sched.merge(game_scores(pbp), on="game_id", how="left")
    base = ["game_id", "season", "week", "gameday", "gametime", "spread_line", "total_line",
            "div_game", "roof", "temp", "wind"]
    rows = []
    for side, other in [("home", "away"), ("away", "home")]:
        d = sched[base].copy()
        d["team"], d["opp"] = sched[f"{side}_team"], sched[f"{other}_team"]
        d["is_home"] = int(side == "home")
        d["rest"] = sched[f"{side}_rest"]
        d["team_line"] = sched["spread_line"] if side == "home" else -sched["spread_line"]
        d["pts_q1"], d["pts_h1"] = sched[f"{side}_q1"], sched[f"{side}_h1"]
        d["pts_q1_allowed"], d["pts_h1_allowed"] = sched[f"{other}_q1"], sched[f"{other}_h1"]
        rows.append(d)
    tg = pd.concat(rows, ignore_index=True).merge(_play_stats(pbp), on=["game_id", "team"], how="left")
    tg["dome"] = tg["roof"].isin(["dome", "closed"]).astype(int)
    tg["implied_total"] = tg["total_line"] / 2 + tg["team_line"] / 2
    tg = tg.sort_values(["team", "gameday", "game_id"]).reset_index(drop=True)

    stat_cols = [f"off_{c}" for c in OFF_STATS] + [f"def_{c}" for c in DEF_STATS] + PTS
    rolled = tg.groupby("team")[stat_cols].transform(
        lambda x: x.shift(1).ewm(halflife=5, ignore_na=True).mean())
    rolled.columns = [f"r_{c}" for c in stat_cols]
    tg = pd.concat([tg, rolled], axis=1)

    opp_cols = ["r_def_epa", "r_def_success", "r_def_explosive", "r_def_epa_q1", "r_def_epa_h1",
                "r_pts_q1_allowed", "r_pts_h1_allowed", "r_off_plays", "r_off_epa"]
    opp = tg[["game_id", "team"] + opp_cols].rename(
        columns={"team": "opp", **{c: "o_" + c[2:] for c in opp_cols}})
    return tg.merge(opp, on=["game_id", "opp"], how="left")


FEATURES = [
    "r_off_epa", "r_off_success", "r_off_plays", "r_off_q1_plays", "r_off_h1_plays",
    "r_off_epa_q1", "r_off_epa_h1", "r_off_succ_q1", "r_off_pass_rate_neutral",
    "r_off_explosive", "r_off_turnovers", "r_pts_q1", "r_pts_h1", "r_def_epa",
    "o_def_epa", "o_def_success", "o_def_explosive", "o_def_epa_q1", "o_def_epa_h1",
    "o_pts_q1_allowed", "o_pts_h1_allowed", "o_off_plays", "o_off_epa",
    "is_home", "team_line", "total_line", "implied_total", "rest", "dome", "temp", "wind", "div_game",
]

FEATURE_LABELS = {
    "r_off_epa": "Offense EPA/play", "r_off_success": "Offense success rate",
    "r_off_plays": "Plays run per game", "r_off_q1_plays": "Q1 plays run",
    "r_off_h1_plays": "1H plays run", "r_off_epa_q1": "Q1 offense EPA/play",
    "r_off_epa_h1": "1H offense EPA/play", "r_off_succ_q1": "Q1 success rate",
    "r_off_pass_rate_neutral": "Neutral pass rate", "r_off_explosive": "Explosive play rate",
    "r_off_turnovers": "Turnovers", "r_pts_q1": "Q1 points (rolling)", "r_pts_h1": "1H points (rolling)",
    "r_def_epa": "Own defense EPA allowed", "o_def_epa": "Opp defense EPA allowed",
    "o_def_success": "Opp defense success allowed", "o_def_explosive": "Opp explosive allowed",
    "o_def_epa_q1": "Opp Q1 EPA allowed", "o_def_epa_h1": "Opp 1H EPA allowed",
    "o_pts_q1_allowed": "Opp Q1 pts allowed", "o_pts_h1_allowed": "Opp 1H pts allowed",
    "o_off_plays": "Opp pace (plays)", "o_off_epa": "Opp offense EPA/play",
    "is_home": "Home field", "team_line": "Vegas spread", "total_line": "Vegas total",
    "implied_total": "Vegas implied team total", "rest": "Rest days", "dome": "Dome",
    "temp": "Temperature", "wind": "Wind", "div_game": "Division game",
}


def current_week(sched, season):
    s = sched[(sched["season"] == season) & (sched["game_type"] == "REG")]
    pending = s[s["home_score"].isna()]
    return int(pending["week"].min()) if len(pending) else int(s["week"].max())


def nan_to_none(v):
    return None if v is None or (isinstance(v, float) and np.isnan(v)) else v
