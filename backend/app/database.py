import os
from sqlalchemy import create_engine, Column, Float, String, Integer, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://fraud:fraud123@localhost:5433/frauddb")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Transaction(Base):
    __tablename__ = "transactions"

    id                  = Column(Integer, primary_key=True, index=True)
    transaction_id      = Column(String, index=True)
    amount              = Column(Float)
    product_cd          = Column(String, nullable=True)
    card4               = Column(String, nullable=True)
    device_type         = Column(String, nullable=True)
    fraud_probability   = Column(Float)
    risk_level          = Column(String)
    xgb_score           = Column(Float)
    iso_score           = Column(Float)
    lstm_score          = Column(Float)
    latency_ms          = Column(Float)
    is_actual_fraud     = Column(Boolean, nullable=True)
    created_at          = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()