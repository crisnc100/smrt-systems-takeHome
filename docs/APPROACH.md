# Product Approach & Thought Process

We kept this build grounded in a simple promise: every answer must come directly from the client’s CSVs, and the reviewer should never wonder how we got the number. Below is the human-friendly version of how we made that happen.

## 1. What we set out to build
- A mobile chat experience where stakeholders can ask about their business data without memorising SQL.
- Two modes so reviewers can pick their comfort level: **Classic** for the polished, deterministic questions we know they expect, and **Smart** when they want to phrase things freely.
- Receipts on every answer: SQL, tables touched, rows sampled, confidence notes—whatever happens, they can trust but verify.

## 2. How we read the dataset
- DuckDB runs locally, pointed at the CSVs in `test_data/` (or any uploads the reviewer provides).
- We mapped the interview columns into friendlier names (`server/app/engine/duck.py`) once at load time, so both modes talk in the same language (`product_id`, `qty`, `unit_price`, etc.).
- CSVs are cached as Parquet for speed, but the raw data never leaves the reviewer’s machine.

## 3. Classic Mode (deterministic)
- We use lightweight intent detectors (regex and keyword checks) to recognise the core prompts the take-home cares about: revenue by period, top products, top customers, orders for a CID, order details for an IID.
- Each intent points to a vetted SQL template with parameters. Same question, same SQL, zero surprises.
- Guards make sure the query is read-only, touches only whitelisted columns, and stays within a reasonable LIMIT.

## 4. Smart Mode (LLM assist, still grounded)
- We call OpenRouter with a clear system prompt (`server/app/engine/schema_context.py`) that lists the exact tables/columns and reminds the model to reply as JSON: `{ "sql", "summary", "follow_ups" }`.
- Once we get the SQL, we run it through our validator (`server/app/engine/sql_validator.py`). It rejects unsafe statements and quietly fixes common vendor idioms (e.g. turning `DATEADD(day, -30, CURRENT_DATE)` into DuckDB’s interval syntax).
- Only after those checks do we execute the SQL against DuckDB. If anything fails, the user gets a friendly error and can fall back to Classic.
- The final answer is formatted by us, not the model: we add the “We found X result(s)… ” heading, weave in the model’s summary, surface sample rows, and attach the evidence bundle.

## 5. Guardrails & evidence (for both modes)
- SELECT-only enforcement, column whitelist, LIMIT injection, and query timeouts live in one place so both Classic and Smart benefit.
- Confidence scoring uses simple heuristics (non-empty result, orphan checks) to flag anything suspicious without blocking the flow.
- The Evidence drawer in the app always shows SQL, tables used, rows scanned, sample rows, and any warnings, so reviewers can rerun the query themselves if they’d like.

## 6. Frontend touch points
- React Native + Expo for quick iOS/Android coverage; React Native Paper gives us a clean Material look-and-feel.
- Mode hints are plain-English (“Classic covers the built-in questions”, “Smart understands free-form questions and still checks your data”) so reviewers don’t have to decode jargon.
- Dynamic suggestion chips pull real CIDs/IIDs from the dataset, but the helper text now just encourages natural language in Smart mode.
- The Settings screen houses the mode toggle, API base URL, CSV upload, self-check button, and live status output so everything is discoverable in one place.

## 7. Self-checks & reviewer confidence
- `/debug/test-queries` exercises the four canonical flows (revenue last 30 days, top products, top customers, representative orders/details) and returns PASS/FAIL with context.
- The app surfaces that same payload in Settings → “Run Self-Check”, making it easy to show the reviewer all systems are green before the demo.

## 8. What to mention in the Loom
1. Flip between Classic and Smart, run one query in each, and open the Evidence drawer to show the SQL + sample rows.
2. Describe the Smart mode pipeline in plain language: “LLM proposes SQL → we validate/fix → DuckDB executes → UI wraps it with evidence.”
3. Run the self-check so they see the guardrails at work.
4. Remind them Smart mode needs an OpenRouter key, but any SQL-friendly model can be swapped in.

This way the reviewer sees a thoughtful, trustworthy experience rather than a black box chatbot.
