Roadmap Summary                                                                                                                                                    
                                                                                                                                                                   
- Strategy: Ship a trust-first vertical slice in 48 hours, then expand.                                                                                            
- Uniqueness: Evidence-by-default, Ask→SQL, “How computed” trace, quality badges, insight nudges.                                                                  
- Scope Guardrails: 4 core questions, 2 reports, Dockerized backend, clean RN UI, no LLM by default.                                                               
                                                                                                                                                                   
Milestones                                                                                                                                                         
                                                                                                                                                                   
- M0: Repo + scaffolds + sample data                                                                                                                               
- M1: End-to-end Chat (revenue_by_period) with evidence                                                                                                            
- M2: Intents coverage (orders_by_customer, top_products, order_details)                                                                                           
- M3: Validators + trust UX (chips, trace, Ask→SQL)                                                                                                                
- M4: Reports + compare mode                                                                                                                                       
- M5: Docker, docs, Loom                                                                                                                                           
                                                                                                                                                                   
4-Day Execution Plan                                                                                                                                               
                                                                                                                                                                   
- Day 1: Vertical Slice                                                                                                                                            
    - Backend: FastAPI skeleton, /health, /datasource/refresh, CSV→Parquet loader (DuckDB), schema alias map, revenue_by_period SQL.                               
    - Mobile: Chat screen, AnswerCard, Evidence Drawer (SQL, tables used, rows scanned, sample rows), follow-up chips for period variants.                         
- Day 2: Coverage + Trust                                                                                                                                          
    - Intents: orders_by_customer, top_products, order_details with parameterized SQL.                                                                             
    - Validators: select-only, whitelist columns, bounded rows/timeouts, non-empty result; failure path returns “cannot answer” + refinements.                     
    - UI: Ask→SQL toggle with sanitized SQL; “How computed” trace + confidence badge; loading/empty/error states.                                                  
- Day 3: Reports + Polish                                                                                                                                          
    - /report: revenue_by_month (bar) + top_customers (bar/pie), compare toggle; short textual summaries.                                                          
    - Mobile Reports: Chart component (Victory Native), filters, compare toggle, export CSV for current chart.                                                     
    - Settings: API URL, Data refresh, Theme; AI toggle hidden unless key present.                                                                                 
- Day 4: Productionize                                                                                                                                             
    - Docker: Server Dockerfile + docker-compose with data volume mount.                                                                                           
    - Perf: LRU cache for aggregates; predicate pushdown; avoid SELECT *.                                                                                          
    - Docs: README (setup), docs/Approach.md (grounding + scale + trust), Loom walkthrough. Buffer for fixes.                                                      
                                                                                                                                                                   
Deliverables                                                                                                                                                       
                                                                                                                                                                   
- Repo with mobile/ and server/ per structure in context.                                                                                                          
- Sample CSVs in server/data.                                                                                                                                      
- Dockerized FastAPI backend, Expo RN app.                                                                                                                         
- README + Approach doc + Loom.                                                                                                                                    
                                                                                                                                                                   
Backend Scope                                                                                                                                                      
                                                                                                                                                                   
- Framework: FastAPI + Uvicorn                                                                                                                                     
- Engine: DuckDB over CSV/Parquet; Parquet cache built on first run                                                                                                
- Endpoints:                                                                                                                                                       
    - GET /health: status                                                                                                                                          
    - POST /datasource/refresh: rebuilds Parquet, returns table stats                                                                                              
    - POST /chat: {message, filters, ai_assist=false} → {answer_text, tables_used, sql, rows_scanned, data_snippets, validations, confidence, follow_ups,          
chart_suggestion}                                                                                                                                                  
    - POST /report: {type, filters} → {summary_text, tables_used, sql[], charts[]}                                                                                 
- Intents (rule-based regex → parameterized SQL):                                                                                                                  
    - revenue_by_period                                                                                                                                            
    - orders_by_customer                                                                                                                                           
    - top_products                                                                                                                                                 
    - order_details                                                                                                                                                
- Validators:                                                                                                                                                      
    - select_only, whitelist_columns, bounded_rows/timeout, non_empty_result                                                                                       
    - join_integrity, numeric_sanity (badge-only, non-blocking)                                                                                                    
- Caching:                                                                                                                                                         
    - LRU for revenue aggregates; memoize TOP-K product queries                                                                                                    
- Security:                                                                                                                                                        
    - Optional bearer API_TOKEN (off by default for take-home)                                                                                                     
                                                                                                                                                                   
Mobile Scope                                                                                                                                                       
                                                                                                                                                                   
- Framework: Expo (TypeScript)                                                                                                                                     
- UI: React Native Paper (Material-inspired), react-navigation                                                                                                     
- Charts: Victory Native                                                                                                                                           
- Screens:                                                                                                                                                         
    - Chat: prompt, suggestion chips, AnswerCard, Evidence Drawer, follow-ups, Ask→SQL toggle                                                                      
    - Reports: revenue_by_month + top_customers, filters, compare toggle, export CSV                                                                               
    - Settings: API URL, Data refresh, Theme, optional AI toggle (hidden)                                                                                          
    - Report Detail (modal): metric/dimension picker (light)                                                                                                       
- Networking: fetch with base URL from Settings; retry + toast on failures                                                                                         
- State: lightweight (React Query optional, otherwise simple hooks)                                                                                                
                                                                                                                                                                   
Uniqueness Enhancers                                                                                                                                               
                                                                                                                                                                   
- Evidence chips: “SQL”, “Rows Scanned”, “Tables Used”, “Samples” with copy-to-clipboard                                                                           
- “How computed” trace: list calculations and safeguards applied                                                                                                   
- Confidence badge: derived from validators; color-coded                                                                                                           
- Data quality badges: orphan joins %, negative prices, outliers — clarify trust                                                                                   
- Insight nudges: context-aware follow-ups, chart suggestions                                                                                                      
- Ask→SQL: user-inspectable sanitized SQL with rerun; parameters highlighted                                                                                       
                                                                                                                                                                   
Acceptance Criteria                                                                                                                                                
                                                                                                                                                                   
- Every chat answer includes executed SQL, tables used, rows scanned, sample rows                                                                                  
- Supports 4 core questions end-to-end with parameterized SQL                                                                                                      
- /report returns 1 visual (bar/line) + textual summary; compare toggle works                                                                                      
- Backend runs via docker compose up; mobile connects via configurable URL                                                                                         
- Handles larger CSVs reasonably using Parquet + DuckDB; no SELECT *                                                                                               
                                                                                                                                                                   
Performance & Scale Plan                                                                                                                                           
                                                                                                                                                                   
- CSV → Parquet on first load; reuse Parquet subsequently                                                                                                          
- Pushdown filters (date ranges, CID/IID); select required columns only                                                                                            
- LRU cache for daily revenue and top-k queries                                                                                                                    
- Cap LIMIT and enforce statement timeout; stream results where possible                                                                                           
                                                                                                                                                                   
Testing Plan                                                                                                                                                       
                                                                                                                                                                   
- Unit: loader aliasing, Parquet build, intent to SQL mapping                                                                                                      
- Integration: /chat happy path and validator failures; /report shape and series correctness                                                                       
- Scale smoke: run with larger CSVs (local) and capture latency                                                                                                    
                                                                                                                                                                   
Demo Script (Loom)                                                                                                                                                 
                                                                                                                                                                   
- First run: refresh data, show sample CSVs loaded                                                                                                                 
- Ask: “Revenue last 30 days” → answer + evidence + follow-ups                                                                                                     
- Ask: “Top 5 products by revenue” → evidence + chart suggestion                                                                                                   
- Orders for customer + order details by IID                                                                                                                       
- Reports tab: revenue by month with compare toggle                                                                                                                
- Ask→SQL flow with sanitized SQL and rerun                                                                                                                        
- Data quality badges explained                                                                                                                                    
                                                                                                                                                                   
Changes From Original Instructions                                                                                                                                 
                                                                                                                                                                   
- UI library: Use React Native Paper (Material look) instead of MUI for RN viability.                                                                              
- LLM: OFF by default; deterministic planner first; optional toggle if key present.                                                                                
- Drive sync: Defer to post-MVP; local CSVs by default per “zero cloud requirement”.                                                                               
                                                                                                                                                                   
Risks & Mitigations                                                                                                                                                
                                                                                                                                                                   
- CSV column variance: schema alias + defensive joins; surface warnings as badges                                                                                  
- Large data perf: Parquet cache, pushdown, caching, LIMIT caps                                                                                                    
- Reviewer setup: Docker Compose, bundled data, concise README and Loom 