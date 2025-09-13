# 🚀 Data Answers - Project Roadmap

## ✨ What We Built (v0.1)

We created a **simple, trustworthy "Data Answers" app** that makes working with your business data feel effortless:

### Core Features
- **📤 Upload CSVs**: Drop your data files (ZIP or individual) right in Settings
- **💬 Natural Language Queries**: Ask questions in plain English - no complex SQL required
- **📊 Smart Answers**: Get responses with inline charts (when helpful) and a clean "Details" drawer showing the SQL, rows scanned, and timing
- **✅ Real Data Ready**: Works perfectly with your actual business data, not just samples

### 🎯 Core Queries (100% Reliable)

We've nailed the fundamentals that every business needs:

**Revenue Insights**
- "revenue last 30 days", "sales this month/quarter/year"
- "August 2024 revenue", "Q3 2024"

**Product Performance**
- "top 5 products", "best selling products/items", "popular products"

**Customer Orders**
- "orders 1001", "orders for CID 1001", "orders for John Smith" (with smart name lookup)

**Order Details**
- "order details 2001", "details for 2001"

### 📈 Built-in Reports

**Revenue by Month** - Clean bar chart with summary stats
**Top Customers** - Visual ranking with key metrics

## 🛡️ Why It's Trustworthy

We built this with transparency and reliability in mind:

- **🔍 Real SQL Under the Hood**: Every answer comes from actual SQL queries run on your CSVs using DuckDB
- **📋 Full Transparency**: The "Details" section shows the exact query, tables used, rows scanned, and execution time
- **📅 Smart Date Handling**: Relative dates automatically anchor to the latest date in your data (so "last 30 days" always makes sense)

## ⚡ What Makes It Practical

Real-world features that just work:

- **📁 Flexible Upload**: Handle ZIP files or individual CSVs through the Settings screen
- **🏷️ Smart Aliases**: Optional `alias_map.json` lets you map your actual column headers to standard names (your CSVs don't need to be "perfect")
- **🔄 Data Freshness**: Clear indicators show "Using data through [latest date] ([N] orders)" for full context
- **✅ Self-Check**: One-tap button to confirm everything is working properly

## 🎯 What We Didn't Add (On Purpose)

We kept the scope focused on what matters most:

- No "compare to previous period" or advanced pricing analysis (yet!)
- No user authentication or multi-tenant complexity
- No Google Drive integration
- No LLM dependencies or external API keys (keeps everything deterministic and private)

## 🔮 Next Steps (Coming Soon)

We're already planning these improvements:

- **👥 Smart Disambiguation**: Helpful messages when multiple customers match ("Which John?")
- **📊 Period Comparisons**: Compare revenue to previous periods
- **💾 Export Options**: Download charts and data as CSV files
- **☁️ Drive Sync**: Optional Google Drive folder synchronization

## 🛠️ Tech Stack

Built with modern, reliable tools:

**📱 Mobile App**
- React Native with Expo for cross-platform magic
- React Native Paper for that clean Material Design look
- Simple, effective chart components

**⚙️ Backend**
- FastAPI for lightning-fast API endpoints
- DuckDB for powerful, embedded SQL processing
- Fully dockerized for easy deployment

**💾 Data Layer**
- CSV files in a local folder (your data stays yours)
- Optional Parquet caching for blazing-fast queries

---

**🎯 Next Priority**: Continuing testing and creating demo video