# ═══════════════════════════════════════════════════════════
#  config.py  —  All Nifty 50 Settings
# ═══════════════════════════════════════════════════════════

# ── All 50 Nifty 50 stocks (Yahoo Finance .NS symbols) ──────────────
NIFTY_50_STOCKS = [
    "RELIANCE.NS", "TCS.NS",       "HDFCBANK.NS",  "INFY.NS",       "ICICIBANK.NS",
    "HINDUNILVR.NS","ITC.NS",       "SBIN.NS",       "BHARTIARTL.NS", "KOTAKBANK.NS",
    "LT.NS",        "AXISBANK.NS",  "BAJFINANCE.NS", "HCLTECH.NS",    "MARUTI.NS",
    "ASIANPAINT.NS","TITAN.NS",     "SUNPHARMA.NS",  "BAJAJFINSV.NS", "WIPRO.NS",
    "TECHM.NS",     "ULTRACEMCO.NS","NESTLEIND.NS",  "POWERGRID.NS",  "NTPC.NS",
    "TATAMOTORS.NS","TATASTEEL.NS", "ONGC.NS",       "JSWSTEEL.NS",   "DRREDDY.NS",
    "CIPLA.NS",     "COALINDIA.NS", "DIVISLAB.NS",   "GRASIM.NS",     "HINDALCO.NS",
    "EICHERMOT.NS", "HEROMOTOCO.NS","INDUSINDBK.NS", "BRITANNIA.NS",  "BPCL.NS",
    "APOLLOHOSP.NS","ADANIPORTS.NS","ADANIENT.NS",   "HDFCLIFE.NS",   "SBILIFE.NS",
    "TATACONSUM.NS","SHREECEM.NS",  "UPL.NS",        "M&M.NS",        "BAJAJ-AUTO.NS",
]

# ── Sub-indices ────────────────────────────────────────────────────────
NIFTY_5_STOCKS  = ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS"]
NIFTY_10_STOCKS = NIFTY_5_STOCKS + ["HINDUNILVR.NS","ITC.NS","SBIN.NS","BHARTIARTL.NS","KOTAKBANK.NS"]
NIFTY_30_STOCKS = NIFTY_50_STOCKS[:30]

# Index symbol
NIFTY_INDEX     = "^NSEI"

# ── Sector mapping ─────────────────────────────────────────────────────
SECTOR_MAP = {
    "RELIANCE.NS":   "Energy",       "TCS.NS":       "IT",
    "HDFCBANK.NS":   "Banking",      "INFY.NS":      "IT",
    "ICICIBANK.NS":  "Banking",      "HINDUNILVR.NS":"FMCG",
    "ITC.NS":        "FMCG",         "SBIN.NS":      "Banking",
    "BHARTIARTL.NS": "Telecom",      "KOTAKBANK.NS": "Banking",
    "LT.NS":         "Infra",        "AXISBANK.NS":  "Banking",
    "BAJFINANCE.NS": "Finance",      "HCLTECH.NS":   "IT",
    "MARUTI.NS":     "Auto",         "ASIANPAINT.NS":"Paint",
    "TITAN.NS":      "Consumer",     "SUNPHARMA.NS": "Pharma",
    "BAJAJFINSV.NS": "Finance",      "WIPRO.NS":     "IT",
    "TECHM.NS":      "IT",           "ULTRACEMCO.NS":"Cement",
    "NESTLEIND.NS":  "FMCG",         "POWERGRID.NS": "Power",
    "NTPC.NS":       "Power",        "TATAMOTORS.NS":"Auto",
    "TATASTEEL.NS":  "Metal",        "ONGC.NS":      "Energy",
    "JSWSTEEL.NS":   "Metal",        "DRREDDY.NS":   "Pharma",
    "CIPLA.NS":      "Pharma",       "COALINDIA.NS": "Mining",
    "DIVISLAB.NS":   "Pharma",       "GRASIM.NS":    "Cement",
    "HINDALCO.NS":   "Metal",        "EICHERMOT.NS": "Auto",
    "HEROMOTOCO.NS": "Auto",         "INDUSINDBK.NS":"Banking",
    "BRITANNIA.NS":  "FMCG",         "BPCL.NS":      "Energy",
    "APOLLOHOSP.NS": "Healthcare",   "ADANIPORTS.NS":"Infra",
    "ADANIENT.NS":   "Energy",       "HDFCLIFE.NS":  "Insurance",
    "SBILIFE.NS":    "Insurance",    "TATACONSUM.NS":"FMCG",
    "SHREECEM.NS":   "Cement",       "UPL.NS":       "Agri",
    "M&M.NS":        "Auto",         "BAJAJ-AUTO.NS":"Auto",
}

# ── Display names ──────────────────────────────────────────────────────
STOCK_NAMES = {
    "RELIANCE.NS":   "Reliance Industries",  "TCS.NS":       "Tata Consultancy",
    "HDFCBANK.NS":   "HDFC Bank",            "INFY.NS":      "Infosys",
    "ICICIBANK.NS":  "ICICI Bank",           "HINDUNILVR.NS":"Hindustan Unilever",
    "ITC.NS":        "ITC Ltd",              "SBIN.NS":      "State Bank of India",
    "BHARTIARTL.NS": "Bharti Airtel",        "KOTAKBANK.NS": "Kotak Mahindra Bank",
    "LT.NS":         "Larsen & Toubro",      "AXISBANK.NS":  "Axis Bank",
    "BAJFINANCE.NS": "Bajaj Finance",        "HCLTECH.NS":   "HCL Technologies",
    "MARUTI.NS":     "Maruti Suzuki",        "ASIANPAINT.NS":"Asian Paints",
    "TITAN.NS":      "Titan Company",        "SUNPHARMA.NS": "Sun Pharma",
    "BAJAJFINSV.NS": "Bajaj Finserv",        "WIPRO.NS":     "Wipro",
    "TECHM.NS":      "Tech Mahindra",        "ULTRACEMCO.NS":"UltraTech Cement",
    "NESTLEIND.NS":  "Nestle India",         "POWERGRID.NS": "Power Grid",
    "NTPC.NS":       "NTPC Ltd",             "TATAMOTORS.NS":"Tata Motors",
    "TATASTEEL.NS":  "Tata Steel",           "ONGC.NS":      "ONGC",
    "JSWSTEEL.NS":   "JSW Steel",            "DRREDDY.NS":   "Dr Reddy's",
    "CIPLA.NS":      "Cipla",                "COALINDIA.NS": "Coal India",
    "DIVISLAB.NS":   "Divi's Labs",          "GRASIM.NS":    "Grasim Industries",
    "HINDALCO.NS":   "Hindalco",             "EICHERMOT.NS": "Eicher Motors",
    "HEROMOTOCO.NS": "Hero MotoCorp",        "INDUSINDBK.NS":"IndusInd Bank",
    "BRITANNIA.NS":  "Britannia",            "BPCL.NS":      "BPCL",
    "APOLLOHOSP.NS": "Apollo Hospitals",     "ADANIPORTS.NS":"Adani Ports",
    "ADANIENT.NS":   "Adani Enterprises",    "HDFCLIFE.NS":  "HDFC Life",
    "SBILIFE.NS":    "SBI Life",             "TATACONSUM.NS":"Tata Consumer",
    "SHREECEM.NS":   "Shree Cement",         "UPL.NS":       "UPL Ltd",
    "M&M.NS":        "Mahindra & Mahindra",  "BAJAJ-AUTO.NS":"Bajaj Auto",
    "^NSEI":         "Nifty 50 Index",
}

# ── Model Settings (for 80%+ accuracy) ────────────────────────────────
SEQUENCE_LENGTH    = 60
PREDICTION_DAYS    = 15
LSTM_EPOCHS        = 100
LSTM_BATCH_SIZE    = 32
LSTM_UNITS         = [256, 128, 64]
DROPOUT_RATE       = 0.2
LEARNING_RATE      = 0.001

# ── Technical thresholds ───────────────────────────────────────────────
RSI_OVERBOUGHT     = 70
RSI_OVERSOLD       = 30

# ── Dashboard ─────────────────────────────────────────────────────────
REFRESH_INTERVAL   = 120_000    # 2 minutes

# ── Colors (dark theme) ────────────────────────────────────────────────
C = {
    "bg":      "#0a0e1a",
    "card":    "#111827",
    "border":  "#1f2937",
    "accent":  "#3b82f6",
    "green":   "#10b981",
    "red":     "#ef4444",
    "yellow":  "#f59e0b",
    "purple":  "#8b5cf6",
    "text":    "#e5e7eb",
    "sub":     "#6b7280",
    "orange":  "#f97316",
}
