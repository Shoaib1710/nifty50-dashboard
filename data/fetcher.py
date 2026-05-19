# ═══════════════════════════════════════════════════════════
#  data/fetcher.py  —  All Data Sources
# ═══════════════════════════════════════════════════════════
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")


def get_stock_data(symbol: str, period: str = "2y") -> pd.DataFrame:
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, auto_adjust=True)
        if df.empty:
            return pd.DataFrame()
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df.dropna(subset=["Close"], inplace=True)
        return df
    except Exception:
        return pd.DataFrame()


def get_nifty_index(period: str = "2y") -> pd.DataFrame:
    return get_stock_data("^NSEI", period)


def get_bulk_close(symbols: list, period: str = "1y") -> pd.DataFrame:
    data = {}
    for sym in symbols:
        try:
            df = get_stock_data(sym, period)
            if not df.empty:
                data[sym] = df["Close"]
        except Exception:
            pass
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data).dropna(how="all")


def get_live_price(symbol: str) -> dict:
    try:
        ticker = yf.Ticker(symbol)
        fi = ticker.fast_info
        price      = round(float(fi.last_price or 0),      2)
        prev_close = round(float(fi.previous_close or price), 2)
        change     = round(price - prev_close, 2)
        pct        = round((change / (prev_close + 1e-9)) * 100, 2)
        high52     = round(float(fi.year_high  or price), 2)
        low52      = round(float(fi.year_low   or price), 2)
        volume     = int(fi.last_volume or 0)
        return dict(price=price, prev_close=prev_close,
                    change=change, pct=pct, volume=volume,
                    high52=high52, low52=low52)
    except Exception as e:
        return dict(price=0, prev_close=0, change=0, pct=0,
                    volume=0, high52=0, low52=0, error=str(e))


def get_fundamentals(symbol: str) -> dict:
    try:
        info = yf.Ticker(symbol).info
        if not info:
            return {}
        roe = info.get("returnOnEquity")
        rev_growth = info.get("revenueGrowth")
        profit_margin = info.get("profitMargins")
        div_yield = info.get("dividendYield")
        return {
            "market_cap":      info.get("marketCap"),
            "pe_ratio":        info.get("trailingPE"),
            "pb_ratio":        info.get("priceToBook"),
            "eps":             info.get("trailingEps"),
            "div_yield":       round(div_yield * 100, 2)       if div_yield    else None,
            "roe":             round(roe * 100, 2)             if roe          else None,
            "revenue_growth":  round(rev_growth * 100, 1)     if rev_growth   else None,
            "profit_margin":   round(profit_margin * 100, 1)  if profit_margin else None,
            "debt_to_equity":  info.get("debtToEquity"),
            "current_ratio":   info.get("currentRatio"),
            "sector":          info.get("sector"),
            "employees":       info.get("fullTimeEmployees"),
            "description":     (info.get("longBusinessSummary") or "")[:300],
        }
    except Exception:
        return {}


def get_live_news(symbol: str, max_items: int = 10) -> list:
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news or []
        result = []
        for item in news[:max_items]:
            content = item.get("content") or {}
            title   = content.get("title") or item.get("title", "")
            link    = (content.get("canonicalUrl") or {}).get("url") or item.get("link", "#")
            pub     = (content.get("provider") or {}).get("displayName") or item.get("publisher", "")
            ts      = (content.get("pubDate") or "")
            if not ts:
                ts_raw = item.get("providerPublishTime", 0)
                ts = datetime.fromtimestamp(ts_raw).strftime("%d %b %Y %H:%M") if ts_raw else ""
            else:
                try:
                    ts = pd.to_datetime(ts).strftime("%d %b %Y %H:%M")
                except Exception:
                    pass
            if title:
                result.append({"title": title, "publisher": pub, "link": link, "published": ts})
        return result
    except Exception:
        return []


def get_nifty_news(max_items: int = 15) -> list:
    results = []
    for sym in ["^NSEI", "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS"]:
        results.extend(get_live_news(sym, max_items=4))
    seen, unique = set(), []
    for item in results:
        if item["title"] not in seen:
            seen.add(item["title"])
            unique.append(item)
    return unique[:max_items]


def get_sector_performance(sector_map: dict, period: str = "1mo") -> pd.DataFrame:
    from collections import defaultdict
    sector_returns = defaultdict(list)
    for symbol, sector in sector_map.items():
        try:
            df = get_stock_data(symbol, period)
            if len(df) >= 2:
                ret = (df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100
                sector_returns[sector].append(float(ret))
        except Exception:
            pass
    rows = [{"Sector": k, "Return %": round(np.mean(v), 2)} for k, v in sector_returns.items()]
    return pd.DataFrame(rows).sort_values("Return %", ascending=False)


def get_synthetic_index(symbols: list, period: str = "1y",
                        index_name: str = "Custom Index") -> pd.DataFrame:
    bulk = get_bulk_close(symbols, period)
    if bulk.empty:
        return pd.DataFrame()
    norm = bulk.div(bulk.iloc[0]) * 100
    idx = norm.mean(axis=1)
    df = pd.DataFrame({"Close": idx}, index=bulk.index)
    df["Open"]   = df["Close"].shift(1).fillna(df["Close"])
    df["High"]   = df["Close"] * 1.005
    df["Low"]    = df["Close"] * 0.995
    df["Volume"] = 1.0
    return df
