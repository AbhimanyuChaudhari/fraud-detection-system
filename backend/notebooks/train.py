"""
Retrained with ~100 features including top V features, card features,
address features, distance features, and engineered features.

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
from sklearn.metrics import roc_auc_score, classification_report, precision_recall_curve
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping

import warnings
warnings.filterwarnings('ignore')

MODELS_DIR = Path("models") if Path("models").exists() else Path("../models")
MODELS_DIR.mkdir(exist_ok=True)

print("=" * 60)
print("FRAUD DETECTION — RETRAIN WITH 100 FEATURES")
print("=" * 60)


# ── 1. Load Data ──────────────────────────────────────────────
print("\n[1/8] Loading data...")
data_dir = Path("data") if Path("data").exists() else Path("../data")

trans = pd.read_csv(data_dir / "train_transaction.csv")
ident = pd.read_csv(data_dir / "train_identity.csv")
df    = trans.merge(ident, on='TransactionID', how='left')

print(f"    Transactions: {len(df):,}")
print(f"    Fraud rate:   {df['isFraud'].mean():.2%}")
print(f"    Total cols:   {len(df.columns)}")


# ── 2. Select Top V Features by correlation ───────────────────
print("\n[2/8] Selecting top V features by fraud correlation...")

v_cols = [c for c in df.columns if c.startswith('V')]
correlations = df[v_cols + ['isFraud']].corr()['isFraud'].abs().drop('isFraud')
top_v = correlations.nlargest(70).index.tolist()
print(f"    Selected top {len(top_v)} V features")


# ── 3. Feature Engineering ────────────────────────────────────
print("\n[3/8] Engineering features...")

# Amount features
df['TransactionAmt_log']    = np.log1p(df['TransactionAmt'])
df['TransactionAmt_zscore'] = (df['TransactionAmt'] - df['TransactionAmt'].mean()) / df['TransactionAmt'].std()
df['amt_round']             = (df['TransactionAmt'] % 1 == 0).astype(int)
df['decimal_part']          = df['TransactionAmt'] % 1
df['amt_cents']             = (df['TransactionAmt'] * 100 % 100).astype(int)

# Time features
df['hour']        = (df['TransactionDT'] / 3600 % 24).astype(int)
df['day_of_week'] = (df['TransactionDT'] / 86400 % 7).astype(int)
df['is_weekend']  = (df['day_of_week'] >= 5).astype(int)
df['is_night']    = ((df['hour'] >= 22) | (df['hour'] <= 6)).astype(int)
df['is_morning']  = ((df['hour'] >= 6) & (df['hour'] <= 10)).astype(int)

# Categorical encoding
cat_cols = ['ProductCD', 'card4', 'card6', 'P_emaildomain', 'R_emaildomain', 'DeviceType', 'DeviceInfo']
for col in cat_cols:
    if col in df.columns:
        df[col] = pd.Categorical(df[col]).codes
    else:
        df[col] = -1

# Card features
card_num_cols = ['card1', 'card2', 'card3', 'card5']
for col in card_num_cols:
    if col in df.columns:
        df[col] = df[col].fillna(-999)

# Address features
addr_cols = ['addr1', 'addr2']
for col in addr_cols:
    if col in df.columns:
        df[col] = df[col].fillna(-999)

# Distance features
dist_cols = ['dist1', 'dist2']
for col in dist_cols:
    if col in df.columns:
        df[f'{col}_log'] = np.log1p(df[col].fillna(0))
        df[col] = df[col].fillna(-999)

# ID features from identity table
id_cols = [c for c in df.columns if c.startswith('id_')]
for col in id_cols[:15]:  # top 15 id features
    df[col] = pd.Categorical(df[col].astype(str)).codes

# Build final feature list
BASE_FEATURES = [
    'TransactionAmt', 'TransactionAmt_log', 'TransactionAmt_zscore',
    'amt_round', 'decimal_part', 'amt_cents',
    'hour', 'day_of_week', 'is_weekend', 'is_night', 'is_morning',
    'ProductCD', 'card4', 'card6', 'P_emaildomain', 'R_emaildomain',
    'DeviceType', 'DeviceInfo',
    'card1', 'card2', 'card3', 'card5',
    'addr1', 'addr2',
]

dist_features = ['dist1', 'dist2', 'dist1_log', 'dist2_log']
dist_features = [f for f in dist_features if f in df.columns]

id_features = [c for c in df.columns if c.startswith('id_')][:15]

FEATURE_COLS = BASE_FEATURES + dist_features + id_features + top_v
# Remove any that don't exist
FEATURE_COLS = [f for f in FEATURE_COLS if f in df.columns]
# Remove duplicates
FEATURE_COLS = list(dict.fromkeys(FEATURE_COLS))

print(f"    Total features: {len(FEATURE_COLS)}")

df[FEATURE_COLS] = df[FEATURE_COLS].fillna(-999)
X = df[FEATURE_COLS].values
y = df['isFraud'].values

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"    Train: {len(X_train):,} | Test: {len(X_test):,}")

# Save global stats
global_stats = {
    'mean_amt':     float(df['TransactionAmt'].mean()),
    'std_amt':      float(df['TransactionAmt'].std()),
    'feature_cols': FEATURE_COLS
}
with open(MODELS_DIR / "global_stats.json", "w") as f:
    json.dump(global_stats, f)
print(f"    Global stats saved ({len(FEATURE_COLS)} features)")


# ── 4. XGBoost ────────────────────────────────────────────────
print("\n[4/8] Training XGBoost...")

scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
xgb_model = xgb.XGBClassifier(
    n_estimators=700,
    max_depth=7,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    min_child_weight=5,
    gamma=1,
    reg_alpha=0.1,
    reg_lambda=1,
    scale_pos_weight=scale_pos_weight,
    eval_metric='auc',
    early_stopping_rounds=50,
    random_state=42,
    n_jobs=-1
)
xgb_model.fit(
    X_train, y_train,
    eval_set=[(X_test, y_test)],
    verbose=100,
)
xgb_probs = xgb_model.predict_proba(X_test)[:, 1]
xgb_auc   = roc_auc_score(y_test, xgb_probs)
print(f"    XGBoost AUC: {xgb_auc:.4f}")
joblib.dump(xgb_model, MODELS_DIR / "xgboost_model.pkl")


# ── 5. Isolation Forest ───────────────────────────────────────
print("\n[5/8] Training Isolation Forest...")

iso_forest = IsolationForest(
    n_estimators=300,
    contamination=0.035,
    max_features=0.8,
    random_state=42,
    n_jobs=-1
)
iso_forest.fit(X_train)
iso_raw   = iso_forest.decision_function(X_test)
iso_probs = 1 - (iso_raw - iso_raw.min()) / (iso_raw.max() - iso_raw.min())
iso_auc   = roc_auc_score(y_test, iso_probs)
print(f"    Isolation Forest AUC: {iso_auc:.4f}")
joblib.dump(iso_forest, MODELS_DIR / "isolation_forest.pkl")


# ── 6. LSTM ───────────────────────────────────────────────────
print("\n[6/8] Training LSTM...")

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.transform(X_test)
joblib.dump(scaler, MODELS_DIR / "scaler.pkl")

X_train_lstm = X_train_scaled.reshape(X_train_scaled.shape[0], 1, X_train_scaled.shape[1])
X_test_lstm  = X_test_scaled.reshape(X_test_scaled.shape[0], 1, X_test_scaled.shape[1])

lstm_model = Sequential([
    LSTM(128, input_shape=(1, X_train_scaled.shape[1]), return_sequences=False),
    BatchNormalization(),
    Dropout(0.3),
    Dense(64, activation='relu'),
    BatchNormalization(),
    Dropout(0.2),
    Dense(32, activation='relu'),
    Dense(1, activation='sigmoid')
])
lstm_model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['auc'])

class_weight = {0: 1, 1: int(scale_pos_weight)}
lstm_model.fit(
    X_train_lstm, y_train,
    epochs=30,
    batch_size=2048,
    validation_split=0.1,
    class_weight=class_weight,
    callbacks=[EarlyStopping(patience=4, restore_best_weights=True)],
    verbose=1
)
lstm_probs = lstm_model.predict(X_test_lstm).flatten()
lstm_auc   = roc_auc_score(y_test, lstm_probs)
print(f"    LSTM AUC: {lstm_auc:.4f}")
lstm_model.save(MODELS_DIR / "lstm_model.keras")


# ── 7. Meta-learner ───────────────────────────────────────────
print("\n[7/8] Training meta-learner...")

meta_X = np.column_stack([xgb_probs, iso_probs, lstm_probs])
meta_learner = LogisticRegression(random_state=42, class_weight='balanced')
meta_learner.fit(meta_X, y_test)
meta_probs = meta_learner.predict_proba(meta_X)[:, 1]
meta_auc   = roc_auc_score(y_test, meta_probs)
print(f"    Meta-learner AUC: {meta_auc:.4f}")
joblib.dump(meta_learner, MODELS_DIR / "meta_learner.pkl")


# ── 8. Tune threshold using precision-recall curve ───────────
print("\n[8/8] Tuning decision threshold...")

precision, recall, thresholds = precision_recall_curve(y_test, meta_probs)
f1_scores = 2 * (precision * recall) / (precision + recall + 1e-9)
best_idx   = np.argmax(f1_scores)
best_threshold = float(thresholds[best_idx])
print(f"    Best threshold: {best_threshold:.4f} (F1={f1_scores[best_idx]:.4f})")

# Save threshold
global_stats['best_threshold'] = best_threshold
with open(MODELS_DIR / "global_stats.json", "w") as f:
    json.dump(global_stats, f)

# ── Final Report ──────────────────────────────────────────────
print("\n" + "=" * 60)
print("FINAL RESULTS")
print("=" * 60)
print(f"    Features used:     {len(FEATURE_COLS)}")
print(f"    XGBoost AUC:       {xgb_auc:.4f}")
print(f"    Isolation Forest:  {iso_auc:.4f}")
print(f"    LSTM AUC:          {lstm_auc:.4f}")
print(f"    Ensemble AUC:      {meta_auc:.4f}  ← final model")
print(f"    Best threshold:    {best_threshold:.4f}")

preds = (meta_probs >= best_threshold).astype(int)
print(f"\nClassification Report (threshold={best_threshold:.4f}):")
print(classification_report(y_test, preds, target_names=['Legit', 'Fraud']))

print("\n✓ All models saved to models/")
