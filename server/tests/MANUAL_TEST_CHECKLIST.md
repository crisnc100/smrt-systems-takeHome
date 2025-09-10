# Query Logic Manual Test Checklist

## Prerequisites
- [ ] Server is running (`python -m uvicorn app.main:app --reload`)
- [ ] Mock data is loaded (Customer.csv, Inventory.csv, Detail.csv, Pricelist.csv)
- [ ] Mobile app or API client is connected to backend

## Intent Detection Tests

### Revenue Queries
- [ ] ✅ "revenue last 30 days" → Returns revenue data for last 30 days
- [ ] ✅ "sales this month" → Returns current month revenue
- [ ] ✅ "Revenue for last month" → Returns previous month revenue
- [ ] ❌ "last 30 days" → Should NOT match (missing revenue keyword)
- [ ] ❌ "30 days revenue" → Verify proper date parsing

### Top Products
- [ ] ✅ "top 5 products" → Returns 5 best-selling products
- [ ] ✅ "Top 10 products" → Returns 10 products
- [ ] ✅ "best selling products" → Returns default top 10
- [ ] ❌ "products" → Should NOT match (missing "top" qualifier)

### Customer Orders
- [ ] ✅ "orders for CID 1001" → Returns orders for customer 1001
- [ ] ✅ "Orders CID 1002" → Returns orders for customer 1002
- [ ] ✅ "show orders 1001" → Correctly extracts CID
- [ ] ❌ "orders" → Should NOT match (missing CID)

### Order Details
- [ ] ✅ "order details IID 2001" → Returns details for order 2001
- [ ] ✅ "details for 2002" → Returns details for order 2002
- [ ] ✅ "Order details 2003" → Case insensitive matching
- [ ] ❌ "details" → Should NOT match (missing IID)

## SQL Safety Tests

### Injection Prevention
- [ ] ❌ "DROP TABLE Customer" → Blocked
- [ ] ❌ "DELETE FROM Inventory" → Blocked
- [ ] ❌ "UPDATE Detail SET price = 0" → Blocked
- [ ] ❌ "INSERT INTO Customer VALUES" → Blocked
- [ ] ❌ "; DROP TABLE" in any query → Blocked

### Safe Queries
- [ ] ✅ SELECT queries pass through
- [ ] ✅ Queries with WHERE clauses work
- [ ] ✅ GROUP BY queries work
- [ ] ✅ JOIN queries work
- [ ] ✅ Aggregate functions (SUM, COUNT, AVG) work

## Data Quality Tests

### Relationships
- [ ] No orphaned orders (all CIDs in Inventory exist in Customer)
- [ ] No orphaned details (all IIDs in Detail exist in Inventory)
- [ ] All price_table_item_ids in Detail exist in Pricelist

### Calculations
- [ ] Order totals in Inventory roughly match sum of Detail items
- [ ] Revenue calculations are consistent across different queries
- [ ] Date filtering properly includes/excludes records

## Performance Tests

### Response Times
- [ ] Small queries (<100 rows) return in <500ms
- [ ] Medium queries (100-1000 rows) return in <1s
- [ ] Large queries (>1000 rows) have LIMIT applied

### Caching
- [ ] Repeated identical queries are faster (cache hit)
- [ ] Cache invalidates when data changes

## Edge Cases

### Ambiguous Inputs
- [ ] "show me 1001" → No match (ambiguous)
- [ ] "details" → No match (too vague)
- [ ] "revenue" → No match (missing time period)

### Special Characters
- [ ] Queries with punctuation work correctly
- [ ] Queries with numbers in various formats work
- [ ] Case variations are handled properly

### Empty Results
- [ ] Queries with no matching data return proper message
- [ ] Out-of-range dates return "no matching rows"
- [ ] Non-existent CIDs/IIDs return appropriate response

## Error Handling

### Timeout Protection
- [ ] Very slow queries timeout after 5 seconds
- [ ] Timeout returns user-friendly error message

### Malformed Queries
- [ ] Invalid SQL syntax returns error (not crash)
- [ ] Invalid date formats are handled gracefully
- [ ] Missing required parameters return helpful message

## Large Dataset Tests (if using generated data)

### Sampling
- [ ] Preview mode returns sample quickly
- [ ] Sample is representative of full dataset

### Pagination
- [ ] Large results are paginated properly
- [ ] Next/previous page navigation works

### Optimization
- [ ] Date range queries use indexes effectively
- [ ] Aggregate queries don't scan unnecessary rows

---

## Test Results Summary

- **Intent Detection**: _/20 tests passed
- **SQL Safety**: _/10 tests passed  
- **Data Quality**: _/6 tests passed
- **Performance**: _/5 tests passed
- **Edge Cases**: _/9 tests passed
- **Error Handling**: _/6 tests passed
- **Large Dataset**: _/6 tests passed (if applicable)

**Total**: _/62 tests passed

## Notes
- Record any issues or unexpected behavior here
- Note performance bottlenecks
- Document any data quality issues found