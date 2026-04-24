"""
Phase 2 & 3: EDA + Train stacking ensemble
Run this script once to train all models and save them.

Usage:
    cd backend
    python notebooks/train.py
"""

import pandas as pd
import numpy as np
import joblib
import os
import json
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping

import warnings
warnings.filterwarnings('ignore')

MODELS_DIR = Path("../models") if not Path("models").exists() else Path("models")
MODELS_DIR.mkdir(exist_ok=True)

print("=" * 60)
print("FRAUD DETECTION — STACKING ENSEMBLE TRAINING")
print("=" * 60)


# ── 1. Load Data ──────────────────────────────────────────────
print("\n[1/7] Loading data...")
data_dir = Path("../data") if not Path("data").exists() else Path("data")

trans = pd.read_csv(data_dir / "train_transaction.csv")
ident = pd.read_csv(data_dir / "train_identity.csv")
df = trans.merge(ident, on='TransactionID', how='left')

print(f"    Transactions: {len(df):,}")
print(f"    Fraud rate:   {df['isFraud'].mean():.2%}")


# ── 2. Feature Engineering ────────────────────────────────────
print("\n[2/7] Engineering features...")

df['TransactionAmt_log']    = np.log1p(df['TransactionAmt'])
df['TransactionAmt_zscore'] = (df['TransactionAmt'] - df['TransactionAmt'].mean()) / df['TransactionAmt'].std()
df['amt_round']             = (df['TransactionAmt'] % 1 == 0).astype(int)
df['decimal_part']          = df['TransactionAmt'] % 1
df['hour']                  = (df['TransactionDT'] / 3600 % 24).astype(int)
df['day_of_week']           = (df['TransactionDT'] / 86400 % 7).astype(int)
df['is_weekend']            = (df['day_of_week'] >= 5).astype(int)
df['is_night']              = ((df['hour'] >= 22) | (df['hour'] <= 6)).astype(int)

cat_cols = ['ProductCD', 'card4', 'card6', 'P_emaildomain', 'R_emaildomain', 'DeviceType']
for col in cat_cols:
    df[col] = pd.Categorical(df[col]).codes

FEATURE_COLS = [
    'TransactionAmt', 'TransactionAmt_log', 'TransactionAmt_zscore',
    'amt_round', 'decimal_part', 'hour', 'day_of_week', 'is_weekend', 'is_night',
    'ProductCD', 'card4', 'card6', 'P_emaildomain', 'R_emaildomain', 'DeviceType'
]

df[FEATURE_COLS] = df[FEATURE_COLS].fillna(-999)
X = df[FEATURE_COLS].values
y = df['isFraud'].values

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
print(f"    Train: {len(X_train):,} | Test: {len(X_test):,}")

# Save global stats for real-time feature engineering
global_stats = {
    'mean_amt': float(df['TransactionAmt'].mean()),
    'std_amt':  float(df['TransactionAmt'].std()),
    'feature_cols': FEATURE_COLS
}
with open(MODELS_DIR / "global_stats.json", "w") as f:
    json.dump(global_stats, f)
print("    Global stats saved")


# ── 3. XGBoost ────────────────────────────────────────────────
print("\n[3/7] Training XGBoost...")

scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
xgb_model = xgb.XGBClassifier(
    n_estimators=500,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=scale_pos_weight,
    use_label_encoder=False,
    eval_metric='auc',
    random_state=42,
    n_jobs=-1
)
xgb_model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=100)
xgb_probs = xgb_model.predict_proba(X_test)[:, 1]
xgb_auc = roc_auc_score(y_test, xgb_probs)
print(f"    XGBoost AUC: {xgb_auc:.4f}")
joblib.dump(xgb_model, MODELS_DIR / "xgboost_model.pkl")


# ── 4. Isolation Forest ───────────────────────────────────────
print("\n[4/7] Training Isolation Forest...")

iso_forest = IsolationForest(n_estimators=200, contamination=0.035, random_state=42, n_jobs=-1)
iso_forest.fit(X_train)
iso_scores_raw = iso_forest.decision_function(X_test)
# Convert to probability-like score (higher = more anomalous)
iso_probs = 1 - (iso_scores_raw - iso_scores_raw.min()) / (iso_scores_raw.max() - iso_scores_raw.min())
iso_auc = roc_auc_score(y_test, iso_probs)
print(f"    Isolation Forest AUC: {iso_auc:.4f}")
joblib.dump(iso_forest, MODELS_DIR / "isolation_forest.pkl")


# ── 5. LSTM ───────────────────────────────────────────────────
print("\n[5/7] Training LSTM...")

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.transform(X_test)
joblib.dump(scaler, MODELS_DIR / "scaler.pkl")

# Reshape for LSTM: (samples, timesteps, features)
X_train_lstm = X_train_scaled.reshape(X_train_scaled.shape[0], 1, X_train_scaled.shape[1])
X_test_lstm  = X_test_scaled.reshape(X_test_scaled.shape[0], 1, X_test_scaled.shape[1])

lstm_model = Sequential([
    LSTM(64, input_shape=(1, X_train_scaled.shape[1]), return_sequences=False),
    Dropout(0.3),
    Dense(32, activation='relu'),
    Dropout(0.2),
    Dense(1, activation='sigmoid')
])
lstm_model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['auc'])
lstm_model.fit(
    X_train_lstm, y_train,
    epochs=20, batch_size=2048,
    validation_split=0.1,
    callbacks=[EarlyStopping(patience=3, restore_best_weights=True)],
    verbose=1
)
lstm_probs = lstm_model.predict(X_test_lstm).flatten()
lstm_auc = roc_auc_score(y_test, lstm_probs)
print(f"    LSTM AUC: {lstm_auc:.4f}")
lstm_model.save(MODELS_DIR / "lstm_model.keras")


# ── 6. Meta-learner (stacking) ────────────────────────────────
print("\n[6/7] Training meta-learner...")

# Stack all three model scores as features for meta-learner
meta_X = np.column_stack([xgb_probs, iso_probs, lstm_probs])
meta_learner = LogisticRegression(random_state=42)
meta_learner.fit(meta_X, y_test)
meta_probs = meta_learner.predict_proba(meta_X)[:, 1]
meta_auc = roc_auc_score(y_test, meta_probs)
print(f"    Meta-learner AUC: {meta_auc:.4f}")
joblib.dump(meta_learner, MODELS_DIR / "meta_learner.pkl")


# ── 7. Final Report ───────────────────────────────────────────
print("\n[7/7] Final results:")
print(f"    XGBoost AUC:       {xgb_auc:.4f}")
print(f"    Isolation Forest:  {iso_auc:.4f}")
print(f"    LSTM AUC:          {lstm_auc:.4f}")
print(f"    Ensemble AUC:      {meta_auc:.4f}  ← final model")

threshold = 0.5
preds = (meta_probs >= threshold).astype(int)
print(f"\nClassification Report (threshold={threshold}):")
print(classification_report(y_test, preds, target_names=['Legit', 'Fraud']))

print("\n✓ All models saved to models/")
print("  Next: run the FastAPI server")
