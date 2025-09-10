# Test Instructions

## Running the Tests

### Prerequisites
1. Make sure the server is running:
   ```bash
   cd server
   python -m uvicorn app.main:app --reload
   ```

2. Ensure mock data is loaded:
   ```bash
   curl -X POST http://localhost:8000/datasource/refresh
   ```

### Run All Tests
```bash
cd server
python run_tests.py
```

### Expected Test Results

#### Tests That Should Pass ✅
- `test_intent_detection` - All intent patterns correctly identified
- `test_safe_queries` - SELECT queries allowed
- `test_limit_enforcement` - LIMIT properly applied
- `test_case_insensitivity` - Case-insensitive matching works
- `test_number_extraction` - Numbers extracted from queries
- `test_special_characters_in_queries` - Special chars handled

#### Tests That May Fail (Expected) ⚠️
- `test_ambiguous_queries` - "revenue" alone should NOT match (fixed)
- Database connection tests - These require the server running:
  - `test_data_relationships`
  - `test_revenue_calculation`
  - `test_date_filtering`
  - `test_price_consistency`
  - `test_order_total_accuracy`
  - `test_date_range_consistency`
  - `test_customer_order_distribution`

### Manual Testing

After running automated tests, manually verify these queries work:

```bash
# Should work
curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' \
  -d '{"message":"revenue last 30 days"}'

curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' \
  -d '{"message":"top 5 products"}'

curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' \
  -d '{"message":"orders for CID 1001"}'

# Should NOT work (return "unsupported question")
curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' \
  -d '{"message":"revenue"}'  # Missing time period

curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' \
  -d '{"message":"products"}'  # Missing "top" qualifier

curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' \
  -d '{"message":"orders"}'  # Missing CID
```

## What the Tests Validate

### 1. Intent Detection Accuracy
- Revenue queries require both keyword AND time period
- Top products require "top" or "best" keyword
- Customer orders require CID
- Order details require IID

### 2. SQL Safety
- Only SELECT queries allowed
- No DROP, DELETE, UPDATE, INSERT
- SQL injection attempts blocked
- Result limits enforced

### 3. Data Quality
- Foreign key relationships valid
- Order totals match detail sums (approximately)
- Date ranges consistent
- No orphaned records

### 4. Edge Cases
- Ambiguous queries rejected
- Special characters handled
- Large numbers processed
- Empty results handled gracefully

## Interpreting Test Output

### Success
```
test_intent_detection ... ok
test_safe_queries ... ok
Ran 20 tests in 0.5s
OK
```

### Failures to Investigate
```
FAIL: test_ambiguous_queries
AssertionError: Should not match vague query: revenue
```
This means the intent detection is too broad.

### Expected Warnings
```
Warning: 2 price mismatches found
```
Some price discrepancies are expected in test data.

## Next Steps After Testing

1. **If core tests pass**: Query logic is working correctly
2. **If intent tests fail**: Check pattern matching in `chat.py`
3. **If SQL tests fail**: Review guards in `validators/guards.py`
4. **If data tests fail**: Verify CSV files are loaded correctly

## Performance Testing

For large dataset testing:
```bash
# Generate 100k orders
python generate_large_dataset.py 1000

# Test with large data
curl -X POST http://localhost:8000/analytics/query \
  -H 'Content-Type: application/json' \
  -d '{
    "query_type": "preview",
    "table": "Inventory_large",
    "limit": 100
  }'
```

Expected response time: <500ms for preview mode