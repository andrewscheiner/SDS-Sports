"""Turn predicted scores + residual distribution into probabilities and betting edges."""
import numpy as np

MARKET_LABELS = {"q1_ml": "Q1 ML", "q1_spread": "Q1 Spread", "q1_total": "Q1 Total",
                 "h1_ml": "1H ML", "h1_spread": "1H Spread", "h1_total": "1H Total"}


def american_to_decimal(a):
    return 1 + (a / 100 if a > 0 else 100 / -a)


def prob_to_american(p):
    if p <= 0 or p >= 1:
        return None
    return round(-100 * p / (1 - p)) if p >= 0.5 else round(100 * (1 - p) / p)


def simulate(home_pred, away_pred, residuals):
    r = np.asarray(residuals)
    hs = np.maximum(0, np.round(home_pred + r[:, 0]))
    as_ = np.maximum(0, np.round(away_pred + r[:, 1]))
    return hs, as_


def fair_lines(home_pred, away_pred, residuals):
    hs, as_ = simulate(home_pred, away_pred, residuals)
    ph, pa, pt = float((hs > as_).mean()), float((hs < as_).mean()), float((hs == as_).mean())
    nh = ph / (ph + pa) if ph + pa else 0.5
    return {"home": round(home_pred, 2), "away": round(away_pred, 2),
            "margin": round(home_pred - away_pred, 2), "total": round(home_pred + away_pred, 2),
            "p_home": round(ph, 3), "p_away": round(pa, 3), "p_tie": round(pt, 3),
            "fair_ml_home": prob_to_american(nh), "fair_ml_away": prob_to_american(1 - nh)}


def _outcomes(market, side, point, hs, as_, has_draw=False):
    """Returns boolean arrays (win, loss) per simulation."""
    if market.endswith("_ml"):
        diff = hs - as_ if side == "home" else as_ - hs
        return diff > 0, (diff < 0) | ((diff == 0) & has_draw)
    if market.endswith("_spread"):
        diff = (hs - as_ if side == "home" else as_ - hs) + point
        return diff > 0, diff < 0
    tot = hs + as_ - point
    return (tot > 0, tot < 0) if side == "over" else (tot < 0, tot > 0)


def _grade(market, side, point, actual, has_draw):
    if actual is None:
        return None
    w, l = _outcomes(market, side, point, np.array([actual[0]]), np.array([actual[1]]), has_draw)
    return "win" if w[0] else "loss" if l[0] else "push"


def _sides(market, m):
    if market.endswith("_ml"):
        return [("home", None, m.get("home")), ("away", None, m.get("away"))]
    if market.endswith("_spread"):
        return [("home", m.get("home_point"), m.get("home_price")), ("away", m.get("away_point"), m.get("away_price"))]
    return [("over", m.get("point"), m.get("over")), ("under", m.get("point"), m.get("under"))]


def game_edges(pred, books, residuals, actual=None):
    """pred: {'q1': (home, away), 'h1': (home, away)}; books: [{book, title, markets}]."""
    sims = {p: simulate(*pred[p], residuals[p]) for p in ("q1", "h1")}
    edges = []
    for b in books:
        for market, m in b["markets"].items():
            period = market[:2]
            hs, as_ = sims[period]
            has_draw = m.get("draw") is not None
            act = actual.get(period) if actual else None
            for side, point, price in _sides(market, m):
                if price is None or (point is None and not market.endswith("_ml")):
                    continue
                win, loss = _outcomes(market, side, point, hs, as_, has_draw)
                pw, pl = float(win.mean()), float(loss.mean())
                dec = american_to_decimal(price)
                edges.append({
                    "book": b["book"], "book_title": b["title"], "market": market,
                    "market_label": MARKET_LABELS[market], "side": side, "point": point, "price": price,
                    "model_prob": round(pw / (pw + pl), 4) if pw + pl else None,
                    "implied_prob": round(1 / dec, 4), "ev": round(pw * (dec - 1) - pl, 4),
                    "result": _grade(market, side, point, act, has_draw),
                })
    return edges
