"""Sportsbook odds: The Odds API (live) or deterministic SAMPLE odds when no real key is set."""
import os
import zlib
from datetime import datetime, timezone
import numpy as np
import requests
from scipy.stats import norm

BOOKS = {"draftkings": "DraftKings", "fanduel": "FanDuel", "betmgm": "BetMGM", "espnbet": "ESPN BET"}
API_MARKETS = {"h2h_q1": "q1_ml", "spreads_q1": "q1_spread", "totals_q1": "q1_total",
               "h2h_h1": "h1_ml", "spreads_h1": "h1_spread", "totals_h1": "h1_total"}
BASE = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl"
SAMPLE_KEY = "sample_odds_api_key_replace_me"


def api_key():
    k = os.environ.get("ODDS_API_KEY", "")
    return None if not k or k == SAMPLE_KEY else k


def bookmakers():
    return os.environ.get("ODDS_BOOKMAKERS", ",".join(BOOKS)).split(",")


def _half(x):
    return round(x * 2) / 2


def _american(p):
    p = min(max(p, 0.03), 0.97)
    return int(round(-100 * p / (1 - p))) if p >= 0.5 else int(round(100 * (1 - p) / p))


def sample_books(game):
    """Plausible Q1/1H lines derived from the full-game Vegas line, varied per book."""
    margin = game.get("spread_line") or 0.0
    total = game.get("total_line") or 44.0
    out = []
    for key in bookmakers():
        rng = np.random.default_rng(zlib.crc32(f"{game['game_id']}{key}".encode()))
        mk = {}
        for per, ms, ts, sd in [("q1", 0.18, 0.19, 7.5), ("h1", 0.55, 0.49, 10.5)]:
            m = margin * ms + rng.normal(0, 0.25)
            sp = _half(m) or 0.5
            tp = _half(total * ts + rng.choice([-0.5, 0, 0, 0.5]))
            if tp == int(tp) and per == "q1":
                tp += 0.5
            ph = norm.cdf(m / sd)
            vig = 1.045 + rng.uniform(-0.01, 0.01)
            k = int(rng.choice([-10, -5, 0, 0, 5, 10]))
            j = int(rng.choice([-10, -5, 0, 0, 5]))
            mk[f"{per}_ml"] = {"home": _american(ph * vig), "away": _american((1 - ph) * vig)}
            mk[f"{per}_spread"] = {"home_point": -sp, "home_price": -110 + k,
                                   "away_point": sp, "away_price": -110 - k}
            mk[f"{per}_total"] = {"point": tp, "over": -110 + j, "under": -110 - j}
        out.append({"book": key, "title": BOOKS.get(key, key), "markets": mk})
    return out


def _parse_book(bm, home_name):
    mk = {}
    for m in bm.get("markets", []):
        key = API_MARKETS.get(m["key"])
        if not key:
            continue
        o = {x["name"]: x for x in m["outcomes"]}
        if key.endswith("_ml"):
            away = next((x for n, x in o.items() if n not in (home_name, "Draw")), None)
            mk[key] = {"home": o.get(home_name, {}).get("price"), "away": away and away["price"],
                       "draw": o.get("Draw", {}).get("price")}
        elif key.endswith("_spread"):
            h = o.get(home_name)
            a = next((x for n, x in o.items() if n != home_name), None)
            if h and a:
                mk[key] = {"home_point": h.get("point"), "home_price": h["price"],
                           "away_point": a.get("point"), "away_price": a["price"]}
        elif "Over" in o and "Under" in o:
            mk[key] = {"point": o["Over"].get("point"), "over": o["Over"]["price"], "under": o["Under"]["price"]}
    return {"book": bm["key"], "title": BOOKS.get(bm["key"], bm["title"]), "markets": mk}


def live_books(games, names):
    """Fetch Q1/1H odds for the given games. Returns ({game_id: books}, quota)."""
    key = api_key()
    r = requests.get(f"{BASE}/events", params={"apiKey": key}, timeout=20)
    r.raise_for_status()
    events = {(e["home_team"], e["away_team"]): e["id"] for e in r.json()}
    result, quota = {}, {}
    for g in games:
        home_name = names.get(g["home_team"])
        eid = events.get((home_name, names.get(g["away_team"])))
        if not eid:
            continue
        r = requests.get(f"{BASE}/events/{eid}/odds", timeout=20, params={
            "apiKey": key, "bookmakers": ",".join(bookmakers()), "markets": ",".join(API_MARKETS),
            "oddsFormat": "american"})
        if r.status_code != 200:
            continue
        quota = {k: v for k, v in r.headers.items() if k.lower().startswith("x-requests")}
        result[g["game_id"]] = [_parse_book(b, home_name) for b in r.json().get("bookmakers", [])]
    return result, quota


def odds_docs(games, names, live=False):
    now = datetime.now(timezone.utc).isoformat()
    fetched, quota = (live_books(games, names) if live and api_key() else ({}, {}))
    docs = []
    for g in games:
        if g["game_id"] in fetched and fetched[g["game_id"]]:
            docs.append({"game_id": g["game_id"], "source": "live", "books": fetched[g["game_id"]], "fetched_at": now})
        else:
            docs.append({"game_id": g["game_id"], "source": "sample", "books": sample_books(g), "fetched_at": now})
    return docs, quota
