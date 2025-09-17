# Progress Update - SMRT Systems Take-Home

## Date: September, 2025

## What We Accomplished Today

### 1. Test Data Integration ✅
**Goal:** Use SMRT Systems' provided test dataset instead of generated mock data for fair evaluation across all candidates.

**What We Did:**
- **Updated data directory path logic** to prioritize `test_data/` folder over generated data
- **Created column mappings** for the interview dataset which has different column names:
  - Customer: Mapped `FNAME1 + LNAME` → `name`, `INDATE` → `order_date`
  - Inventory: Mapped `SUBTOTAL` → `order_total`, `INDATE` → `order_date`
  - Detail: Mapped `Item_ID` → `detail_id`, `item_count` → `quantity`
  - Pricelist: Mapped `item_id` → `price_table_item_id`, `name` → `item_name`
- **Successfully loaded** 53 customers, 334 inventory records, 334 detail records, 337 pricelist items
- **Verified queries work** with the test data (e.g., "revenue last 30 days" returns $3,537.55)

**Technical Changes:**
- Modified `/server/app/engine/duck.py` to handle both user-uploaded data and test data
- Added special view creation logic for interview dataset schema differences
- Configured `.env` file for OpenRouter API key storage

### 2. Dual-Mode Toggle & API Plumbing ✅
**Goal:** Respond to reviewer feedback by wiring a Classic vs AI toggle end-to-end.

**What We Did:**
- Added a **segmented toggle in Settings** that persists the preferred query mode via AsyncStorage
- Updated the **chat UI** to display the active mode, include it in every request, and tag responses/cards accordingly
- Extended the **frontend API client** so `/chat` calls always send `query_mode` and stash the returned mode flag
- Expanded the **FastAPI chat endpoint** to accept the mode, annotate all responses, and route AI requests through a placeholder `llm_query` engine (ready for real LLM integration)

**Technical Changes:**
- `frontend/lib/api.ts`, `frontend/screens/SettingsScreen.tsx`, `frontend/screens/ChatScreen.tsx`, `frontend/components/AnswerCard.tsx`
- `server/app/routers/chat.py` now branches on `query_mode`
- New `server/app/engine/llm_query.py` stub captures AI-mode requests for forthcoming LLM integration

### 3. AI Smart Mode Backend 🚧
**Goal:** Stand up the first working slice of the LLM-powered flow (prompting, OpenRouter call, SQL validation, and execution).

**What We Did:**
- Created `schema_context.py` with a structured schema summary and reusable system prompt
- Replaced the placeholder in `llm_query.py` with a production-ready OpenRouter client (primary + fallback models, JSON-only responses, friendly error messages)
- Added `sql_validator.py` to enforce SELECT-only statements, strip dangerous keywords, whitelist tables, and auto-inject `LIMIT`
- Updated `chat.py` to run the AI branch end-to-end: generate SQL, validate it, execute against DuckDB, and surface the response as a `ChatResponse`
- Extended unit tests (`test_queries.py`) to cover the validator behaviour

**Technical Changes:**
- `server/app/engine/schema_context.py`, `server/app/engine/llm_query.py`, `server/app/engine/sql_validator.py`
- `server/app/routers/chat.py`
- `server/tests/test_queries.py`
- Added `httpx` to backend requirements for OpenRouter access

### 4. AI Mode UX Refinements 🎨
**Goal:** Smooth out the end-to-end experience now that the AI pipeline works. (*In progress*)

**What’s Done:**
- Chat header + answer cards display which mode handled each response so users always know Classic vs AI Smart
- Follow-up suggestions are capped and deduplicated to prevent overload when the LLM returns lots of ideas
- Added AI sample row previews so users can see concrete evidence from the generated SQL

**TODO:**
- Reword quick-suggestion chips so they read as examples instead of “only supported phrases”
- Surface a short inline tip explaining the difference between Classic and AI Smart modes
- Add AI-mode evidence snippets (sample rows) once the LLM output format is exercised with real data

## Current Status

### Working Features:
- ✅ App loads and queries SMRT Systems' test data correctly
- ✅ Pattern-matching queries (Classic Mode) fully functional
- ✅ Column mappings handle schema differences transparently
- ✅ Server runs on port 8001 with test data

### Environment Setup:
- Python virtual environment created at `/server/venv/`
- Dependencies installed (FastAPI, DuckDB, etc.)
- OpenRouter API key configured in `/server/.env`

## Testing Required

### Immediate Testing:
1. **Full query test suite** with the test data:
   - Revenue queries (by month, quarter, year)
   - Customer queries (top customers, specific customer orders)
   - Product queries (top products, inventory details)
   - Complex joins across all tables

2. **Edge cases:**
   - Empty result queries
   - Invalid date ranges
   - Non-existent customer/product IDs

3. **Performance testing:**
   - Response times with 334 orders
   - Memory usage with current dataset

## Next Steps to Complete

### Priority 1: AI/LLM Mode Stabilisation (Tomorrow)
1. **Result Verification & Snippets**
   - Add lightweight evidence sampling for AI responses
   - Tune `confidence` heuristics once we observe real outputs

2. **End-to-End Manual Run**
    - Exercise the AI mode with a real OpenRouter key ✅ (e.g., “Show revenue by month for this year” returns rows with sample evidence)
    - Capture latency + cost notes for the write-up/demo

3. **Prompt/Validator Tuning**
   - Expand column allowlists if new questions surface additional fields
   - Record any tricky prompts to document best practices

4. **Frontend polish**
   - [x] Refresh suggestion chip copy + add a one-line “mode info” callout in chat/settings
   - [x] Surface AI-mode evidence snippets; monitor layout with real data

### Priority 2: Final Deliverables (Wednesday)
1. **Complete Testing**
   - Test both Classic and AI modes
   - Verify no hallucinations in AI mode
   - Ensure seamless mode switching

2. **Documentation Updates**
   - Update APPROACH.md with dual-mode architecture
   - Create comparison table of modes
   - Add performance metrics

3. **Video Recording**
   - Demo both modes with test data
   - Show hallucination prevention
   - Explain technical approach

## Code Structure for AI Mode

```python
# Planned structure for LLM integration
/server/app/engine/
  ├── duck.py           # Existing DuckDB engine
  ├── llm_query.py      # New: OpenRouter integration
  ├── sql_validator.py  # New: Validate LLM-generated SQL
  └── schema_context.py # New: Provide schema to LLM

/server/app/routers/
  └── chat.py          # Modified: Route based on query_mode
```

## Success Criteria

1. **Test Data**: ✅ App uses provided test dataset exclusively
2. **AI Mode**: ✅ Toggle live + SQL generation pipeline
3. **No Hallucinations**: ⏳ Need real-world verification & evidence surface
4. **Performance**: ⏳ Sub-3 second response times
5. **Documentation**: ⏳ Clear explanation of dual-mode approach

## Notes

- Server runs at `http://localhost:8001`
- Test data location: `/test_data/` (interview_task_*.csv files)
- API key stored securely in `.env` (added to .gitignore)
- Column mappings handle schema differences automatically

## Commands for Testing

```bash
# Start server
cd server
source venv/bin/activate
python -m uvicorn app.main:app --reload --port 8001

# Test queries
curl -X POST http://localhost:8001/datasource/refresh
curl -X POST http://localhost:8001/chat -H "Content-Type: application/json" -d '{"message": "revenue last 30 days"}'
```

## Timeline

- **Monday**: Test data integration ✅
- **Tuesday**: AI/LLM mode implementation
- **Wednesday**: Final testing, documentation, and submission
