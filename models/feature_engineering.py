# ═══════════════════════════════════════════════════════════
#  models/feature_engineering.py
#  50+ Features for High-Accuracy Prediction
# ═══════════════════════════════════════════════════════════
import pandas as pd
import numpy as np
import ta
import warnings
warnings.filterwarnings("ignore")


def build_features(df: pd.DataFrame, nifty_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Build 50+ features from OHLCV data.
    Optionally include Nifty 50 index as market context.
    """
    df = df.copy()

    # ── 1. Returns & Log Returns ─────────────────────────────────────
    df["Return_1d"]  = df["Close"].pct_change(1)
    df["Return_3d"]  = df["Close"].pct_change(3)
    df["Return_5d"]  = df["Close"].pct_change(5)
    df["Return_10d"] = df["Close"].pct_change(10)
    df["Return_20d"] = df["Close"].pct_change(20)
    df["Log_Return"] = np.log(df["Close"] / df["Close"].shift(1))

    # ── 2. Moving Averages ───────────────────────────────────────────
    for window in [5, 10, 20, 50, 100, 200]:
        df[f"SMA_{window}"] = df["Close"].rolling(window).mean()
        df[f"EMA_{window}"] = ta.trend.EMAIndicator(df["Close"], window=window).ema_indicator()

    # ── 3. MA Ratios ─────────────────────────────────────────────────
    for window in [20, 50, 200]:
        df[f"Price_SMA{window}_Ratio"] = df["Close"] / df[f"SMA_{window}"]

    # ── 4. RSI (multiple periods) ────────────────────────────────────
    for window in [7, 14, 21]:
        df[f"RSI_{window}"] = ta.momentum.RSIIndicator(df["Close"], window=window).rsi()

    # ── 5. MACD ──────────────────────────────────────────────────────
    macd = ta.trend.MACD(df["Close"])
    df["MACD"]       = macd.macd()
    df["MACD_Signal"]= macd.macd_signal()
    df["MACD_Hist"]  = macd.macd_diff()
    df["MACD_Cross"] = (df["MACD"] > df["MACD_Signal"]).astype(int)

    # ── 6. Bollinger Bands ───────────────────────────────────────────
    bb = ta.volatility.BollingerBands(df["Close"])
    df["BB_Upper"]  = bb.bollinger_hband()
    df["BB_Mid"]    = bb.bollinger_mavg()
    df["BB_Lower"]  = bb.bollinger_lband()
    df["BB_Width"]  = bb.bollinger_wband()
    df["BB_Pos"]    = (df["Close"] - df["BB_Lower"]) / (df["BB_Upper"] - df["BB_Lower"] + 1e-9)

    # ── 7. ATR & Volatility ──────────────────────────────────────────
    df["ATR_14"]  = ta.volatility.AverageTrueRange(df["High"], df["Low"], df["Close"]).average_true_range()
    df["ATR_Pct"] = df["ATR_14"] / df["Close"]
    df["Volatility_20d"] = df["Log_Return"].rolling(20).std() * np.sqrt(252)
    df["Volatility_5d"]  = df["Log_Return"].rolling(5).std()  * np.sqrt(252)

    # ── 8. Stochastic Oscillator ─────────────────────────────────────
    stoch = ta.momentum.StochasticOscillator(df["High"], df["Low"], df["Close"])
    df["Stoch_K"] = stoch.stoch()
    df["Stoch_D"] = stoch.stoch_signal()

    # ── 9. Williams %R ───────────────────────────────────────────────
    df["Williams_R"] = ta.momentum.WilliamsRIndicator(df["High"], df["Low"], df["Close"]).williams_r()

    # ── 10. CCI ──────────────────────────────────────────────────────
    df["CCI"] = ta.trend.CCIIndicator(df["High"], df["Low"], df["Close"]).cci()

    # ── 11. ADX ──────────────────────────────────────────────────────
    adx = ta.trend.ADXIndicator(df["High"], df["Low"], df["Close"])
    df["ADX"]     = adx.adx()
    df["ADX_Pos"] = adx.adx_pos()
    df["ADX_Neg"] = adx.adx_neg()

    # ── 12. OBV ──────────────────────────────────────────────────────
    df["OBV"]      = ta.volume.OnBalanceVolumeIndicator(df["Close"], df["Volume"]).on_balance_volume()
    df["OBV_SMA20"]= df["OBV"].rolling(20).mean()

    # ── 13. Volume Indicators ────────────────────────────────────────
    df["Vol_SMA20"]     = df["Volume"].rolling(20).mean()
    df["Vol_Ratio"]     = df["Volume"] / (df["Vol_SMA20"] + 1e-9)
    df["VWAP"]          = (df["Close"] * df["Volume"]).rolling(20).sum() / (df["Volume"].rolling(20).sum() + 1e-9)
    df["Price_VWAP_Ratio"] = df["Close"] / (df["VWAP"] + 1e-9)

    # ── 14. Candlestick Body Features ───────────────────────────────
    df["Body_Size"]  = abs(df["Close"] - df["Open"]) / (df["Open"] + 1e-9)
    df["Upper_Wick"] = (df["High"] - df[["Close","Open"]].max(axis=1)) / (df["Open"] + 1e-9)
    df["Lower_Wick"] = (df[["Close","Open"]].min(axis=1) - df["Low"]) / (df["Open"] + 1e-9)
    df["Is_Bullish"] = (df["Close"] > df["Open"]).astype(int)

    # ── 15. Momentum ─────────────────────────────────────────────────
    df["ROC_10"] = ta.momentum.ROCIndicator(df["Close"], window=10).roc()
    df["ROC_20"] = ta.momentum.ROCIndicator(df["Close"], window=20).roc()
    df["MOM_10"] = ta.momentum.AwesomeOscillatorIndicator(df["High"], df["Low"]).awesome_oscillator()

    # ── 16. Nifty Index Correlation ──────────────────────────────────
    if nifty_df is not None and not nifty_df.empty:
        try:
            nifty_aligned = nifty_df["Close"].reindex(df.index, method="ffill")
            df["Nifty_Return_1d"] = nifty_aligned.pct_change(1)
            df["Nifty_Return_5d"] = nifty_aligned.pct_change(5)
            df["Beta_20d"] = (
                df["Return_1d"].rolling(20).cov(df["Nifty_Return_1d"]) /
                df["Nifty_Return_1d"].rolling(20).var()
            )
            df["Relative_Strength"] = df["Return_5d"] - df["Nifty_Return_5d"]
        except Exception:
            df["Nifty_Return_1d"] = 0
            df["Nifty_Return_5d"] = 0
            df["Beta_20d"]        = 1
            df["Relative_Strength"] = 0

    # ── 17. Calendar Features ────────────────────────────────────────
    df["DayOfWeek"]   = pd.to_datetime(df.index).dayofweek
    df["Month"]       = pd.to_datetime(df.index).month
    df["Quarter"]     = pd.to_datetime(df.index).quarter
    df["Is_MonthEnd"] = pd.to_datetime(df.index).is_month_end.astype(int)

    # ── 18. Target ────────────────────────────────────────────────────
    df["Target_Direction"] = (df["Close"].shift(-1) > df["Close"]).astype(int)
    df["Target_Price"]     = df["Close"].shift(-1)

    df.dropna(inplace=True)
    return df


def get_feature_columns(df: pd.DataFrame) -> list:
    exclude = {"Open","High","Low","Close","Volume","Dividends","Stock Splits",
               "Target_Direction","Target_Price"}
    return [c for c in df.columns if c not in exclude]
