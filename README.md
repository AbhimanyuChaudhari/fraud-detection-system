# Real-Time Fraud Detection System

Stacking ensemble ML system that scores financial transactions in real time.

## Stack
- **Models**: XGBoost + Isolation Forest + LSTM → Meta-learner (stacking ensemble)
- **Streaming**: Apache Kafka
- **API**: FastAPI
- **Database**: PostgreSQL
- **Frontend**: React + Vite
- **Dataset**: IEEE-CIS Fraud Detection (Kaggle)

## Setup

### 1. Get the data
Download from kaggle.com/c/ieee-fraud-detection
Place `train_transaction.csv` and `train_identity.csv` in `backend/data/`

### 2. Start infrastructure
```bash
docker-compose up -d
```

### 3. Train models
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python notebooks/train.py
```

### 4. Start API
```bash
uvicorn app.main:app --reload
```

### 5. Start Kafka stream
```bash
python app/kafka_producer.py
```

### 6. Start frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173
