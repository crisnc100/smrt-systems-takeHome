# SMRT Mobile – Runbook & Progress

This document is a concise, user‑friendly record of what’s built, how to run it, and what to do next. It also captures key technical decisions and known pitfalls so reviewers can evaluate quickly.

## Overview
- Purpose: Chat + Reports app that answers questions grounded strictly in CSV data (Customer, Inventory, Detail, Pricelist) with visible evidence.
- Stack:
  - Frontend: React Native (Expo, TypeScript) in `frontend/`
  - Backend: FastAPI + DuckDB in `server/` (Dockerized)
- Trust & Safety: Rule‑based intents → parameterized SQL; validators (SELECT‑only, whitelist, LIMIT, timeout); evidence returned with every answer.

## Architecture
- Frontend (Expo Dev Client recommended)
  - Screens: Chat, Reports, Settings
  - Components: AnswerCard (with Evidence), Chart (Victory)
  - Networking: Base URL stored in AsyncStorage; user‑configurable in Settings
- Backend (FastAPI)
  - Data engine: DuckDB over CSV/Parquet; CSV → Parquet cache on refresh
  - Intents: revenue_by_period, orders_by_customer, top_products, order_details
  - Reports: revenue_by_month, top_customers
  - Validators: SELECT‑only, column whitelist, LIMIT cap, 2s timeout
  - Evidence: executed SQL, tables used, rows scanned, sample rows

## What’s Implemented
- Endpoints
  - GET `/health` → { status, data_dir, service }
  - POST `/datasource/refresh` → builds Parquet cache, creates views, returns table counts
  - POST `/chat` → Q&A with intents, validations, evidence and follow‑ups
  - POST `/report` → revenue_by_month, top_customers (series + summary + SQL)
- Frontend
  - Chat: prompt input, suggestion chips, AnswerCard, collapsible Evidence, follow‑up chips
  - Reports: segmented toggle, fetch /report, render Victory chart + summary
  - Settings: API base URL, “Refresh Data” button
- Dev Quality
  - LRU cache for queries; cleared on refresh
  - Consistent error shape: { error, suggestion }
  - Dockerfile + docker‑compose for backend
  - Test harness: `./test_queries.sh`

## How To Run
### Backend
- Docker (recommended)
  - From repo root: `docker compose up --build`
  - API at `http://localhost:8000`
- Local (Python 3.11+)
  - `cd server`
  - `python -m venv .venv && source .venv/bin/activate` (Windows: `.venv\Scripts\activate`)
  - `pip install -r requirements.txt`
  - `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- Refresh data: `curl -X POST http://localhost:8000/datasource/refresh`

### Frontend
- Dev Client (stable, recommended)
  - `cd frontend`
  - Install deps: `npm install` (and `npx expo install` if prompted)
  - Build dev client (Android): `eas build --profile development --platform android`
  - Install APK on device/emulator, then: `npm run start:dev`
  - iOS (Mac): `eas build --profile development --platform ios` (requires Apple dev account)
- Expo Web (quick local)
  - `cd frontend && npm run web`

### Networking (Devices)
- iOS physical device: use your PC’s LAN IP
  - Settings tab → API URL: `http://<YOUR_PC_LAN_IP>:8000` (e.g., `http://172.16.21.155:8000`)
  - Safari test: open `http://<YOUR_PC_LAN_IP>:8000/health`
  - Windows Firewall: allow inbound on port 8000 (or allow Python)
- Android emulator: `http://10.0.2.2:8000`
- iOS simulator: `http://localhost:8000`

## Request/Response Shapes
### POST /chat
Request:
```
{
  "message": "revenue last 30 days",
  "filters": {"date_range": {"from":"2024-08-01","to":"2024-08-31"}},
  "ai_assist": false
}
```
Response (success):
```
{
  "answer_text": "Revenue from 2024-08-01 to 2024-08-31: $X.",
  "tables_used": ["Inventory"],
  "sql": "SELECT ...",
  "rows_scanned": 1234,
  "data_snippets": [{"date":"2024-08-12","revenue":4211.22}],
  "validations": [{"name":"non_empty_result","status":"pass"}],
  "confidence": 0.92,
  "follow_ups": ["Top products last 30 days"],
  "chart_suggestion": {"type":"line","x":"order_date","y":"revenue"}
}
```
Response (guard or empty):
```
{ "error": "Cannot answer: ...", "suggestion": "Try ..." }
```

### POST /report
Requests:
```
{ "type": "revenue_by_month", "filters": {"date_range": {"from":"2024-01-01","to":"2024-12-31"}} }
{ "type": "top_customers", "filters": {"k": 5} }
```
Response:
```
{
  "summary_text": "...",
  "tables_used": ["Inventory"],
  "sql": ["SELECT ..."],
  "charts": [
    {"type":"bar","series":[{"name":"Revenue","data":[["2024-01", 10000], ["2024-02", 12000]]]}]
  ]
}
```

## Known Issues & Fixes
- Expo Go SDK mismatch → use Expo SDK 53 and `npx expo install` to align.
- Metro importLocationsPlugin missing → pin React Native (0.76.x) and Metro (^0.80), or `npx expo install`.
- Expo Go native crash (non‑std C++ exception) → use Dev Client (EAS) or web.
- “Network request failed” on device → use PC LAN IP (not localhost), allow firewall, or use Android `adb reverse`.
- DuckDB parser error near `?` → fixed by inlining file path literals in `read_csv_auto`/`read_parquet` and `COPY`.
- CSV header parsing → `HEADER=TRUE` in DuckDB calls.

## Developer Shortcuts
- Test backend quickly: `bash ./test_queries.sh`
- Data refresh: `curl -X POST http://localhost:8000/datasource/refresh`
- Health: `curl http://localhost:8000/health`

## Next Actions (High‑Value)
1) Chat polish
- Ask→SQL toggle in UI (sanitized SQL with copy button)
- “How computed” trace (validators applied, filters used)
- Data quality badges (orphan joins %, negative prices/outliers)

2) Reports upgrades
- Compare toggle (period‑over‑period deltas)
- Export CSV of current series
- Add Top Products report (bar) and Revenue trend (line)

3) Performance & Scale
- Precompute daily revenue (cache)
- Predicate pushdown everywhere and select only needed columns
- Validate with larger CSVs (100k–1M rows)

4) Docs & Demo
- Update README with Dev Client steps and LAN IP guidance
- Record Loom walkthrough (first run, Chat, Evidence, Reports)

## Version Notes
- Frontend: Expo SDK 53 dev client (or 52 depending on local state), React Native 0.76.x
- Backend: Python 3.11, FastAPI, DuckDB 1.0+

## File Map (Key)
- `frontend/` – Expo app (Chat, Reports, Settings)
- `server/` – FastAPI backend (routers, engine, validators)
- `docker-compose.yml` – one‑command backend
- `docs/Approach.md` – overall approach
- `docs/Runbook.md` – this document

---
If anything blocks your run, start by checking:
- Device can reach `http://<PC_LAN_IP>:8000/health`
- `POST /datasource/refresh` returns counts
- Chat answers include SQL + rows scanned
- Reports render a bar chart without errors

