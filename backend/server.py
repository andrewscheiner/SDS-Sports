from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from nfl.edges import game_edges, fair_lines, american_to_decimal  # noqa: E402
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


@api.get("/nfl/week")
async def nfl_week(season: int, week: int):
    m = await get_meta()
    games = await db.nfl_games.find({"season": season, "week": week}, {"_id": 0}).sort(
        [("gameday", 1), ("gametime", 1)]).to_list(32)
    odds = {o["game_id"]: o async for o in db.nfl_odds.find(
        {"game_id": {"$in": [g["game_id"] for g in games]}}, {"_id": 0})}
    res = m["residuals"]
    all_edges = []
    for g in games:
        o = odds.get(g["game_id"], {"books": [], "source": "none"})
        pred = {p: tuple(g["pred"][p]) for p in ("q1", "h1")}
        g["fair"] = {p: fair_lines(*pred[p], res[p]) for p in ("q1", "h1")}
        g["odds_source"], g["odds_fetched_at"], g["books"] = o["source"], o.get("fetched_at"), o["books"]
        edges = game_edges(pred, o["books"], res, g["actual"])
        for e in edges:
            e.update(game_id=g["game_id"], matchup=f"{g['away_team']} @ {g['home_team']}",
                     team=g["home_team"] if e["side"] == "home" else g["away_team"] if e["side"] == "away" else None)
        g["edges"] = edges
        g["best_edge"] = max(edges, key=lambda e: e["ev"]) if edges else None
        all_edges += edges
    best = {}
    for e in sorted(all_edges, key=lambda e: -e["ev"]):
        best.setdefault((e["game_id"], e["market"], e["side"]), e)
    top = [e for e in best.values() if e["ev"] > 0][:10]
    graded = [e for e in best.values() if e["ev"] >= 0.04 and e["result"]]
    record = {r: sum(e["result"] == r for e in graded) for r in ("win", "loss", "push")}
    record["units"] = round(sum(
        (american_to_decimal(e["price"]) - 1) if e["result"] == "win" else -1 if e["result"] == "loss" else 0
        for e in graded), 2)
    return {"season": season, "week": week, "games": games, "top_edges": top, "record": record}


@api.post("/nfl/odds/refresh")
async def refresh_odds(season: int, week: int):
    games = await db.nfl_games.find({"season": season, "week": week},
                                    {"_id": 0, "game_id": 1, "home_team": 1, "away_team": 1,
                                     "spread_line": 1, "total_line": 1}).to_list(32)
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
