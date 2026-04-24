"""
Simulates real-time transaction stream by reading IEEE-CIS test data
and producing to Kafka one transaction per second.

Usage:
    cd backend
    python app/kafka_producer.py
"""

import json
import time
import pandas as pd
import numpy as np
from kafka import KafkaProducer
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

KAFKA_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC         = os.environ.get("KAFKA_TOPIC", "transactions")
DELAY_SECONDS = 1.0  # one transaction per second

def load_transactions():
    data_dir = Path("./data")
    print("Loading transactions...")
    trans = pd.read_csv(data_dir / "train_transaction.csv")
    ident = pd.read_csv(data_dir / "train_identity.csv")
    df    = trans.merge(ident, on='TransactionID', how='left')

    # Use last 20% as our "live" stream (same split as training)
    df = df.tail(int(len(df) * 0.2)).reset_index(drop=True)
    print(f"Loaded {len(df):,} transactions to stream")
    return df

def row_to_dict(row):
    """Convert a DataFrame row to a clean JSON-serializable dict."""
    return {
        "TransactionID":  str(row.get('TransactionID', '')),
        "TransactionAmt": float(row.get('TransactionAmt', 0)),
        "TransactionDT":  float(row.get('TransactionDT', 0)),
        "ProductCD":      str(row.get('ProductCD', 'W')),
        "card4":          str(row.get('card4', 'visa')),
        "card6":          str(row.get('card6', 'debit')),
        "P_emaildomain":  str(row.get('P_emaildomain', 'gmail.com')),
        "R_emaildomain":  str(row.get('R_emaildomain', 'gmail.com')),
        "DeviceType":     str(row.get('DeviceType', 'desktop')),
        "isFraud":        int(row.get('isFraud', 0)),
    }

def main():
    df = load_transactions()
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    print(f"Streaming to Kafka topic '{TOPIC}' at {1/DELAY_SECONDS:.1f} tx/sec...")
    print("Press Ctrl+C to stop\n")

    for i, row in df.iterrows():
        msg = row_to_dict(row)
        producer.send(TOPIC, msg)
        label = "FRAUD" if msg['isFraud'] else "legit"
        print(f"[{i}] ${msg['TransactionAmt']:.2f} | {msg['ProductCD']} | {label}")
        time.sleep(DELAY_SECONDS)

    producer.flush()
    print("Stream complete.")

if __name__ == "__main__":
    main()
