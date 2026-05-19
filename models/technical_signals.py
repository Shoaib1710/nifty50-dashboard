# ═══════════════════════════════════════════════════════════
#  models/technical_signals.py
#  RSI · MACD · Bollinger Bands · Signals · Backtest
# ═══════════════════════════════════════════════════════════
import pandas as pd
import numpy as np
import ta
from config import RSI_OVERBOUGHT, RSI_OVERSOLD


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["RSI"]      = ta.momentum.RSIIndicator(df["Close"]).rsi()
    macd           = ta.trend.MACD(df["Close"])
    df["MACD"]     = macd.macd()
    df["MACD_Sig"] = macd.macd_signal()
    df["MACD_Hist"]= macd.macd_diff()
    bb             = ta.volatility.BollingerBands(df["Close"])
    df["BB_Upper"] = bb.bollinger_hband()
    df["BB_Mid"]   = bb.bollinger_mavg()
    df["BB_Lower"] = bb.bollinger_lband()
    df["BB_Width"] = bb.bollinger_wband()
    df["EMA_20"]   = ta.trend.EMAIndicator(df["Close"], 20).ema_indicator()
    df["EMA_50"]   = ta.trend.EMAIndicator(df["Close"], 50).ema_indicator()
    df["Vol_SMA20"]= df["Volume"].rolling(20).mean()
    df["ATR"]      = ta.volatility.AverageTrueRange(df["High"], df["Low"], df["Close"]).average_true_range()
    return df


def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    df = add_indicators(df)
    buy = (
        (df["RSI"] < RSI_OVERSOLD) &
        (df["MACD"] > df["MACD_Sig"]) &
        (df["MACD"].shift(1) <= df["MACD_Sig"].shift(1))
    )
    sell = (
        (df["RSI"] > RSI_OVERBOUGHT) |
        (
            (df["MACD"] < df["MACD_Sig"]) &
            (df["MACD"].shift(1) >= df["MACD_Sig"].shift(1))
        )
    )
    df["Signal"] = "HOLD"
    df.loc[buy,  "Signal"] = "BUY"
    df.loc[sell, "Signal"] = "SELL"
    return df


def backtest(df: pd.DataFrame) -> dict:
    trades, position = [], None
    for i, row in df.iterrows():
        if row["Signal"] == "BUY" and position is None:
            position = {"buy_price": row["Close"], "date": i}
        elif row["Signal"] == "SELL" and position is not None:
            ret = (row["Close"] - position["buy_price"]) / position["buy_price"] * 100
            trades.append({"return_pct": round(ret, 2), "buy_date": position["date"], "sell_date": i})
            position = None
    if not trades:
        return {"total_return": 0, "win_rate": 0, "num_trades": 0, "avg_return": 0, "trades": []}
    wr = len([t for t in trades if t["return_pct"] > 0]) / len(trades) * 100
    return {
        "total_return": round(sum(t["return_pct"] for t in trades), 2),
        "win_rate":     round(wr, 1),
        "num_trades":   len(trades),
        "avg_return":   round(np.mean([t["return_pct"] for t in trades]), 2),
        "trades":       trades,
    }
