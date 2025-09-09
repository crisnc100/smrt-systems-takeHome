# Approach: Data-Grounded Q&A

This project answers questions strictly grounded in CSV data using DuckDB over CSV/Parquet. The mobile app provides a chat interface with trust features; the backend plans, validates, and executes parameterized queries.

Core principles:
- Deterministic planner first (rule-based intents → parameterized SQL)
- SELECT-only, whitelisted tables, bounded rows/timeouts (progressively added)
- Evidence-first responses: executed SQL, tables used, rows scanned, sample rows
- Scale path: CSV → Parquet cache, predicate pushdown, column selection, LRU

Day 1 vertical slice:
- Endpoint `/chat` supports `revenue_by_period` with date parsing and evidence
- `/datasource/refresh` builds Parquet cache and creates views over CSV/Parquet

Next steps:
- Add more intents, validators, and reports; wire Expo app

