# Technical Approach: Query Logic & Scalability

## Overview
This document outlines the technical approach for building a trustworthy, scalable natural language query system for CSV/Parquet data analysis.

## Core Principles

### 1. Data Grounding & Trust
- **No Hallucinations**: Every answer is backed by actual SQL query results
- **Evidence-Based**: Show the exact SQL, tables used, and sample data
- **Confidence Scoring**: Calculate confidence based on data quality metrics
- **Validation Guards**: Prevent SQL injection and ensure SELECT-only queries

### 2. Query Intent Detection
We use a **rule-based pattern matching** approach rather than LLM-based intent detection for:
- **Predictability**: Consistent behavior across queries
- **Speed**: No API calls or model inference needed
- **Debuggability**: Clear regex patterns that can be tested
- **Cost**: Zero inference costs

## Architecture

```
User Query → Intent Detection → SQL Generation → Validation → Execution → Evidence Bundle
     ↓            ↓                   ↓              ↓            ↓              ↓
  Natural    Pattern Match      Template Fill    Guards      DuckDB      Format Response
  Language    with Regex         with Params     Check       Query       with Evidence
```

## Intent Detection Strategy

### Pattern-Based Matching
Each intent has specific trigger patterns:

```python
INTENTS = {
    "revenue_by_period": {
        "keywords": ["revenue", "sales", "income", "earnings"],
        "patterns": [r"last (\d+) days?", r"this month", r"last month"],
        "required": ["time_period"]
    },
    "top_products": {
        "keywords": ["top", "best"],
        "patterns": [r"top (\d+)?", r"best selling"],
        "optional": ["limit"]
    },
    "orders_by_customer": {
        "keywords": ["orders", "CID"],
        "patterns": [r"CID\s*(\d+)", r"customer\s+(\d+)"],
        "required": ["customer_id"]
    }
}
```

### Matching Algorithm
1. Check for required keywords first (fast rejection)
2. Extract parameters using regex groups
3. Validate all required parameters are found
4. Return SQL template with extracted values

## SQL Generation

### Template-Based Queries
Pre-defined, tested SQL templates ensure safety:

```sql
-- Revenue by Period Template
SELECT 
    DATE_TRUNC('day', order_date) as date,
    COUNT(*) as order_count,
    SUM(order_total) as revenue
FROM Inventory
WHERE order_date >= CURRENT_DATE - INTERVAL '{days} days'
GROUP BY date
ORDER BY date DESC
```

### Parameter Injection
- Use parameterized queries where possible
- Validate numeric parameters
- Sanitize string inputs
- Apply reasonable limits

## Data Quality & Confidence

### Quality Metrics
Calculate confidence based on:
- **Orphan Rate**: Foreign key violations
- **Null Rate**: Missing critical values
- **Data Freshness**: How recent the data is
- **Coverage**: Percentage of expected data present

### Confidence Scoring
```python
def calculate_confidence(metrics):
    confidence = 0.75  # Base confidence
    
    if metrics.orphan_rate > 0.1:
        confidence -= 0.2  # High orphan rate
    if metrics.null_rate > 0.2:
        confidence -= 0.15  # Many nulls
    if metrics.days_old > 30:
        confidence -= 0.1  # Stale data
        
    return max(0.3, min(1.0, confidence))
```

## Scalability Strategy

### 1. Parquet Conversion
Convert CSV to Parquet for 5-10x performance:
```python
df = pd.read_csv("data.csv")
df.to_parquet("data.parquet", compression='snappy')
```

### 2. Query Optimization

#### Preview Mode (Sampling)
For exploratory queries on large datasets:
```sql
SELECT * FROM large_table 
TABLESAMPLE BERNOULLI(10)  -- 10% sample
LIMIT 1000
```

#### Aggregation Optimization
Pre-compute common aggregates:
```sql
CREATE MATERIALIZED VIEW daily_revenue AS
SELECT DATE(order_date) as day, SUM(order_total) as revenue
FROM Inventory
GROUP BY day
```

#### Partitioning Strategy
For tables >1M rows:
- **Inventory**: Partition by year/month of order_date
- **Detail**: Hash partition on IID for parallel joins
- **Customer**: Range partition on CID

### 3. Caching

#### Query Result Cache
LRU cache for repeated queries:
```python
@lru_cache(maxsize=100)
def cached_query(sql_hash, params_hash):
    return execute_query(sql, params)
```

#### Metadata Cache
Cache table statistics and schemas to avoid repeated scans.

### 4. Timeout Protection
Prevent runaway queries:
```python
def query_with_timeout(sql, timeout_s=5.0):
    with ThreadPoolExecutor() as executor:
        future = executor.submit(execute_query, sql)
        return future.result(timeout=timeout_s)
```

## Performance Targets

| Dataset Size | Query Type | Target Response Time |
|-------------|------------|---------------------|
| <10K rows | Simple SELECT | <100ms |
| <100K rows | Aggregation | <500ms |
| <1M rows | Complex JOIN | <2s |
| >1M rows | Preview Sample | <500ms |
| >10M rows | Pre-aggregated | <1s |

## Error Handling

### Graceful Degradation
1. Try exact query first
2. If timeout, try with sampling
3. If still slow, suggest pre-aggregation
4. Always return partial results rather than error

### User-Friendly Messages
- "Query is taking longer than expected. Showing preview..."
- "No matching data found. Try expanding your date range."
- "Large dataset detected. Consider using preview mode."

## Testing Strategy

### Unit Tests
- Intent detection accuracy
- SQL injection prevention
- Parameter extraction
- Limit enforcement

### Integration Tests
- End-to-end query flow
- Data relationship validation
- Performance benchmarks
- Concurrent query handling

### Load Tests
- Generate large datasets (100K, 1M, 10M rows)
- Measure query response times
- Validate optimization triggers
- Test cache effectiveness

## Security Considerations

### SQL Injection Prevention
1. **Whitelist Operations**: Only allow SELECT
2. **Parameter Validation**: Type-check all inputs
3. **Query Analysis**: Parse SQL AST before execution
4. **Limit Enforcement**: Cap result sets

### Data Access Control
- Read-only database connections
- Separate schemas for different access levels
- Audit logging for all queries

## Future Enhancements

### Near-term
- [ ] Incremental data loading
- [ ] Query result pagination
- [ ] Export to Excel/CSV
- [ ] Scheduled report generation

### Long-term
- [ ] Distributed query execution
- [ ] Real-time data streaming
- [ ] ML-based query optimization
- [ ] Natural language query builder UI

## Conclusion

This approach prioritizes:
1. **Trustworthiness** through evidence-based answers
2. **Performance** through intelligent optimization
3. **Scalability** through sampling and caching
4. **Maintainability** through simple, testable patterns

The system should handle datasets from 100 rows to 10M+ rows while maintaining sub-second response times for most queries through strategic use of sampling, caching, and pre-aggregation.