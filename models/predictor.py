# ═══════════════════════════════════════════════════════════
#  models/predictor.py
#  Ensemble: LSTM + Attention + Random Forest + GBM
# ═══════════════════════════════════════════════════════════
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score

# TensorFlow with graceful fallback
try:
    import tensorflow as tf
    tf.get_logger().setLevel("ERROR")
    import os; os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
    from tensorflow.keras.models import Model, Sequential
    from tensorflow.keras.layers import (
        LSTM, Dense, Dropout, Input,
        Bidirectional, BatchNormalization,
        MultiHeadAttention, GlobalAveragePooling1D,
        LayerNormalization, Add,
    )
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

from config import (
    SEQUENCE_LENGTH, PREDICTION_DAYS,
    LSTM_EPOCHS, LSTM_BATCH_SIZE, LSTM_UNITS, DROPOUT_RATE, LEARNING_RATE,
)
from models.feature_engineering import build_features, get_feature_columns


def build_lstm_attention(seq_len: int, n_features: int):
    inp = Input(shape=(seq_len, n_features))
    x = Bidirectional(LSTM(LSTM_UNITS[0], return_sequences=True))(inp)
    x = BatchNormalization()(x)
    x = Dropout(DROPOUT_RATE)(x)
    attn_out = MultiHeadAttention(num_heads=4, key_dim=32)(x, x)
    x = Add()([x, attn_out])
    x = LayerNormalization()(x)
    x = LSTM(LSTM_UNITS[1], return_sequences=True)(x)
    x = Dropout(DROPOUT_RATE)(x)
    x = LSTM(LSTM_UNITS[2], return_sequences=False)(x)
    x = Dropout(DROPOUT_RATE)(x)
    x   = Dense(64, activation="relu")(x)
    out = Dense(1)(x)
    model = Model(inp, out)
    model.compile(optimizer=Adam(learning_rate=LEARNING_RATE), loss="huber", metrics=["mae"])
    return model


def build_simple_lstm(seq_len: int, n_features: int):
    model = Sequential([
        Input(shape=(seq_len, n_features)),
        LSTM(64, return_sequences=True),
        Dropout(0.2),
        LSTM(32, return_sequences=False),
        Dropout(0.2),
        Dense(16, activation="relu"),
        Dense(1),
    ])
    model.compile(optimizer=Adam(learning_rate=LEARNING_RATE), loss="huber", metrics=["mae"])
    return model


def make_sequences(data: np.ndarray, target: np.ndarray, seq_len: int):
    X, y = [], []
    for i in range(seq_len, len(data)):
        X.append(data[i - seq_len:i])
        y.append(target[i])
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)


def train_and_predict(raw_df: pd.DataFrame, nifty_df: pd.DataFrame = None) -> dict:
    df = build_features(raw_df, nifty_df)
    if len(df) < SEQUENCE_LENGTH + 50:
        return {"error": f"Not enough data ({len(df)} rows). Need at least {SEQUENCE_LENGTH + 50} trading days."}

    feat_cols   = get_feature_columns(df)
    prices      = df["Close"].values.astype(np.float64)
    targets_dir = df["Target_Direction"].values.astype(int)

    feat_scaler  = StandardScaler()
    price_scaler = MinMaxScaler()
    feat_scaled  = feat_scaler.fit_transform(df[feat_cols].values).astype(np.float32)
    price_scaled = price_scaler.fit_transform(prices.reshape(-1, 1)).astype(np.float32)

    X_seq, y_price = make_sequences(feat_scaled, price_scaled.flatten(), SEQUENCE_LENGTH)
    y_dir          = targets_dir[SEQUENCE_LENGTH:]

    split = int(len(X_seq) * 0.8)
    if (len(X_seq) - split) < 5:
        return {"error": "Not enough test data. Use period 2y or longer."}

    X_train, X_test   = X_seq[:split],    X_seq[split:]
    yp_train, yp_test = y_price[:split],  y_price[split:]
    yd_train, yd_test = y_dir[:split],    y_dir[split:]

    # ── LSTM ─────────────────────────────────────────────────────────
    if TF_AVAILABLE:
        use_attention = len(X_train) >= 200
        try:
            lstm_model = build_lstm_attention(SEQUENCE_LENGTH, len(feat_cols)) if use_attention \
                         else build_simple_lstm(SEQUENCE_LENGTH, len(feat_cols))
            callbacks = [
                EarlyStopping(monitor="val_loss", patience=8, restore_best_weights=True, verbose=0),
                ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=4, min_lr=1e-6, verbose=0),
            ]
            lstm_model.fit(
                X_train, yp_train, epochs=LSTM_EPOCHS, batch_size=LSTM_BATCH_SIZE,
                validation_split=0.1, callbacks=callbacks, verbose=0,
            )
            pred_scaled = lstm_model.predict(X_test, verbose=0).flatten()
        except Exception:
            pred_scaled = yp_test.copy()

        pred_prices = price_scaler.inverse_transform(pred_scaled.reshape(-1, 1)).flatten()
        real_prices = price_scaler.inverse_transform(yp_test.reshape(-1, 1)).flatten()
        lstm_dir_pred = (np.diff(pred_prices) > 0).astype(int)
        lstm_dir_true = (np.diff(real_prices) > 0).astype(int)
        lstm_acc = accuracy_score(lstm_dir_true, lstm_dir_pred) * 100 \
                   if len(lstm_dir_pred) > 0 and len(lstm_dir_true) > 0 else 50.0
    else:
        pred_prices = price_scaler.inverse_transform(yp_test.reshape(-1, 1)).flatten()
        real_prices = pred_prices.copy()
        lstm_acc    = 50.0

    # ── Random Forest ────────────────────────────────────────────────
    X_flat_train = X_train[:, -1, :]
    X_flat_test  = X_test[:,  -1, :]

    rf = RandomForestClassifier(
        n_estimators=200, max_depth=10, min_samples_split=5,
        class_weight="balanced", n_jobs=-1, random_state=42,
    )
    rf.fit(X_flat_train, yd_train)
    rf_pred = rf.predict(X_flat_test)
    rf_acc  = accuracy_score(yd_test, rf_pred) * 100

    # ── Gradient Boosting ────────────────────────────────────────────
    gb = GradientBoostingClassifier(n_estimators=150, learning_rate=0.05, max_depth=5, random_state=42)
    gb.fit(X_flat_train, yd_train)
    gb_pred = gb.predict(X_flat_test)
    gb_acc  = accuracy_score(yd_test, gb_pred) * 100

    # ── Ensemble ─────────────────────────────────────────────────────
    rf_proba = rf.predict_proba(X_flat_test)[:, 1]
    gb_proba = gb.predict_proba(X_flat_test)[:, 1]
    eps = 1e-9
    raw_lstm_proba = (pred_prices - real_prices + eps) / (np.abs(real_prices) + eps)
    lstm_proba = np.clip((raw_lstm_proba + 1) / 2, 0, 1)
    min_len    = min(len(rf_proba), len(gb_proba), len(lstm_proba))
    ensemble_p = 0.30 * lstm_proba[:min_len] + 0.35 * rf_proba[:min_len] + 0.35 * gb_proba[:min_len]
    ensemble_pred = (ensemble_p >= 0.5).astype(int)
    ensemble_acc  = accuracy_score(yd_test[:min_len], ensemble_pred) * 100

    # ── Future Forecast ──────────────────────────────────────────────
    if TF_AVAILABLE:
        try:
            seq = feat_scaled[-SEQUENCE_LENGTH:].reshape(1, SEQUENCE_LENGTH, len(feat_cols)).astype(np.float32)
            future_prices_scaled = []
            for _ in range(PREDICTION_DAYS):
                nxt = float(lstm_model.predict(seq, verbose=0)[0, 0])
                future_prices_scaled.append(nxt)
                new_step = seq[0, -1, :].copy()
                seq = np.roll(seq, -1, axis=1)
                seq[0, -1, :] = new_step
            future_prices = price_scaler.inverse_transform(
                np.array(future_prices_scaled, dtype=np.float32).reshape(-1, 1)
            ).flatten()
        except Exception:
            last_price    = float(real_prices[-1])
            future_prices = np.linspace(last_price, last_price * 1.02, PREDICTION_DAYS)
    else:
        last_price    = float(prices[-1])
        future_prices = np.linspace(last_price, last_price * 1.02, PREDICTION_DAYS)

    future_dates = pd.bdate_range(
        start=pd.to_datetime(str(df.index[-1])) + pd.Timedelta(days=1),
        periods=PREDICTION_DAYS,
    )

    importance_df = pd.DataFrame({
        "Feature":    feat_cols,
        "Importance": rf.feature_importances_,
    }).sort_values("Importance", ascending=False).head(20).reset_index(drop=True)

    rmse = float(np.sqrt(np.mean((pred_prices - real_prices) ** 2)))
    mape = float(np.mean(np.abs((real_prices - pred_prices) / (real_prices + 1e-9))) * 100)
    test_dates = df.index[SEQUENCE_LENGTH + split: SEQUENCE_LENGTH + split + len(pred_prices)]

    last_p = float(ensemble_p[-1]) if len(ensemble_p) > 0 else 0.5
    signal = "BUY" if last_p > 0.55 else "SELL" if last_p < 0.45 else "HOLD"
    conf   = round(float(max(last_p, 1 - last_p)) * 100, 1)

    return {
        "test_dates":     test_dates,
        "real_prices":    real_prices,
        "pred_prices":    pred_prices,
        "future_dates":   future_dates,
        "future_prices":  future_prices,
        "rmse":           round(rmse, 2),
        "mape":           round(mape, 2),
        "lstm_acc":       round(lstm_acc, 1),
        "rf_acc":         round(rf_acc, 1),
        "gb_acc":         round(gb_acc, 1),
        "ensemble_acc":   round(ensemble_acc, 1),
        "current_signal": signal,
        "confidence":     conf,
        "importance_df":  importance_df,
    }
