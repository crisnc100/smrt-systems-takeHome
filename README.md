# SMRT Systems Query Intelligence Platform

AI-driven mobile app with trustworthy CSV-backed Q&A. Evidence-based answers with no hallucinations.

## Features

- 🎯 **Natural Language Queries**: Ask questions in plain English
- 🔍 **Evidence-Based Answers**: Every response includes SQL, data sources, and sample results
- 📊 **Visual Reports**: Charts and graphs for data visualization
- ⚡ **Scalable Architecture**: Handles datasets from 100 to 10M+ rows
- 🛡️ **SQL Injection Protection**: Safe, validated queries only
- 📱 **Mobile-First Design**: React Native app for iOS/Android

## Quick Start

### Backend (FastAPI + DuckDB)

**Docker:**
```bash
docker compose up --build
# API at http://localhost:8000
```

**Local Development:**
```bash
cd server
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Initialize Data:**
```bash
curl -X POST http://localhost:8000/datasource/refresh
```

### Frontend (React Native + Expo)

```bash
cd frontend
npm install
npx expo install expo-clipboard  # for Copy SQL button
npx expo start
# or with a dev client build
# npx expo start --dev-client
```

Configure backend URL in app settings. Tips:
- iOS Simulator: `http://localhost:8000`
- Android Emulator: `http://10.0.2.2:8000`
- Physical device on same Wi‑Fi: `http://<your-computer-LAN-IP>:8000`

## Example Queries

```bash
# Revenue analysis
curl -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"revenue last 30 days"}'

# Top products
curl -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"top 5 products"}'

# Customer orders
curl -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"orders for CID 1001"}'

# Order details
curl -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"order details IID 2001"}'
```

## Testing

**Run Test Suite:**
```bash
cd server
python run_tests.py
# Or use the test script:
bash test_query_logic.sh
```

**Generate Large Test Data:**
```bash
python generate_large_dataset.py 1000  # ~100k orders
```

**Manual Testing:**
See `server/tests/MANUAL_TEST_CHECKLIST.md`

## Architecture

- **Intent Detection**: Pattern-based natural language understanding
- **SQL Generation**: Template-based safe query construction
- **Query Optimization**: Sampling, caching, and partitioning for scale
- **Evidence Bundle**: Returns SQL, source tables, row counts, sample data
- **Confidence Scoring**: Data quality metrics inform trust level

See `server/Approach.md` for detailed technical approach.

## Environment Variables

- `DATA_DIR`: Path to CSV files (default: `./server/data`)
