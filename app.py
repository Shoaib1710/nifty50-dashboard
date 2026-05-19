# ═══════════════════════════════════════════════════════════════
#  app.py  —  Nifty 50 AI Dashboard (Flask Backend)
#  Run: python app.py
#  Open: http://localhost:5000
# ═══════════════════════════════════════════════════════════════
import os
import json
import warnings
import numpy as np
import pandas as pd
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

warnings.filterwarnings("ignore")

from config import (
    NIFTY_50_STOCKS, NIFTY_5_STOCKS, NIFTY_10_STOCKS, NIFTY_30_STOCKS,
    NIFTY_INDEX, STOCK_NAMES, SECTOR_MAP, C, REFRESH_INTERVAL,
)
from data.fetcher import (
    get_stock_data, get_nifty_index, get_bulk_close,
    get_live_price, get_fundamentals, get_live_news,
    get_nifty_news, get_sector_performance, get_synthetic_index,
)
from models.technical_signals import generate_signals, backtest
from models.sentiment import analyze
from models.predictor import train_and_predict

# ── Flask App ──────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)
CORS(app)

# ── Index options ──────────────────────────────────────────────────
INDEX_OPTIONS = [
    {"label": "📊 Nifty 50 Index",   "value": "NIFTY_INDEX"},
    {"label": "🔢 Nifty 50 Stocks",  "value": "NIFTY_50"},
    {"label": "🔢 Nifty 30 Stocks",  "value": "NIFTY_30"},
    {"label": "🔢 Nifty 10 Stocks",  "value": "NIFTY_10"},
    {"label": "🔢 Nifty 5 Stocks",   "value": "NIFTY_5"},
] + [{"label": f"  {STOCK_NAMES.get(s, s)}", "value": s} for s in NIFTY_50_STOCKS]


def resolve_symbol(value: str):
    """Returns (yf_symbol, display_name, is_basket, basket_stocks)."""
    mapping = {
        "NIFTY_INDEX": ("^NSEI",  "Nifty 50 Index",   False, []),
        "NIFTY_50":    (None,     "Nifty 50 Basket",  True,  NIFTY_50_STOCKS),
        "NIFTY_30":    (None,     "Nifty 30 Basket",  True,  NIFTY_30_STOCKS),
        "NIFTY_10":    (None,     "Nifty 10 Basket",  True,  NIFTY_10_STOCKS),
        "NIFTY_5":     (None,     "Nifty 5 Basket",   True,  NIFTY_5_STOCKS),
    }
    if value in mapping:
        return mapping[value]
    return value, STOCK_NAMES.get(value, value), False, []


# ══════════════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/stocks")
def api_stocks():
    return jsonify({"options": INDEX_OPTIONS})


@app.route("/api/data")
def api_data():
    symbol = request.args.get("symbol", "NIFTY_INDEX")
    period = request.args.get("period", "1y")
    try:
        sym, name, is_basket, basket = resolve_symbol(symbol)
        if is_basket:
            df = get_synthetic_index(basket, period, name)
        else:
            df = get_stock_data(sym, period)

        if df is None or df.empty:
            return jsonify({"error": "No data returned. Try a different period."})

        df = generate_signals(df)
        last  = float(df["Close"].iloc[-1])
        prev  = float(df["Close"].iloc[-2]) if len(df) > 1 else last

        live = get_live_price(sym) if not is_basket else {}
        price   = live.get("price",   round(last, 2))
        change  = live.get("change",  round(last - prev, 2))
        pct     = live.get("pct",     round((last - prev) / (prev + 1e-9) * 100, 2))
        high52  = live.get("high52",  round(float(df["Close"].max()), 2))
        low52   = live.get("low52",   round(float(df["Close"].min()), 2))
        signal  = str(df["Signal"].iloc[-1]) if "Signal" in df.columns else "HOLD"
        rsi     = float(df["RSI"].iloc[-1])  if "RSI"    in df.columns else None

        kpi = dict(name=name, price=price, change=change, pct=pct,
                   high52=high52, low52=low52, signal=signal, rsi=rsi)

        signals = []
        for idx, row in df.iterrows():
            s = str(row.get("Signal", "HOLD"))
            if s in ("BUY", "SELL"):
                y = float(row["Low"]) * 0.985 if s == "BUY" else float(row["High"]) * 1.015
                signals.append({"date": str(idx), "type": s, "y": y})

        bt = backtest(df)
        clean_trades = [{"return_pct": t["return_pct"], "buy_date": str(t["buy_date"]), "sell_date": str(t["sell_date"])} for t in bt.get("trades", [])]
        bt["trades"] = clean_trades

        def to_list(col):
            if col not in df.columns:
                return None
            return [None if pd.isna(v) else float(v) for v in df[col]]

        return jsonify({
            "name":      name,
            "dates":     [str(i) for i in df.index],
            "open":      to_list("Open"),
            "high":      to_list("High"),
            "low":       to_list("Low"),
            "close":     to_list("Close"),
            "volume":    to_list("Volume"),
            "rsi":       to_list("RSI"),
            "macd":      to_list("MACD"),
            "macd_sig":  to_list("MACD_Sig"),
            "macd_hist": to_list("MACD_Hist"),
            "bb_upper":  to_list("BB_Upper"),
            "bb_mid":    to_list("BB_Mid"),
            "bb_lower":  to_list("BB_Lower"),
            "ema20":     to_list("EMA_20"),
            "ema50":     to_list("EMA_50"),
            "signals":   signals,
            "kpi":       kpi,
            "backtest":  bt,
        })
    except Exception as e:
        import traceback
        return jsonify({"error": f"Data fetch failed: {str(e)}", "trace": traceback.format_exc()})


@app.route("/api/heatmap")
def api_heatmap():
    try:
        returns = {}
        for s in NIFTY_50_STOCKS:
            try:
                lv = get_live_price(s)
                returns[s] = lv.get("pct", 0.0)
            except Exception:
                returns[s] = 0.0

        names    = [STOCK_NAMES.get(s, s) for s in NIFTY_50_STOCKS]
        rets     = [float(returns.get(s, 0)) for s in NIFTY_50_STOCKS]
        sectors  = [SECTOR_MAP.get(s, "Other") for s in NIFTY_50_STOCKS]
        abs_rets = [abs(r) + 0.1 for r in rets]

        sect_df  = pd.DataFrame({"Sector": sectors, "Return": rets})
        sect_avg = sect_df.groupby("Sector")["Return"].mean().reset_index().sort_values("Return")
        return jsonify({
            "names":      names,
            "rets":       rets,
            "abs_rets":   abs_rets,
            "sectors":    sectors,
            "sect_names": list(sect_avg["Sector"]),
            "sect_rets":  [round(float(r), 3) for r in sect_avg["Return"]],
        })
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/news")
def api_news():
    symbol = request.args.get("symbol", "NIFTY_INDEX")
    try:
        sym, name, is_basket, _ = resolve_symbol(symbol)
        if is_basket or sym is None:
            news = get_nifty_news(15)
        else:
            news = get_live_news(sym, 15)
            if len(news) < 5:
                news += get_nifty_news(8)
        news = news[:20]
        headlines   = [n.get("title", "") for n in news]
        sent_result = analyze(headlines)
        return jsonify({
            "news":       news,
            "sentiments": sent_result["items"],
            "sentiment":  {
                "overall": sent_result["overall"],
                "score":   sent_result["score"],
                "pos_pct": sent_result.get("pos_pct", 0),
                "neg_pct": sent_result.get("neg_pct", 0),
                "method":  sent_result["method"],
            },
        })
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/fundamentals")
def api_fundamentals():
    symbol = request.args.get("symbol", "NIFTY_INDEX")
    try:
        sym, name, is_basket, basket = resolve_symbol(symbol)
        syms = basket[:10] if is_basket else ([sym] if sym else [])
        stocks = []
        for s in syms:
            if not s:
                continue
            f = get_fundamentals(s)
            if not f:
                continue
            mc = f.get("market_cap")
            mc_str = (f"₹{mc/1e12:.2f}T" if mc and mc > 1e12 else f"₹{mc/1e9:.1f}B" if mc else "—")
            def fmtv(v, pre="", suf="", dec=2):
                if v is None: return "—"
                if isinstance(v, float): return f"{pre}{v:.{dec}f}{suf}"
                return f"{pre}{v}{suf}"
            stocks.append({
                "name":           STOCK_NAMES.get(s, s),
                "market_cap":     mc_str,
                "pe_ratio":       fmtv(f.get("pe_ratio"), dec=1),
                "pb_ratio":       fmtv(f.get("pb_ratio")),
                "eps":            fmtv(f.get("eps"), pre="₹"),
                "roe":            fmtv(f.get("roe"), suf="%", dec=1),
                "div_yield":      fmtv(f.get("div_yield"), suf="%"),
                "revenue_growth": fmtv(f.get("revenue_growth"), suf="%", dec=1),
                "profit_margin":  fmtv(f.get("profit_margin"), suf="%", dec=1),
                "debt_to_equity": fmtv(f.get("debt_to_equity")),
                "current_ratio":  fmtv(f.get("current_ratio")),
                "sector":         f.get("sector", "—"),
                "employees":      f"{f['employees']:,}" if f.get("employees") else "—",
                "description":    f.get("description", ""),
            })
        return jsonify({"stocks": stocks})
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/train", methods=["POST"])
def api_train():
    body   = request.get_json(force=True, silent=True) or {}
    symbol = body.get("symbol", "NIFTY_INDEX")
    period = body.get("period", "1y")
    try:
        sym, name, is_basket, basket = resolve_symbol(symbol)
        raw_df   = get_synthetic_index(basket, period) if is_basket else get_stock_data(sym, period)
        nifty_df = get_nifty_index(period)
        result   = train_and_predict(raw_df, nifty_df)
        if "error" in result:
            return jsonify(result)
        return jsonify({
            "test_dates":     [str(d) for d in result["test_dates"]],
            "real_prices":    [float(v) for v in result["real_prices"]],
            "pred_prices":    [float(v) for v in result["pred_prices"]],
            "future_dates":   [str(d) for d in result["future_dates"]],
            "future_prices":  [float(v) for v in result["future_prices"]],
            "rmse":           result["rmse"],
            "mape":           result["mape"],
            "lstm_acc":       result["lstm_acc"],
            "rf_acc":         result["rf_acc"],
            "gb_acc":         result["gb_acc"],
            "ensemble_acc":   result["ensemble_acc"],
            "current_signal": result["current_signal"],
            "confidence":     result["confidence"],
            "importance":     result["importance_df"].to_dict("records"),
        })
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()})


# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("🚀 Starting Nifty 50 AI Dashboard...")
    print("📊 Open: http://localhost:5000")
    print("⏹  Stop: Ctrl+C")
    app.run(debug=True, port=5000, use_reloader=False)
