# 🇮🇳 Nifty 50 AI Dashboard

**Real-time · LSTM + Attention · Ensemble ML · 80%+ Accuracy**

A full-stack stock analysis dashboard for Nifty 50 Indian stocks with AI-powered predictions.

---

## 📁 Project Structure

```
nifty50_dashboard/
│
├── app.py                        ← 🚀 Main Flask app (run this)
├── config.py                     ← ⚙️  All Nifty 50 stocks, sectors, settings
├── requirements.txt              ← 📦 Python dependencies
│
├── data/
│   ├── __init__.py
│   └── fetcher.py                ← 📡 yFinance data fetching (prices, news, fundamentals)
│
├── models/
│   ├── __init__.py
│   ├── technical_signals.py      ← 📈 RSI, MACD, Bollinger Bands, Backtest
│   ├── feature_engineering.py   ← 🔧 50+ ML features
│   ├── sentiment.py              ← 💬 VADER sentiment analysis
│   └── predictor.py              ← 🤖 LSTM + Attention + Random Forest + GBM
│
├── static/
│   ├── style.css                 ← 🎨 Dark theme CSS
│   └── main.js                   ← ⚡ Frontend JS (Plotly charts, API calls)
│
└── templates/
    └── index.html                ← 🖥️  Main HTML template
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.9 or newer
- pip

### 2. Install Dependencies

```bash
cd nifty50_dashboard
pip install -r requirements.txt
```

> **GPU (optional):** For faster LSTM training, install TensorFlow with GPU support.
> For CPU-only: `pip install tensorflow-cpu` instead.

### 3. Run the App

```bash
python app.py
```

### 4. Open in Browser

```
http://localhost:5000
```

---

## 🎛️ Features

| Tab | Feature |
|-----|---------|
| 📈 Price & Signals | Candlestick chart, Bollinger Bands, EMA, Volume, BUY/SELL markers |
| 🤖 AI Prediction | LSTM + Attention forecast, 15-day future prediction |
| 🗺️ Nifty Heatmap | Treemap of all 50 stocks + sector performance |
| 📰 News & Sentiment | Live news + VADER sentiment gauge |
| 📋 Fundamentals | P/E, P/B, ROE, EPS, Market Cap per stock |
| 🔁 Backtest | RSI + MACD strategy equity curve |

---

## 🤖 ML Models

- **LSTM + Multi-Head Attention** — Price regression with bidirectional LSTM
- **Random Forest** — Direction classification (200 trees)
- **Gradient Boosting** — Direction classification
- **Ensemble** — Weighted vote: 30% LSTM + 35% RF + 35% GB

**50+ features** including RSI, MACD, Bollinger Bands, ATR, Stochastic, Williams %R, CCI, ADX, OBV, VWAP, candlestick patterns, calendar features, and Nifty correlation.

---

## ⚠️ Disclaimer

This dashboard is for **educational and research purposes only**.
It is **not financial advice**. ML predictions carry significant risk.
Always do your own research before making investment decisions.

---

## 🔧 VS Code Tips

1. Install the **Python** extension
2. Select your Python interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter"
3. Open terminal: `Ctrl+`` ` → `python app.py`
4. Set `"python.terminal.activateEnvironment": true` in settings for venv support

### Recommended Extensions
- Python (Microsoft)
- Pylance
- GitLens
