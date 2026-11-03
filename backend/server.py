from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, Request
from pymongo.errors import DuplicateKeyError
import hmac
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from nfl.edges import game_edges, fair_lines, american_to_decimal, MARKET_LABELS  # noqa: E402
from nfl import odds as odds_mod  # noqa: E402
from nfl.pipeline import run as run_pipeline  # noqa: E402
from nfl.features import team_names  # noqa: E402

client = AsyncIOMotorClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]
app = FastAPI()
api = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)
JOB = {"status": "idle", "message": "", "finished_at": None}


async def get_meta():
    meta = await db.nfl_meta.find_one({"_id": "model"})
    if not meta:
        raise HTTPException(503, "Model not trained yet. POST /api/nfl/pipeline/run")
    return meta


@api.get("/")
async def root():
    return {"message": "SDS Sports API"}


@api.get("/nfl/meta")
async def nfl_meta():
    m = await get_meta()
    weeks = sorted(await db.nfl_games.distinct("week", {"season": m["season"]}))
    sources = await db.nfl_odds.distinct("source")
    return {
        "season": m["season"], "current_week": m["current_week"], "weeks": weeks,
        "train_start": m["train_start"], "trained_at": m["trained_at"], "metrics": m["metrics"],
        "importance": m["importance"], "n_train_rows": m["n_train_rows"],
        "backtest_seasons": m["backtest_seasons"], "odds_sources": sources,
        "odds_key_configured": odds_mod.api_key() is not None,
        "books": [{"key": k, "title": odds_mod.BOOKS.get(k, k)} for k in odds_mod.bookmakers()],
    }


def _profit(e):
    return (american_to_decimal(e["price"]) - 1) if e["result"] == "win" else -1 if e["result"] == "loss" else 0


def _summary(plays):
    rec = {r: sum(e["result"] == r for e in plays) for r in ("win", "loss", "push")}
    rec["units"] = round(sum(_profit(e) for e in plays), 2)
    rec["roi"] = round(rec["units"] / len(plays), 4) if plays else 0
    return rec


async def build_week(season, week, meta):
    games = await db.nfl_games.find({"season": season, "week": week}, {"_id": 0}).sort(
        [("gameday", 1), ("gametime", 1)]).to_list(32)
    odds = {o["game_id"]: o async for o in db.nfl_odds.find(
        {"game_id": {"$in": [g["game_id"] for g in games]}}, {"_id": 0})}
    res = meta["residuals"]
    all_edges = []
    for g in games:
        o = odds.get(g["game_id"], {"books": [], "source": "none"})
        pred = {p: tuple(g["pred"][p]) for p in ("q1", "h1")}
        g["fair"] = {p: fair_lines(*pred[p], res[p]) for p in ("q1", "h1")}
        g["odds_source"], g["odds_fetched_at"], g["books"] = o["source"], o.get("fetched_at"), o["books"]
        edges = game_edges(pred, o["books"], res, g["actual"])
        for e in edges:
            e.update(game_id=g["game_id"], week=week, odds_source=o["source"],
                     matchup=f"{g['away_team']} @ {g['home_team']}",
                     team=g["home_team"] if e["side"] == "home" else g["away_team"] if e["side"] == "away" else None)
        g["edges"] = edges
        g["best_edge"] = max(edges, key=lambda e: e["ev"]) if edges else None
        all_edges += edges
    # One play per game/market/side: the book with the best EV (line shopping).
    best = {}
    for e in sorted(all_edges, key=lambda e: -e["ev"]):
        best.setdefault((e["game_id"], e["market"], e["side"]), e)
    return games, list(best.values())


@api.get("/nfl/week")
async def nfl_week(season: int, week: int):
    m = await get_meta()
    games, best = await build_week(season, week, m)
    top = sorted([e for p in ("q1", "h1") for e in [x for x in best
                  if x["ev"] > 0 and x["market"].startswith(p)][:10]], key=lambda e: -e["ev"])
    record = _summary([e for e in best if e["ev"] >= 0.04 and e["result"]])
    return {"season": season, "week": week, "games": games, "top_edges": top, "record": record}


@api.get("/nfl/season")
async def nfl_season(season: int, min_ev: float = 0.04):
    """Season tracker: plays are graded at the stored closing line (odds are frozen at kickoff)."""
    m = await get_meta()
    weeks = sorted(await db.nfl_games.distinct("week", {"season": season}))
    plays, by_week, cum = [], [], 0.0
    for w in weeks:
        _, best = await build_week(season, w, m)
        wp = [e for e in best if e["ev"] >= min_ev and e["result"]]
        if not wp:
            continue
        s = _summary(wp)
        cum += s["units"]
        by_week.append({"week": w, **s, "cum_units": round(cum, 2)})
        plays += wp
    by_market = [{"market": k, "label": MARKET_LABELS[k], **_summary([e for e in plays if e["market"] == k])}
                 for k in MARKET_LABELS if any(e["market"] == k for e in plays)]
    sources = sorted({e["odds_source"] for e in plays})
    return {"season": season, "min_ev": min_ev, "total": _summary(plays), "by_week": by_week,
            "by_market": by_market, "odds_sources": sources, "n_plays": len(plays)}


@api.post("/nfl/odds/refresh")
async def refresh_odds(season: int, week: int):
    games = await db.nfl_games.find({"season": season, "week": week},
                                    {"_id": 0, "game_id": 1, "home_team": 1, "away_team": 1,
                                     "spread_line": 1, "total_line": 1, "gameday": 1, "gametime": 1}).to_list(32)
    # Never overwrite odds after kickoff: the stored line becomes the closing line used for grading.
    games = [g for g in games if not odds_mod.kicked_off(g)]
    try:
        docs, quota = odds_mod.odds_docs(games, team_names(), live=True)
    except Exception as e:
        logger.exception("odds refresh failed")
        raise HTTPException(502, f"Odds provider error: {e}")
    for d in docs:
        await db.nfl_odds.replace_one({"game_id": d["game_id"]}, d, upsert=True)
    return {"updated": len(docs), "live": sum(d["source"] == "live" for d in docs), "quota": quota,
            "key_configured": odds_mod.api_key() is not None}


def _run_job(season, week):
    JOB.update(status="running", message="Training models...")
    try:
        r = run_pipeline(season, week, log=lambda s: JOB.update(message=s))
        JOB.update(status="done", message=f"Week {r['week']}: {r['games']} games")
    except Exception as e:
        logger.exception("pipeline failed")
        JOB.update(status="error", message=str(e))
    JOB["finished_at"] = datetime.now(timezone.utc).isoformat()


@api.post("/nfl/pipeline/run")
async def pipeline_run(bg: BackgroundTasks, season: int | None = None, week: int | None = None):
    if JOB["status"] == "running":
        raise HTTPException(409, "Pipeline already running")
    JOB.update(status="running", message="Queued")
    bg.add_task(_run_job, season, week)
    return JOB


@api.post("/cron/nfl-refresh", status_code=202)
async def cron_nfl_refresh(request: Request, bg: BackgroundTasks):
    # Cron endpoints must ack 2xx immediately; enqueue/background the actual work.
    auth = request.headers.get("authorization", "")
    token = auth[7:] if auth.startswith("Bearer ") else ""
    if not token or not hmac.compare_digest(token, os.environ["WEBHOOK_CRON_SECRET"]):
        raise HTTPException(401, "Unauthorized")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid body")
    run_id = request.headers.get("x-webhook-id") or (body or {}).get("run_id")
    if not run_id:
        raise HTTPException(400, "Missing run id")
    try:
        await db.cron_runs.insert_one({"_id": run_id, "job": "nfl-refresh",
                                       "received_at": datetime.now(timezone.utc).isoformat()})
    except DuplicateKeyError:
        return {"status": "duplicate"}
    if JOB["status"] == "running":
        return {"status": "already_running"}
    JOB.update(status="running", message="Queued (daily refresh)")
    bg.add_task(_run_job, None, None)
    return {"status": "queued"}


@api.get("/nfl/pipeline/status")
async def pipeline_status():
    return JOB


app.include_router(api)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
