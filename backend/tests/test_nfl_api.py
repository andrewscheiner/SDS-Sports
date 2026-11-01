# NFL Q1/1H prediction dashboard API regression tests
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
S = requests.Session()


# Meta endpoint
def test_meta():
    r = S.get(f"{BASE_URL}/api/nfl/meta", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["season"] == 2026 and d["current_week"] == 8
    assert d["weeks"] == list(range(1, 9))
    assert d["metrics"]["pts_q1"]["mae"] > 0 and d["metrics"]["pts_h1"]["mae"] > 0
    assert len(d["importance"]) > 0 and "label" in d["importance"][0]
    assert len(d["books"]) == 7
    assert {b["key"] for b in d["books"]} >= {"draftkings", "fanduel", "betmgm", "williamhill_us", "espnbet", "fanatics", "bet365"}
    assert d["odds_key_configured"] is False
    assert d["train_start"] == 2018


# Current week games/edges
def test_week8():
    r = S.get(f"{BASE_URL}/api/nfl/week", params={"season": 2026, "week": 8}, timeout=60)
    assert r.status_code == 200
    d = r.json()
    assert len(d["games"]) == 14
    for g in d["games"]:
        assert len(g["pred"]["q1"]) == 2 and len(g["pred"]["h1"]) == 2
        assert "q1" in g["fair"] and "h1" in g["fair"]
        assert len(g["books"]) == 7
        assert len(g["edges"]) > 0 and g["best_edge"] is not None
        assert g["best_edge"]["ev"] == max(e["ev"] for e in g["edges"])
        # Thursday game may already be final
        if g["actual"] is None:
            assert all(e["result"] is None for e in g["edges"])
        assert g["odds_source"] == "sample"
    evs = [e["ev"] for e in d["top_edges"]]
    assert evs == sorted(evs, reverse=True)
    assert all(e > 0 for e in evs)
    assert set(d["record"]) == {"win", "loss", "push", "units"}


# Past week graded
def test_week5_graded():
    r = S.get(f"{BASE_URL}/api/nfl/week", params={"season": 2026, "week": 5}, timeout=60)
    assert r.status_code == 200
    d = r.json()
    assert len(d["games"]) > 0
    for g in d["games"]:
        assert g["actual"] is not None
        assert all(e["result"] in ("win", "loss", "push") for e in g["edges"])
    rec = d["record"]
    print("week5 record", rec)
    assert rec["win"] + rec["loss"] + rec["push"] > 0


# Edge: week with no data
def test_week_empty():
    r = S.get(f"{BASE_URL}/api/nfl/week", params={"season": 2026, "week": 20}, timeout=30)
    assert r.status_code == 200
    assert r.json()["games"] == []


def test_week_missing_params():
    r = S.get(f"{BASE_URL}/api/nfl/week", timeout=30)
    assert r.status_code == 422


# Odds refresh (sample)
def test_odds_refresh():
    r = S.post(f"{BASE_URL}/api/nfl/odds/refresh", params={"season": 2026, "week": 8}, timeout=60)
    assert r.status_code == 200
    d = r.json()
    assert d["key_configured"] is False
    assert d["updated"] == 14 and d["live"] == 0
    w = S.get(f"{BASE_URL}/api/nfl/week", params={"season": 2026, "week": 8}, timeout=60).json()
    assert all(len(g["books"]) == 7 for g in w["games"])


# Pipeline run + poll
def test_pipeline_run():
    r = S.post(f"{BASE_URL}/api/nfl/pipeline/run", timeout=30)
    assert r.status_code in (200, 409)
    r2 = S.post(f"{BASE_URL}/api/nfl/pipeline/run", timeout=30)
    assert r2.status_code == 409
    status = None
    for _ in range(60):
        status = S.get(f"{BASE_URL}/api/nfl/pipeline/status", timeout=30).json()
        if status["status"] != "running":
            break
        time.sleep(3)
    print("pipeline status", status)
    assert status["status"] == "done", status
    m = S.get(f"{BASE_URL}/api/nfl/meta", timeout=30).json()
    assert m["season"] == 2026 and m["current_week"] == 8
    w = S.get(f"{BASE_URL}/api/nfl/week", params={"season": 2026, "week": 8}, timeout=60).json()
    assert len(w["games"]) == 14
