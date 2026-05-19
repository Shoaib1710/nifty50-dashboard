# ═══════════════════════════════════════════════════════════
#  models/sentiment.py  —  VADER + FinBERT (optional)
# ═══════════════════════════════════════════════════════════
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_vader = SentimentIntensityAnalyzer()
_finbert = None


def _load_finbert():
    global _finbert
    if _finbert is None:
        try:
            from transformers import pipeline
            _finbert = pipeline(
                "text-classification",
                model="ProsusAI/finbert",
                device=-1, truncation=True, max_length=512,
            )
        except Exception:
            _finbert = None
    return _finbert


LABEL_COLORS = {"Positive": "#10b981", "Negative": "#ef4444", "Neutral": "#f59e0b"}


def analyze(headlines: list, use_finbert: bool = False) -> dict:
    if not headlines:
        return {"overall": "Neutral", "score": 0.0, "items": [], "method": "N/A"}

    results = []
    method  = "VADER"

    if use_finbert:
        pipe = _load_finbert()
        if pipe:
            method = "FinBERT"
            try:
                raw = pipe(headlines)
                lmap = {"positive": 1, "negative": -1, "neutral": 0}
                for text, r in zip(headlines, raw):
                    label = r["label"].lower()
                    score = r["score"] * lmap.get(label, 0)
                    results.append({"headline": text, "label": label.capitalize(), "score": round(score, 3)})
            except Exception:
                results = []

    if not results:
        method = "VADER"
        for text in headlines:
            vs    = _vader.polarity_scores(text)
            sc    = vs["compound"]
            label = "Positive" if sc >= 0.05 else "Negative" if sc <= -0.05 else "Neutral"
            results.append({"headline": text, "label": label, "score": round(sc, 3)})

    avg = np.mean([r["score"] for r in results])
    if avg >= 0.05:    overall = "Bullish 📈"
    elif avg <= -0.05: overall = "Bearish 📉"
    else:              overall = "Neutral ➡️"

    return {
        "overall": overall,
        "score":   round(float(avg), 3),
        "items":   results,
        "method":  method,
        "pos_pct": round(len([r for r in results if r["label"] == "Positive"]) / len(results) * 100, 1),
        "neg_pct": round(len([r for r in results if r["label"] == "Negative"]) / len(results) * 100, 1),
    }
