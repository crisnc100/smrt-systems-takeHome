# AI Mode Implementation Plan

## Overview
Based on valuable feedback from the SMRT Systems team, we're enhancing our CSV query application to include an AI-powered mode alongside our existing pattern-matching system. This document outlines our implementation approach.

## Feedback Context
The SMRT Systems team appreciated our structured, deterministic approach but highlighted two key requirements:
1. **Use the provided test dataset** - Ensure consistency across all candidate evaluations
2. **Add AI/LLM capabilities** - Implement natural language query processing with LLM integration

## Dual-Mode Architecture

### Classic Mode (Current Implementation)
- **Pattern-based matching** for common queries
- **Zero hallucination risk** - all queries are predetermined
- **Fast response times** - no external API calls
- **100% reliable** for supported query patterns

### AI Smart Mode (New Addition)
- **Natural language understanding** via OpenRouter LLM API
- **Flexible query handling** - understands complex, arbitrary questions
- **SQL generation** from conversational input
- **Hallucination prevention** through strict validation
- **Unified chat UI** - users type the same way regardless of mode; quick suggestions are examples, not requirements

## Implementation Strategy

### 1. Data Source Configuration
- Switch from mock data generation to using provided test files in `/test_data/`
- Files: `Customer_test.csv`, `Inventory_test.csv`, `Detail_test.csv`, `Pricelist_test.csv`
- Ensures evaluation consistency with other candidates

### 2. Mode Toggle Feature
**User Experience:**
- Settings screen toggle: "Query Mode: [Classic | AI Smart Mode]"
- Mode indicator in chat interface
- Seamless switching between modes
- Preference saved for future sessions

### 3. AI Integration Architecture

```
User Query
    ↓
OpenRouter API 
    ↓
SQL Generation with Schema Context
    ↓
Multi-Layer Validation
    ↓
DuckDB Execution
    ↓
Real Data Results
```

### 4. Hallucination Prevention System

**Three-Layer Defense:**

**Layer 1: Constrained Prompting**
- Provide exact schema definition to LLM
- Specify available tables and columns only
- Include relationship mappings
- Set strict generation rules

**Layer 2: SQL Validation**
- Verify all table names exist
- Validate column references
- Ensure SELECT-only operations
- Check JOIN relationships
- Auto-add LIMIT clauses

**Layer 3: Result Verification**
- No data fabrication
- Empty results handled gracefully
- Error messages are factual
- Fallback to Classic Mode if needed

## Technical Implementation

### New Components
1. **`llm_query.py`** - OpenRouter integration and prompt management
2. **`sql_validator.py`** - LLM output validation and sanitization
3. **Mode toggle** in Settings UI
4. **Mode routing** in chat endpoint

### Environment Configuration
- `OPENROUTER_API_KEY` – required for live AI mode queries (store in `server/.env`)
- Optional overrides:
  - `OPENROUTER_MODEL` / `OPENROUTER_FALLBACK_MODEL`
  - `OPENROUTER_BASE_URL`
  - `OPENROUTER_TIMEOUT`, `OPENROUTER_MAX_TOKENS`
  - `OPENROUTER_SITE_URL`, `OPENROUTER_APP_NAME`

### OpenRouter Configuration
- **Primary Model**: Claude-3-haiku (optimal for SQL generation)
- **Fallback Model**: GPT-3.5-turbo
- **Cost-Effective**: Pay-per-query pricing
- **Fast Response**: <2 second query generation

### Schema Context Template
```python
SCHEMA = """
Tables and Columns:
- Customer: CID (int), name, email, phone
- Inventory: IID (int), CID (int, links to Customer), order_date, order_total
- Detail: detail_id (int), IID (int, links to Inventory), price_table_item_id (int), quantity
- Pricelist: price_table_item_id (int), item_name, price

Generate DuckDB SQL only. Never reference other tables or columns.
"""
```

## Example Interactions

### Classic Mode
**User**: "revenue last 30 days"
**System**: Matches pattern → Executes predefined query → Returns results

### AI Smart Mode
**User**: "Which customers haven't ordered anything this month but were active last month?"
**System**:
- LLM interprets complex request
- Generates: `SELECT DISTINCT c.* FROM Customer c WHERE c.CID IN (SELECT CID FROM Inventory WHERE order_date >= '2024-12-01' AND order_date < '2025-01-01') AND c.CID NOT IN (SELECT CID FROM Inventory WHERE order_date >= '2025-01-01')`
- Validates SQL structure
- Executes and returns real results
- Shows: "[AI Mode] Found 3 customers matching your criteria..."

## Benefits of This Approach

1. **Best of Both Worlds**
   - Reliability of pattern matching
   - Flexibility of AI understanding

2. **No Hallucinations**
   - LLM generates SQL, not answers
   - All results from actual data
   - Validation prevents invalid queries

3. **User Control**
   - Choose mode based on needs
   - Transparency in query generation
   - Fallback options available

4. **Production Ready**
   - Error handling at every step
   - Cost-effective API usage
   - Scalable architecture

## Timeline
- **Day 1**: Test data integration + Mode toggle UI
- **Day 2**: OpenRouter integration + Validation layer
- **Day 3**: Testing + Documentation updates

## Success Metrics
- ✅ Both modes functioning independently
- ✅ Zero hallucinations in AI mode
- ✅ Successful queries on provided test dataset
- ✅ Clear mode differentiation in UI
- ✅ Sub-3 second response times

## Next Steps
1. Configure application to use test_data files
2. Implement mode toggle in settings
3. Integrate OpenRouter API
4. Add validation layers
5. Test extensively with provided dataset
6. Update main documentation
7. Add UI polish (mode indicator tooltip, AI follow-up copy tweaks)
7. Add UI polish (mode indicator tooltip, AI follow-up copy tweaks)
