  <originalInstructions> 
    Candidate Task: AI-Driven Mobile App with CSV Integration
Objective:
Build a mobile application (React Native preferred) that acts as an interface to an AI system capable of querying a set of CSV files stored in a fixed location (e.g., Google Drive).
The application should:
Provide a chat-based interface where a user can ask questions about their financial/order information.
The AI system should query the CSV files directly to generate answers, ensuring that responses are reliable and grounded in the actual data. (Hallucinations or fabricated answers must be prevented through data validation techniques.)
The app should handle at least the following files (dataset provided here):


Customer.csv – customer profile information
Inventory.csv – order-level information (linked to Customer via CID)
Detail.csv – order details (linked to Inventory via IID, and to Pricelist via price_table_item_id)
Pricelist.csv – pricing information
Ensure that the system can scale to handle larger datasets (e.g., more rows), even though the provided dataset is minimal.


Bonus Points:
Implement report generation:
Textual reports summarizing customer/order/inventory data.
Visual reports (charts/graphs) that make insights easier to understand.
Clean UI/UX using React Native + MUI.
Include backend/API logic (PHP or Python) to handle queries and serve structured responses.
Dockerized setup for easier review and deployment.


Deliverables:
A GitHub/GitLab repo link containing:
Source code for the mobile app + backend (if applicable).
Setup instructions.
Brief documentation (1-2 pager) describing your approach, including how you ensured data-grounded responses and scalability.
A loom/video recording of the final outcome


Mail your submissions to: 
prakhar.l@smrtsystems.com
CC: himanshu.s@smrtsystems.com, sidharth.a@smrtsystems.com 

Deadline: Sep 15th, 2025 10 AM

</originalInstructions>

## Implementation Status (Updated: Jan 2025)

### ✅ Core Requirements COMPLETE
- **Query Logic**: All 24 API tests passing (100% success rate)
- **No Hallucinations**: System rejects invalid queries, only returns real data
- **SQL Safety**: Injection protection verified, SELECT-only enforcement working
- **Evidence-Based**: Every response includes SQL query, row counts, and sample data
- **Pattern Matching**: Natural language understanding for revenue, products, orders
- **Scalability**: Query optimization, sampling, and caching implemented

### Test Results
```
Tests run: 24
Passed: 24 ✅
Failed: 0 ❌
- 12 valid queries correctly processed
- 8 invalid queries correctly rejected  
- 4 SQL injection attempts blocked
```

### Key Achievements
1. Fixed critical bug where "revenue" without time period was incorrectly matching
2. Implemented comprehensive test suite with unit and API tests
3. Added support for "best selling products" pattern
4. Created thorough documentation (Approach.md, README, test instructions)

<Simple>
 A mobile app that gives trustworthy answers about your business data - with receipts.

  The Problem

  Imagine you're a business owner with customer orders, inventory, and pricing data in spreadsheets. You want quick answers like:
  - "What's my revenue this month?"
  - "Who are my top customers?"
  - "Which products sell best?"

  But you don't trust AI chatbots because they might make up numbers. You need real answers from real data.

  Our Solution

  A chat app that:
  1. Answers questions using ONLY your actual data - no guessing, no hallucinations
  2. Shows its work - every answer includes the exact database query, which tables were checked, and sample rows
  3. Builds trust - you can see exactly how each number was calculated
  4. Runs locally - your sensitive business data never leaves your device/server

  Real-World Use Case

  Sarah runs an e-commerce store. She has CSVs with customer info, orders, inventory, and prices.

  Instead of manually creating Excel pivots, she asks the app:
  - "Revenue last 30 days?" → $45,230 (plus the SQL query that calculated it)
  - "Top 5 products?" → Chart with product names (plus the data table)
  - "Orders for customer John?" → List of orders (plus evidence of which tables were joined)

  Why It's Different

  Traditional AI: "Your revenue is probably around $50k" (might be wrong)

  Our App: "Your revenue is $45,230.50" (here's the SQL, here's the 1,247 orders I counted, here's a sample of the data)

  The Trust Factor

  Every answer includes:
  - ✅ The exact SQL query executed
  - ✅ Which data files were used
  - ✅ How many records were analyzed
  - ✅ Sample rows you can verify
  - ✅ Confidence score based on data quality

  Bottom line: It's like having a data analyst who always shows their Excel formulas - you can verify everything.
  </Simple>
  
  
  Build a React Native mobile app with a chat-based interface that answers questions grounded strictly in CSV data
(Customer, Inventory, Detail, Pricelist). Backend executes validated queries (no hallucinations) and returns answers
with evidence. Ship fast with clean UI, basic reports, Dockerized backend, and clear docs.

    <goal>Strictly data-grounded answers with visible evidence</goal>
    <goal>Minimum 4 screens: Chat, Reports, Settings, Onboarding (optional modal for report detail)</goal>
    <goal>Backend runs locally via Docker; zero cloud requirement for reviewers</goal>
    <goal>Scales to larger datasets via Parquet + DuckDB optimizations</goal>
    <goal>Unique trust features: evidence chips, Ask→SQL toggle, insight suggestions</goal>

    <time>1 week</time>
    <stack>React Native (Expo recommended), FastAPI (Python), DuckDB</stack>
    <dataLocation>Local CSV folder by default; optional Google Drive sync (post-MVP)</dataLocation>
    <auth>None for take-home; optional simple bearer token if hosted</auth>
    <aiIntegration>LLM optional and OFF by default; deterministic planner first</aiIntegration>

    <feature>Chat Q&amp;A: Top customers/products, revenue by period, orders by customer, order details by IID</feature>
    <feature>Evidence bundle: executed SQL, tables/columns, rows scanned, sample rows</feature>
    <feature>Reports: Revenue by month (chart), Top customers (chart), textual summary</feature>
    <feature>Settings: Data refresh, API URL, theme, optional AI toggle (hidden by default)</feature>
    <nonGoals>Full user authentication, multi-tenant data, complex Drive OAuth — defer</nonGoals>

    <trustMode>Evidence chips + confidence score from validators; “How computed” trace</trustMode>
    <askToSqlToggle>User can inspect limited SELECT-only SQL and rerun</askToSqlToggle>
    <insightCards>Post-answer follow-ups (e.g., “Compare last 30 days”)</insightCards>
    <compareMode>Period-over-period diffs for key metrics</compareMode>
    <dataQualityBadges>Show orphan joins, missing IDs, negative prices to contextualize answers</dataQualityBadges>

    <mobile>
      <framework>Expo (React Native + TypeScript)</framework>
      <ui>React Native Paper (Material-inspired), react-navigation, react-native-svg + Victory Native</ui>
      <network>Axios or fetch to backend; base URL from Settings</network>
    </mobile>
    <backend>
      <framework>FastAPI + Uvicorn</framework>
      <engine>DuckDB for SQL on CSV/Parquet; optional Polars for transforms</engine>
      <planner>Rule-based intents → SQL templates; optional LLM for QueryPlan (off by default)</planner>
      <validation>Strict validators (row counts, join completeness, SELECT-only)</validation>
      <docker>Single container; local volume mount for data folder</docker>
    </backend>
    <data-engine>
      <ingestion>Load CSVs from `DATA_DIR`; build Parquet cache on first run</ingestion>
      <joins>Customer.CID = Inventory.CID; Inventory.IID = Detail.IID; Detail.price_table_item_id =
Pricelist.price_table_item_id</joins>
      <aliasing>Schema alias map to normalize columns</aliasing>
      <caching>LRU cache for parameterized queries</caching>
    </data-engine>
    <integration>
      <endpoints>/health, /datasource/refresh, /chat, /report</endpoints>
      <responses>Answers + evidence (SQL, tables, rows, samples); chart series for reports</responses>
    </integration>

    <file name="Customer.csv">
      <columns>CID (pk), name, email, created_at, segment?</columns>
    </file>
    <file name="Inventory.csv">
      <columns>IID (pk), CID (fk), order_date, status, order_total</columns>
    </file>
    <file name="Detail.csv">
      <columns>DID (pk), IID (fk), product_id, qty, unit_price, price_table_item_id (fk)</columns>
    </file>
    <file name="Pricelist.csv">
      <columns>price_table_item_id (pk), product_id, price</columns>
    </file>
    <alias-map-example><![CDATA[
customer_id: [CID, customerId]
inventory_id: [IID, inventoryId]
order_total: [total, order_total]
order_date: [date, order_date]
]]>


    <endpoint method="GET" path="/health">
      <request>{}</request>
      <response>{"ok": true, "version": "x.y.z"}</response>
    </endpoint>

    <endpoint method="POST" path="/datasource/refresh">
      <request>{"source":"local","config":{"data_dir":"./data"}}</request>
      <response>{"status":"ok","files_loaded":4,"parquet_cached":true,"last_sync":"ISO-8601"}</response>
    </endpoint>

    <endpoint method="POST" path="/chat">
      <request><![CDATA[
{
"session_id": "uuid-optional",
"message": "what is revenue last 30 days?",
"filters": {"date_range": {"from":"2024-08-01","to":"2024-08-31"}},
"ai_assist": false
}
]]>
      <response><![CDATA[
{
"answer_text": "Revenue last 30 days: $123,450 (↑ 12% vs prior).",
"tables_used": ["Inventory", "Detail"],
"sql": "SELECT ...",
"rows_scanned": 12412,
"data_snippets": [{"date":"2024-08-12","revenue":4211.22}],
"validations": [{"name":"non_empty_result","status":"pass"}],
"confidence": 0.92,
"follow_ups": ["Top products last 30 days", "Compare vs prior 30 days"],
"chart_suggestion": {"type":"line","x":"order_date","y":"revenue"}
}
]]>
    </endpoint>

    <endpoint method="POST" path="/report">
      <request><![CDATA[
{ "type": "revenue_by_month", "filters": {"date_range": {"from":"2024-01-01","to":"2024-12-31"}} }
]]>
      <response><![CDATA[
{
"summary_text": "2024 revenue by month with peak in July.",
"tables_used": ["Inventory","Detail"],
"sql": ["SELECT ... GROUP BY month"],
"charts": [
    {"type":"bar","series":[{"name":"Revenue","data":[["2024-01", 10000], ["2024-02", 12000]]]}]
}
]]>
    </endpoint>

    <rules-based-intents>
      <intent name="revenue_by_period" match="revenue|sales (today|yesterday|last|this) (week|month|30 days|quarter|
year)">
        <sql-template><![CDATA[
SELECT CAST(order_date AS DATE) AS day, SUM(order_total) AS revenue
FROM Inventory
WHERE order_date BETWEEN :from AND :to
GROUP BY day
ORDER BY day;
]]>
      </intent>
      <intent name="orders_by_customer" match="orders for (customer|cid) (?P<cid>\w+)">
        <sql-template><![CDATA[
SELECT I.IID, I.order_date, I.order_total
FROM Inventory I
WHERE I.CID = :cid
ORDER BY I.order_date DESC
LIMIT 100;
]]>
      </intent>
      <intent name="top_products" match="top (products|items)( by (revenue|qty))?">
        <sql-template><![CDATA[
SELECT D.product_id,
       SUM(D.qty) AS total_qty,
       SUM(D.qty * D.unit_price) AS total_revenue
FROM Detail D
GROUP BY D.product_id
ORDER BY total_revenue DESC
LIMIT :k;
]]>
      </intent>
      <intent name="order_details" match="order (details|lines) (for )?(iid|order) (?P<iid>\w+)">
        <sql-template><![CDATA[
SELECT D.DID, D.product_id, D.qty, D.unit_price, (D.qty * D.unit_price) AS line_total
FROM Detail D
WHERE D.IID = :iid
ORDER BY D.DID;
]]>
      </intent>
    </rules-based-intents>

    <optional-llm>
      <status>OFF by default</status>
      <purpose>Convert NL → QueryPlan JSON; still validated; SELECT-only</purpose>
      <queryplan-schema><![CDATA[
{
"type": "object",
"required": ["intent","filters","limits"],
"properties": {
    "intent": {"enum":["revenue_by_period","orders_by_customer","top_products","order_details"]},
    "filters": {"type":"object"},
    "limits": {"type":"object","properties":{"rows":{"type":"integer","maximum":5000}}}
}
}
]]>
    </optional-llm>

    <validator name="select_only">Reject non-SELECT; deny DDL/DML keywords</validator>
    <validator name="whitelist_columns">Only allowed tables/columns from schema map</validator>
    <validator name="bounded_rows">Apply LIMIT and statement timeout</validator>
    <validator name="non_empty_result">If zero rows, return “cannot answer” with refinement suggestions</validator>
    <validator name="join_integrity">Check orphan rates when joins are used; show badge if high</validator>
    <validator name="numeric_sanity">Flag negative totals or extreme outliers</validator>

    <screen name="Onboarding (optional)">Choose sample data; explain trust mode</screen>
    <screen name="Chat">
      <components>Prompt input, suggestion chips, answer card, evidence drawer (SQL, rows, samples), follow-up chips,
Ask→SQL toggle</components>
    </screen>
    <screen name="Reports">
      <components>Revenue by month chart, Top customers chart, filters, compare toggle</components>
    </screen>
    <screen name="Report Detail (modal)">Metric + dimension picker, export CSV/PDF</screen>
    <screen name="Settings">
      <components>API URL, Data refresh, Theme, AI toggle (hidden unless key present)</components>
    </screen>

    <flow name="First Run">
      <step>Load sample CSVs from bundled data directory</step>
      <step>Call /datasource/refresh and show success toast</step>
    </flow>
    <flow name="Ask a Question">
      <step>User taps “Revenue last 30 days”</step>
      <step>App calls /chat with message and date filter</step>
      <step>Backend plans query, validates, executes</step>
      <step>App shows answer + evidence chips; follow-ups appear</step>
    </flow>
    <flow name="Reports">
      <step>User opens Reports tab</step>
      <step>App fetches /report for revenue_by_month</step>
      <step>Chart renders with compare toggle and summary text</step>
    </flow>
    <flow name="Settings">
      <step>User updates API URL, taps “Refresh Data”</step>
      <step>App calls /datasource/refresh; shows result</step>
    </flow>

    <strategy>CSV → Parquet on first load; pushdown predicates; select required columns only</strategy>
    <cache>Memoize aggregates (revenue by day/month, top-k products)</cache>
    <batched>Precompute daily revenue; refresh on data change</batched>
    <largeData>Streamed scans via DuckDB; keep LIMITs reasonable; avoid SELECT *</largeData>

    <day index="1">
      <tasks>
        <task>Scaffold Expo app (TS), navigation, theme</task>
        <task>Scaffold FastAPI, /health, project structure</task>
        <task>Place sample CSVs under server/data</task>
        <task>Write README skeleton and goals</task>
      </tasks>
    </day>
    <day index="2">
      <tasks>
        <task>Implement CSV loader, alias map, Parquet cache</task>
        <task>DuckDB connection, core joins, unit tests for loader</task>
        <task>/datasource/refresh endpoint</task>
      </tasks>
    </day>
    <day index="3">
      <tasks>
        <task>Rule-based intents + SQL templates</task>
        <task>/chat endpoint returns narrative + evidence</task>
        <task>RN Chat screen wired to backend</task>
      </tasks>
    </day>
    <day index="4">
      <tasks>
        <task>Add validators (select-only, whitelist, bounded rows, non-empty)</task>
        <task>Evidence drawer UI + Ask→SQL toggle</task>
        <task>LRU caching and basic perf checks</task>
      </tasks>
    </day>
    <day index="5">
      <tasks>
        <task>/report endpoint for revenue_by_month and top_customers</task>
        <task>Charts in RN (Victory Native), compare toggle</task>
        <task>Insight chips and data quality badges</task>
      </tasks>
    </day>
    <day index="6">
      <tasks>
        <task>Polish UI, empty/error states, loading skeletons</task>
        <task>Dockerize backend; docker-compose for API</task>
        <task>Finalize docs: setup, approach, grounding, scalability</task>
      </tasks>
    </day>
    <day index="7">
      <tasks>
        <task>Scale tests with larger CSVs; profile hot paths</task>
        <task>Fix edge cases; lock version</task>
        <task>Record Loom walkthrough; repo hygiene</task>
      </tasks>
    </day>

<![CDATA[
repo-root/
mobile/                 # Expo app
    app.json
    app/                  # expo-router or src/
      screens/
        ChatScreen.tsx
        ReportsScreen.tsx
        SettingsScreen.tsx
        ReportDetailModal.tsx
      components/
        EvidenceDrawer.tsx
        AnswerCard.tsx
        Chart.tsx
      lib/api.ts
      theme/
server/                 # FastAPI
    app/
      main.py
      routers/
        health.py
        datasource.py
        chat.py
        report.py
      data/
        loader.py
        schema_alias.py
      engine/
        duck.py
        cache.py
      planner/
        intents.py
        templates.py
        query_plan.py
      validators/
        guards.py
        grounding.py
      reporting/
        compose.py
      tests/
        test_loader.py
        test_intents.py
    data/
      Customer.csv
      Inventory.csv
      Detail.csv
      Pricelist.csv
    Dockerfile
    requirements.txt
docker-compose.yml
README.md
docs/Approach.md
]]>

    <prereqs>Node 18+, pnpm/yarn/npm, Python 3.11+, Docker</prereqs>
    <commands>
      <backend><![CDATA[
cd server
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
]]>
      <mobile><![CDATA[
cd mobile
npm install
npm run start
]]>
      <docker-backend><![CDATA[
docker compose up --build

# Backend at http://localhost:8000

]]>
    </commands>
    <env-vars>
      <var name="DATA_DIR" default="./data">Path to CSVs</var>
      <var name="API_PORT" default="8000">Backend port</var>
      <var name="API_TOKEN" optional="true">Optional bearer for hosted demo</var>
      <var name="OPENROUTER_API_KEY" optional="true">Optional; LLM assist OFF if missing</var>
    </env-vars>

    <unit>Loader parses CSVs, builds Parquet, alias map works</unit>
    <unit>Intents produce safe SQL given inputs</unit>
    <integration>/chat returns answers + evidence; validators trip on bad inputs</integration>
    <report>Charts return sane series; compare calculations correct</report>
    <scale>Run with 100k–1M rows in one table; measure latency</scale>

    <criterion>Every answer includes executed SQL, tables used, rows scanned, and sample rows</criterion>
    <criterion>Core questions supported: revenue by period, orders by customer, top products, order details</criterion>
    <criterion>At least one textual and one visual report</criterion>
    <criterion>Dockerized backend starts with one command; mobile connects with configurable base URL</criterion>
    <criterion>Handles larger CSVs with acceptable latency via Parquet + DuckDB</criterion>
    <criterion>Docs and Loom/video included</criterion>

    <file name="server/Dockerfile"><![CDATA[
FROM python:3.11-slim
WORKDIR /app
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server /app
ENV DATA_DIR=/app/data
EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
]]>
    <file name="docker-compose.yml"><![CDATA[
services:
api:
    build: ./server
    ports: ["8000:8000"]
    environment:
      - DATA_DIR=/app/data
    volumes:
      - ./server/data:/app/data
]]>


    <narrative>Answers composed from query results; no free-text beyond templated summaries</narrative>
    <failurePath>Return “cannot answer” with reason and suggested refinements when validators fail</failurePath>
    <sql-guard>Block non-SELECT; whitelist columns; cap LIMIT and time</sql-guard>
    <evidence>Always return SQL, tables, rows count, and sample rows; show in UI</evidence>

    <prompt>Revenue last 30 days</prompt>
    <prompt>Top 5 products by revenue</prompt>
    <prompt>Orders for CID 12345</prompt>
    <prompt>Order details for IID 98765</prompt>
    <prompt>Compare revenue this month vs last month</prompt>

    <feature>Google Drive integration (service account + folder sync)</feature>
    <feature>Supabase path (import CSVs, views/RPCs, Edge Function for NL→SQL)</feature>
    <feature>User auth (email magic link) if hosting</feature>
    <feature>Export PDF/CSV for reports</feature>

    <steps>
      <step>Create project; tables for Customer, Inventory, Detail, Pricelist</step>
      <step>Import CSV via SQL Editor (COPY) or UI</step>
      <step>Create views for common joins; indexes on CID, IID, order_date</step>
      <step>Define RPCs: revenue_by_period, orders_by_customer, top_products, order_details</step>
      <step>Mobile calls PostgREST endpoints; optional Edge Function for NL→QueryPlan</step>
    </steps>
    <tradeoffs>More setup; great hosting and auth; still must enforce grounding via RPCs</tradeoffs>

    <risk>MUI on RN</risk>
    <mitigation>Use React Native Paper for Material look</mitigation>
    <risk>Dataset column names differ</risk>
    <mitigation>Schema alias map; defensive joins; validation warnings</mitigation>
    <risk>Large CSV performance</risk>
    <mitigation>Parquet cache, predicate pushdown, aggregates</mitigation>
    <risk>Reviewer setup friction</risk>
    <mitigation>Docker Compose, sample data, clear README, Loom</mitigation>

    <step index="1" title="Scaffold projects">
      <details>Expo app with screens; FastAPI app with routers and health check</details>
    </step>
    <step index="2" title="Implement data loader">
      <details>Read CSVs, build Parquet cache, alias schema, expose /datasource/refresh</details>
    </step>
    <step index="3" title="Write SQL templates and intents">
      <details>Map common questions to parameterized SQL with guards</details>
    </step>
    <step index="4" title="Build /chat endpoint">
      <details>Plan → validate → execute → format narrative + evidence</details>
    </step>
    <step index="5" title="Wire Chat UI">
      <details>Send message, render answer, evidence drawer, follow-ups</details>
    </step>
    <step index="6" title="Add validators and caching">
      <details>SELECT-only, whitelist, bounded rows; LRU cache for aggregates</details>
    </step>
    <step index="7" title="Reports endpoint and UI">
      <details>revenue_by_month and top_customers; charts and compare toggle</details>
    </step>
    <step index="8" title="Polish and Dockerize">
      <details>Error/empty states, loading skeletons; Dockerfile + compose; docs</details>
    </step>
    <step index="9" title="Scale test and record">
      <details>Run with larger CSVs, fix hotspots, record Loom</details>
    </step>

    <item>Git repo with mobile/ and server/</item>
    <item>Dockerized FastAPI backend + sample CSVs</item>
    <item>Setup instructions (README) and 1–2 page approach doc</item>
    <item>Loom/video walkthrough</item>