# SMRT Systems Take-Home

AI-driven mobile app with CSV-backed Q&A. This repo includes:

- `server/`: FastAPI + DuckDB backend (Dockerized)
- `frontend/`: React Native (Expo) app [planned next]

Quick start (backend):

```
docker compose up --build
# API at http://localhost:8000
```

Or run locally:

```
cd server
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then refresh the data sources:

```
curl -X POST http://localhost:8000/datasource/refresh
```

Ask a question (Day 1 vertical slice):

```
curl -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"revenue last 30 days","filters":{},"ai_assist":false}'

More examples:

```
# Top products
curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' -d '{"message":"top 5 products"}'

# Orders by customer
curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' -d '{"message":"orders for CID 1001"}'

# Order details by IID
curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' -d '{"message":"order details IID 2001"}'
```

Quick test harness:

```
bash ./test_queries.sh

Frontend (Expo):

```
cd frontend
npm install
# If Expo Go on your device is SDK 53, ensure dependencies match:
npx expo install expo@^53
# Optionally let Expo align React Native and peers:
npx expo install

npm start
```

If you see an SDK mismatch error, upgrade to SDK 53 (as above) or run the iOS Simulator build for SDK 51. Removing the icon asset reference is already handled in app.json.
```
```

Environment:

- `DATA_DIR` (default: `./server/data`) path to CSVs
