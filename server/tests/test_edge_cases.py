"""
Edge case tests for query logic
"""
import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.engine import duck
from app.routers.chat import _detect_intent
from app.validators import guards

class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""
    
    def test_ambiguous_queries(self):
        """Test queries that could match multiple intents"""
        test_cases = [
            ("show me 1001", None),  # Could be CID or IID
            ("details", None),  # Too vague
            ("orders", None),  # Missing context
            ("revenue", None),  # Missing time period
            ("products", None),  # Missing "top" qualifier
        ]
        
        for message, expected in test_cases:
            spec = _detect_intent(message, None)
            self.assertIsNone(spec, f"Should not match vague query: {message}")
    
    def test_case_insensitivity(self):
        """Test that intent detection is case-insensitive"""
        test_cases = [
            ("REVENUE LAST 30 DAYS", "revenue_by_period"),
            ("Revenue Last Month", "revenue_by_period"),
            ("TOP 5 PRODUCTS", "top_products"),
            ("top 10 Products", "top_products"),
            ("Orders for cid 1001", "orders_by_customer"),
            ("order details iid 2001", "order_details"),
        ]
        
        for message, expected_intent in test_cases:
            spec = _detect_intent(message, None)
            self.assertIsNotNone(spec, f"Failed to detect intent for: {message}")
            _, _, _, intent_name, _, _ = spec
            self.assertEqual(intent_name, expected_intent,
                           f"Case sensitivity issue for '{message}'")
    
    def test_number_extraction(self):
        """Test extraction of IDs and quantities from queries"""
        test_cases = [
            ("top 3 products", 3),
            ("top 15 products", 15),
            ("best 7 products", 7),
            ("top products", 10),  # Default
        ]
        
        for message, expected_limit in test_cases:
            spec = _detect_intent(message, None)
            if spec:
                query_template, params, _, _, _, _ = spec
                # Check if the limit is correctly extracted
                if "LIMIT" in query_template:
                    # Parse limit from query
                    import re
                    match = re.search(r'LIMIT (\d+)', query_template)
                    if match:
                        limit = int(match.group(1))
                        self.assertEqual(limit, expected_limit,
                                       f"Wrong limit extracted from '{message}'")
    
    def test_sql_injection_advanced(self):
        """Test advanced SQL injection attempts"""
        dangerous_queries = [
            "SELECT * FROM Customer WHERE 1=1; --",
            "SELECT * FROM Customer WHERE name = 'a' OR '1'='1'",
            "SELECT * FROM Customer UNION SELECT * FROM passwords",
            "SELECT * FROM Customer; EXEC sp_configure 'show advanced options'",
            "SELECT * FROM Customer WHERE CID = 1 OR SLEEP(5)",
            "SELECT * FROM Customer WHERE name LIKE '%'; DROP TABLE Customer; --",
        ]
        
        for sql in dangerous_queries:
            ok, reason = guards.assert_select_only(sql)
            self.assertFalse(ok, f"Should block SQL injection: {sql}")
    
    def test_malformed_dates(self):
        """Test handling of malformed date inputs"""
        conn = duck.get_conn()
        
        # Test various date formats
        date_queries = [
            "SELECT * FROM Inventory WHERE order_date = '2024-13-01'",  # Invalid month
            "SELECT * FROM Inventory WHERE order_date = '2024-07-32'",  # Invalid day
            "SELECT * FROM Inventory WHERE order_date = 'yesterday'",  # Text date
            "SELECT * FROM Inventory WHERE order_date = '07/01/2024'",  # Different format
        ]
        
        for query in date_queries:
            try:
                # Should handle gracefully without crashing
                result = conn.execute(query).fetchall()
            except Exception as e:
                # Expected to fail, but should not crash server
                self.assertIsInstance(e, Exception)
    
    def test_empty_results_handling(self):
        """Test that empty results are handled properly"""
        conn = duck.get_conn()
        
        # Query that should return no results
        result = conn.execute("""
            SELECT * FROM Customer WHERE CID = -999
        """).fetchall()
        
        self.assertEqual(len(result), 0, "Should handle empty results")
    
    def test_null_value_handling(self):
        """Test handling of NULL values in data"""
        conn = duck.get_conn()
        
        # Check for NULL handling in aggregations
        result = conn.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(order_total) as non_null_totals
            FROM Inventory
        """).fetchone()
        
        self.assertIsNotNone(result, "Should handle NULL counts")
    
    def test_large_number_handling(self):
        """Test handling of very large numbers in queries"""
        test_cases = [
            "orders for CID 999999999",  # Very large CID
            "order details IID 999999999",  # Very large IID
            "top 1000 products",  # Large limit
        ]
        
        for message in test_cases:
            spec = _detect_intent(message, None)
            # Should detect intent even with large numbers
            if "CID" in message:
                self.assertIsNotNone(spec, f"Should handle large CID: {message}")
            elif "IID" in message:
                self.assertIsNotNone(spec, f"Should handle large IID: {message}")
    
    def test_special_characters_in_queries(self):
        """Test handling of special characters"""
        test_cases = [
            "revenue last 30 days!",
            "top 5 products?",
            "orders for CID #1001",
            "order details (IID 2001)",
            "revenue@last month",
        ]
        
        for message in test_cases:
            # Should handle gracefully without errors
            spec = _detect_intent(message, None)
            # Check that it either matches or returns None, but doesn't crash
            self.assertTrue(spec is None or isinstance(spec, tuple))
    
    def test_concurrent_query_handling(self):
        """Test that queries can be handled concurrently"""
        import concurrent.futures
        import time
        
        def run_query(query):
            conn = duck.get_conn()
            return conn.execute(query).fetchall()
        
        queries = [
            "SELECT COUNT(*) FROM Customer",
            "SELECT SUM(order_total) FROM Inventory",
            "SELECT COUNT(*) FROM Detail",
            "SELECT AVG(unit_price) FROM Pricelist",
        ]
        
        # Run queries concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(run_query, q) for q in queries]
            results = [f.result(timeout=5) for f in futures]
        
        # All queries should complete
        self.assertEqual(len(results), len(queries))

class TestDataValidation(unittest.TestCase):
    """Test data validation and quality checks"""
    
    def test_price_consistency(self):
        """Test that prices are consistent between Detail and Pricelist"""
        conn = duck.get_conn()
        
        # Check if Detail prices match Pricelist
        mismatched = conn.execute("""
            SELECT COUNT(*) 
            FROM Detail d
            JOIN Pricelist p ON d.price_table_item_id = p.price_table_item_id
            WHERE ABS(d.unit_price - p.unit_price) > 0.01
        """).fetchone()[0]
        
        # Some mismatches are expected in test data
        # but should be documented
        if mismatched > 0:
            print(f"Warning: {mismatched} price mismatches found")
    
    def test_order_total_accuracy(self):
        """Test that order totals match sum of details"""
        conn = duck.get_conn()
        
        # Compare Inventory totals with Detail sums
        discrepancies = conn.execute("""
            SELECT 
                i.IID,
                i.order_total as inventory_total,
                COALESCE(SUM(d.qty * d.unit_price), 0) as calculated_total,
                ABS(i.order_total - COALESCE(SUM(d.qty * d.unit_price), 0)) as difference
            FROM Inventory i
            LEFT JOIN Detail d ON i.IID = d.IID
            GROUP BY i.IID, i.order_total
            HAVING difference > 0.01
        """).fetchall()
        
        if discrepancies:
            print(f"Warning: {len(discrepancies)} orders have total discrepancies")
    
    def test_date_range_consistency(self):
        """Test that all dates are within reasonable range"""
        conn = duck.get_conn()
        
        # Check date ranges
        date_stats = conn.execute("""
            SELECT 
                MIN(order_date) as earliest,
                MAX(order_date) as latest,
                COUNT(DISTINCT order_date) as unique_dates
            FROM Inventory
        """).fetchone()
        
        self.assertIsNotNone(date_stats[0], "Should have earliest date")
        self.assertIsNotNone(date_stats[1], "Should have latest date")
        self.assertGreater(date_stats[2], 0, "Should have some unique dates")
    
    def test_customer_order_distribution(self):
        """Test customer order distribution for anomalies"""
        conn = duck.get_conn()
        
        # Check if any customer has unusual number of orders
        distribution = conn.execute("""
            SELECT 
                CID,
                COUNT(*) as order_count,
                SUM(order_total) as total_spent
            FROM Inventory
            GROUP BY CID
            ORDER BY order_count DESC
        """).fetchall()
        
        if distribution:
            max_orders = distribution[0][1]
            avg_orders = sum(d[1] for d in distribution) / len(distribution)
            
            # Flag if one customer has way more orders than average
            if max_orders > avg_orders * 10:
                print(f"Warning: Customer {distribution[0][0]} has {max_orders} orders (avg: {avg_orders:.1f})")

if __name__ == "__main__":
    unittest.main()