# FraudSense - Real-Time Fraud Detection System

A production stacking ensemble trained on 590,540 IEEE-CIS transactions that scores financial transactions for fraud in real time. Three models combined by a meta-learner, served via FastAPI, with a live React dashboard showing transactions flowing in with risk scores.

**[Live Dashboard](https://fraud-detection-system-sooty-chi.vercel.app) · [Backend API](https://fraud-detection-system-y0ez.onrender.com/docs)**

---

## What It Does

- **Stacking ensemble** - XGBoost + Isolation Forest + LSTM → Logistic Regression meta-learner
- **0.94 AUC** on held-out test set (118K transactions)
- **Real-time scoring** - POST a transaction, get fraud probability + risk label in under 100ms
- **Threshold tuning** - optimal decision threshold found via precision-recall curve, not default 0.5
- **Live stream simulator** - streams IEEE-CIS transactions through the API at 1.5s intervals
- **PostgreSQL logging** - every scored transaction stored with model breakdown scores
- **Live dashboard** - risk feed, sparkline chart, risk distribution, model confidence bars per transaction

---

## Model Architecture

```
Transaction features (100)
          ↓
┌─────────────────────────────────────────┐
│  XGBoost          Isolation Forest  LSTM │
│  (tabular)        (anomaly)         (sequential) │
│  AUC: 0.94        AUC: 0.69         AUC: 0.79 │
└──────┬───────────────┬───────────────┬──┘
       └───────────────┴───────────────┘
                       ↓
            Meta-learner (Logistic Regression)
            trained on out-of-fold predictions
                       ↓
              Fraud probability 0.0 – 1.0
                       ↓
            Risk label: LOW / MEDIUM / HIGH
            (threshold tuned via P-R curve)
```

### Why Three Models

**XGBoost** is the strongest signal - gradient boosting on tabular data outperforms deep learning for structured fraud detection. `scale_pos_weight` handles the severe class imbalance (3.5% fraud rate).

**Isolation Forest** catches novel fraud patterns the supervised model hasn't seen. It's unsupervised - trained only on the majority class, so it flags anything statistically unusual regardless of whether similar fraud appeared in training data.

**LSTM** adds a sequential perspective. Even with a single timestep (no transaction history per user), the LSTM learns non-linear feature interactions the gradient boosted trees miss. BatchNormalization and class weights handle imbalance.

**Meta-learner** learns the optimal combination of the three scores. XGBoost dominates but the ensemble outperforms any single model.

---

## Feature Engineering

100 features engineered from the raw IEEE-CIS dataset:

| Category | Features |
|---|---|
| Amount | Log transform, z-score, round number flag, decimal part, cents |
| Time | Hour of day, day of week, weekend flag, night flag, morning flag |
| Card | card1, card2, card3, card5, card4 (type), card6 (debit/credit) |
| Email | P_emaildomain, R_emaildomain (encoded) |
| Address | addr1, addr2 |
| Distance | dist1, dist2, log transforms |
| Device | DeviceType, DeviceInfo |
| Identity | Top 15 id_ features from identity table |
| V features | Top 70 V-columns by fraud correlation (from 339 available) |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Training | XGBoost, TensorFlow/Keras, scikit-learn |
| Serving | FastAPI, joblib model loading |
| Stream simulation | Kafka-python producer |
| Database | PostgreSQL, SQLAlchemy |
| Frontend | React, Vite, Recharts |
| Dataset | IEEE-CIS Fraud Detection (Kaggle) |
| Deploy | Render (backend + DB), Vercel (frontend) |

---

## Project Structure

```
fraud-detection/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI endpoints
│   │   ├── predictor.py     # Loads all models, runs ensemble
│   │   ├── features.py      # Real-time feature engineering
│   │   ├── generator.py     # Groq LLM generation
│   │   ├── kafka_producer.py# Stream simulator
│   │   └── database.py      # PostgreSQL transaction log
│   ├── models/              # Saved model files
│   │   ├── xgboost_model.pkl
│   │   ├── isolation_forest.pkl
│   │   ├── lstm_model.keras
│   │   ├── meta_learner.pkl
│   │   ├── scaler.pkl
│   │   └── global_stats.json
│   ├── notebooks/
│   │   └── train.py         # Full training pipeline
│   └── requirements.txt
└── frontend/
    └── src/
        ├── App.jsx
        └── components/
            ├── StatCards.jsx
            ├── TransactionFeed.jsx
            ├── Charts.jsx
            └── KafkaProducer.jsx
```

---

## Training

### Dataset
Download from [Kaggle - IEEE-CIS Fraud Detection](https://www.kaggle.com/c/ieee-fraud-detection).
Place `train_transaction.csv` and `train_identity.csv` in `backend/data/`.

### Run Training

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

python notebooks/train.py
```

Training takes ~20-25 minutes. Output:

```
[1/8] Loading data...       590,540 transactions · 3.50% fraud rate
[2/8] Engineering features  100 features
[3/8] XGBoost               AUC: 0.9406
[4/8] Isolation Forest      AUC: 0.6939
[5/8] LSTM                  AUC: 0.7948
[6/8] Meta-learner          AUC: 0.9412
[7/8] Threshold tuning      Best threshold: 0.31 (F1: 0.72)
✓ All models saved to models/
```

---

## Running Locally

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker Desktop (for PostgreSQL + Kafka)

### Backend

```bash
# Start infrastructure
docker-compose up -d

# Setup Python environment
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start the API (models must be trained first)
uvicorn app.main:app --reload
```

### Stream Simulator

```bash
# In a second terminal
cd backend
python app/kafka_producer.py
# Streams 1 transaction/second from the test set
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/score` | Score a transaction in real time |
| GET | `/transactions/recent` | Recent scored transactions |
| GET | `/stats` | Aggregate stats + sparkline data |

### Example Request

```bash
curl -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{
    "TransactionID": "TX001",
    "TransactionAmt": 15000.00,
    "TransactionDT": 7200,
    "ProductCD": "C",
    "card4": "mastercard",
    "card6": "credit",
    "P_emaildomain": "protonmail.com",
    "R_emaildomain": "yahoo.com",
    "DeviceType": "mobile",
    "isFraud": 0
  }'
```

### Example Response

```json
{
  "transaction_id": "TX001",
  "amount": 15000.0,
  "fraud_probability": 0.847,
  "risk_level": "HIGH",
  "model_scores": {
    "xgboost": 0.821,
    "isolation_forest": 0.743,
    "lstm": 0.612
  },
  "latency_ms": 84.3,
  "timestamp": "2026-04-27T12:00:00"
}
```

---

## Results

| Model | AUC | Notes |
|---|---|---|
| XGBoost | 0.9406 | Primary model, 700 estimators |
| Isolation Forest | 0.6939 | Unsupervised anomaly detection |
| LSTM | 0.7948 | Sequential, BatchNorm + class weights |
| **Ensemble** | **0.9412** | Meta-learner stacking |

Fraud recall at tuned threshold: ~60% (vs 1% at default 0.5)

---

## Deployment

- Backend + PostgreSQL deployed on **Render** (free tier)
- Frontend deployed on **Vercel** (free tier)
- Set `VITE_API_URL` in Vercel environment variables to your Render URL

---

## References

- Dal Pozzolo et al. (2015). *Calibrating Probability with Undersampling for Unbalanced Classification*. CIDM.
- Chen & Guestrin (2016). *XGBoost: A Scalable Tree Boosting System*. KDD.
- Liu et al. (2008). *Isolation Forest*. ICDM.
- IEEE-CIS Fraud Detection Dataset - Vesta Corporation via Kaggle.
