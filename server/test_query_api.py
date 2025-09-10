#!/usr/bin/env python3
"""
API test suite using only built-in libraries
"""
import urllib.request
import urllib.error
import json
import sys

BASE_URL = "http://localhost:8000"

def test_query(message, should_succeed=True):
    """Test a single query against the API"""
    data = json.dumps({"message": message}).encode('utf-8')
    req = urllib.request.Request(
        f"{BASE_URL}/chat",
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode('utf-8'))
        
        if should_succeed:
            # Should get a valid response with SQL
            success = "sql" in result and "error" not in result
        else:
            # Got a successful response when we expected failure
            # Check if it's actually an error response
            success = "error" in result
    except urllib.error.HTTPError as e:
        result = json.loads(e.read().decode('utf-8'))
        if should_succeed:
            success = False
        else:
            # Error expected - this is good
            success = True
    
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: '{message[:50]}...' -> {'Success' if should_succeed else 'Error expected'}")
    
    if not success:
        print(f"    Response: {json.dumps(result)[:200]}")
    
    return success

def main():
    print("=" * 60)
    print("QUERY LOGIC API TESTS")
    print("=" * 60)
    print(f"Testing against: {BASE_URL}")
    print()
    
    # Check server is running
    try:
        response = urllib.request.urlopen(f"{BASE_URL}/health")
        if response.status != 200:
            print("❌ Server not responding on /health")
            sys.exit(1)
        print("✅ Server is running\n")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print(f"   Make sure server is running: python -m uvicorn app.main:app --reload")
        sys.exit(1)
    
    tests_passed = 0
    tests_failed = 0
    
    print("Testing VALID queries (should succeed):")
    print("-" * 40)
    
    valid_queries = [
        "revenue last 30 days",
        "sales last month",
        "revenue for last 7 days",
        "top 5 products",
        "top 10 products",
        "best selling products",
        "orders for CID 1001",
        "Orders CID 1002",
        "show orders 1001",
        "order details IID 2001",
        "details for 2002",
        "Order details 2003",
    ]
    
    for query in valid_queries:
        if test_query(query, should_succeed=True):
            tests_passed += 1
        else:
            tests_failed += 1
    
    print("\nTesting INVALID queries (should fail):")
    print("-" * 40)
    
    invalid_queries = [
        "revenue",  # Missing time period
        "sales",  # Missing time period
        "products",  # Missing "top" qualifier
        "orders",  # Missing CID
        "details",  # Missing IID
        "show me 1001",  # Ambiguous
        "last 30 days",  # Missing revenue keyword
        "CID 1001",  # Missing "orders" keyword
    ]
    
    for query in invalid_queries:
        if test_query(query, should_succeed=False):
            tests_passed += 1
        else:
            tests_failed += 1
    
    print("\nTesting SQL INJECTION attempts (should fail):")
    print("-" * 40)
    
    injection_queries = [
        "DROP TABLE Customer",
        "DELETE FROM Inventory",
        "'; DROP TABLE Customer; --",
        "1 OR 1=1",
    ]
    
    for query in injection_queries:
        if test_query(query, should_succeed=False):
            tests_passed += 1
        else:
            tests_failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    total = tests_passed + tests_failed
    print(f"Tests run: {total}")
    print(f"Passed: {tests_passed} ✅")
    print(f"Failed: {tests_failed} ❌")
    
    if tests_failed == 0:
        print("\n🎉 All tests passed! Query logic is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {tests_failed} test(s) failed. Review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())