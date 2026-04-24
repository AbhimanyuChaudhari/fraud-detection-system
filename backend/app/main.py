import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import threading

from app.database  import init_db, get_db, Transaction
from app.predictor import get_predictor
from app.features  import engineer_single

load_dotenv()

app = FastAPI(title="Fraud Detection API", version="1.0.0")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"],
    allow_methods=["*"], allow_headers=["*"]
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": str(exc)})

@app.on_event("startup")
def startup():
    init_db()
    # Warm up models
    threading.Thread(target=get_predictor, daemon=True).start()


# ── Models ────────────────────────────────────────────────────

class TransactionIn(BaseModel):
    TransactionID:  str
    TransactionAmt: float
    TransactionDT:  float
    ProductCD:      str = "W"
    card4:          str = "visa"
    card6:          str = "debit"
    P_emaildomain:  str = "gmail.com"
    R_emaildomain:  str = "gmail.com"
    DeviceType:     str = "desktop"
    isFraud:        int = 0


# ── Endpoints ─────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "running", "service": "Fraud Detection API"}


@app.post("/score")
def score_transaction(tx: TransactionIn, db: Session = Depends(get_db)):
    """Score a single transaction in real time."""
    predictor = get_predictor()

    # Engineer features
    features = engineer_single(tx.dict(), predictor.global_stats)

    # Get prediction
    result = predictor.predict(features)

    # Store in DB
    record = Transaction(
        transaction_id    = tx.TransactionID,
        amount            = tx.TransactionAmt,
        product_cd        = tx.ProductCD,
        card4             = tx.card4,
        device_type       = tx.DeviceType,
        fraud_probability = result["fraud_probability"],
        risk_level        = result["risk_level"],
        xgb_score         = result["model_scores"]["xgboost"],
        iso_score         = result["model_scores"]["isolation_forest"],
        lstm_score        = result["model_scores"]["lstm"],
        latency_ms        = result["latency_ms"],
        is_actual_fraud   = bool(tx.isFraud)
    )
    db.add(record)
    db.commit()

    return {
        "transaction_id":   tx.TransactionID,
        "amount":           tx.TransactionAmt,
        "product_cd":       tx.ProductCD,
        **result,
        "timestamp":        datetime.utcnow().isoformat()
    }


@app.get("/transactions/recent")
def get_recent(limit: int = 50, db: Session = Depends(get_db)):
    """Get most recent scored transactions for live feed."""
    rows = db.query(Transaction).order_by(desc(Transaction.created_at)).limit(limit).all()
    return [
        {
            "id":               r.id,
            "transaction_id":   r.transaction_id,
            "amount":           r.amount,
            "product_cd":       r.product_cd,
            "risk_level":       r.risk_level,
            "fraud_probability":r.fraud_probability,
            "xgb_score":        r.xgb_score,
            "iso_score":        r.iso_score,
            "lstm_score":       r.lstm_score,
            "latency_ms":       r.latency_ms,
            "is_actual_fraud":  r.is_actual_fraud,
            "timestamp":        r.created_at.isoformat()
        }
        for r in rows
    ]


@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Aggregate stats for the dashboard."""
    total      = db.query(func.count(Transaction.id)).scalar() or 0
    flagged    = db.query(func.count(Transaction.id)).filter(Transaction.risk_level == "HIGH").scalar() or 0
    avg_lat    = db.query(func.avg(Transaction.latency_ms)).scalar() or 0
    fraud_rate = round((flagged / total * 100), 2) if total else 0

    risk_counts = {
        "LOW":    db.query(func.count(Transaction.id)).filter(Transaction.risk_level == "LOW").scalar() or 0,
        "MEDIUM": db.query(func.count(Transaction.id)).filter(Transaction.risk_level == "MEDIUM").scalar() or 0,
        "HIGH":   db.query(func.count(Transaction.id)).filter(Transaction.risk_level == "HIGH").scalar() or 0,
    }

    # Last 60 transactions for sparkline
    recent = db.query(Transaction).order_by(desc(Transaction.created_at)).limit(60).all()
    sparkline = [round(r.fraud_probability, 3) for r in reversed(recent)]

    return {
        "total_scored":  total,
        "high_risk":     flagged,
        "fraud_rate":    fraud_rate,
        "avg_latency_ms":round(avg_lat, 2),
        "risk_counts":   risk_counts,
        "sparkline":     sparkline
    }
