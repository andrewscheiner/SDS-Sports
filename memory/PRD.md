# PRD — SDS Sports: NFL Q1 / 1H Prediction Dashboard

## Original problem
NFL dashboard for the user's React LLC site predicting 1st-quarter and 1st-half team scores for the current week (nflreadpy + XGBoost; EPA, plays run, etc.), compared against sportsbooks (ML, spread, total — no props) via The Odds API to find edges; Python pipeline writes to a DB the site displays.

## User choices
Odds API (no key yet → placeholder key, SAMPLE odds) · show 2026 Week 8 · train 2018–2025 (+2026 to date) · books DraftKings, FanDuel, BetMGM, Caesars, ESPN BET, Fanatics, Bet365 · dark green & gold, concise.

## Architecture
- `backend/nfl/features.py` — nflreadpy pbp → team-game stats (EPA, success, plays, Q1/1H plays & EPA, neutral pass rate, explosives, turnovers) → EWM pre-game features + opponent defense + Vegas line/total, rest, weather.
- `backend/nfl/model.py` — XGBoost (Poisson) for team Q1 & 1H points, blended 50/50 with Vegas-implied share; backtest 2023–25.
- `backend/nfl/edges.py` — residual simulation → win/tie probs, fair lines, EV per book/market/side, grading.
- `backend/nfl/odds.py` — The Odds API event odds (h2h/spreads/totals _q1/_h1) or SAMPLE odds.
- `backend/nfl/pipeline.py` — `python -m nfl.pipeline` → Mongo `nfl_games`, `nfl_odds`, `nfl_meta`.
- API: `/api/nfl/meta`, `/api/nfl/week`, `POST /api/nfl/odds/refresh`, `POST /api/nfl/pipeline/run`, `/api/nfl/pipeline/status`.
- Frontend route `/sports/nfl`.

## Implemented (2026-11-01)
- Full pipeline, walk-forward weekly predictions 2026 W1–8, graded past weeks, dashboard (week select, Q1/1H filter, min-EV, top edges, game cards, 7-book odds dialog, model panel, refresh/retrain).

## Backlog
- P0: Add real ODDS_API_KEY (Caesars/Fanatics need paid plan; verify bet365 key for US).
- P1: Scheduled odds refresh + line-movement history; season-long ROI tracking with real closing lines.
- P2: Hyperparameter tuning / extra features (pace sec/play, injuries, QB EPA); embed into LLC React site.
