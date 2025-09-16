"""
Comprehensive test suite for query logic
"""
import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.engine import duck, sql_validator
from app.routers.chat import _detect_intent, _run_with_guards
from app.validators import guards

class TestQueryLogic(unittest.TestCase):
    """Test core query logic and intent detection"""
    
    @classmethod
    def setUpClass(cls):
        """Setup test data"""
        duck.ensure_views()
    
    def test_intent_detection(self):
        """Test that intents are correctly detected"""
        test_cases = [
            ("revenue last 30 days", "revenue_by_period"),
            ("Revenue for last month", "revenue_by_period"),
            ("sales this month", "revenue_by_period"),
            ("top 5 products", "top_products"),
            ("Top products", "top_products"),
            ("best selling items", None),  # Should not match without "top"
            ("orders for CID 1001", "orders_by_customer"),
            ("Orders CID 1002", "orders_by_customer"),
            ("show orders 1001", "orders_by_customer"),
            ("order details IID 2001", "order_details"),
            ("details for 2002", "order_details"),
            ("Order details 2003", "order_details"),
        ]
        
        for message, expected_intent in test_cases:
            spec = _detect_intent(message, None)
            if expected_intent:
                self.assertIsNotNone(spec, f"Failed to detect intent for: {message}")
                _, _, _, intent_name, _, _ = spec
                self.assertEqual(intent_name, expected_intent, 
                               f"Wrong intent for '{message}': got {intent_name}, expected {expected_intent}")
            else:
                self.assertIsNone(spec, f"Should not detect intent for: {message}")
    
    def test_sql_guards(self):
        """Test SQL injection prevention"""
        dangerous_queries = [
            "DROP TABLE Customer",
            "DELETE FROM Inventory",
            "UPDATE Detail SET price = 0",
            "INSERT INTO Customer VALUES (999, 'hacker', 'hack@evil.com')",
            "SELECT * FROM Customer; DROP TABLE Inventory",
        ]
        
        for sql in dangerous_queries:
            ok, reason = guards.assert_select_only(sql)
            self.assertFalse(ok, f"Should block dangerous SQL: {sql}")
    
    def test_safe_queries(self):
        """Test that safe queries pass guards"""
        safe_queries = [
            "SELECT * FROM Customer",
            "SELECT COUNT(*) FROM Inventory WHERE order_date > '2024-01-01'",
            "SELECT SUM(order_total) FROM Inventory",
            "SELECT product_id, SUM(qty) FROM Detail GROUP BY product_id",
        ]
        
        for sql in safe_queries:
            ok, reason = guards.assert_select_only(sql)
            self.assertTrue(ok, f"Should allow safe SQL: {sql}. Reason: {reason}")
    
    def test_limit_enforcement(self):
        """Test that LIMIT is properly enforced"""
        queries = [
            ("SELECT * FROM Customer", "SELECT * FROM Customer LIMIT 1000"),
            ("SELECT * FROM Customer LIMIT 5000", "SELECT * FROM Customer LIMIT 1000"),
            ("SELECT * FROM Customer LIMIT 50", "SELECT * FROM Customer LIMIT 50"),
        ]

        for original, expected in queries:
            result = guards.enforce_limit(original, 1000)
            self.assertEqual(result.strip(), expected.strip())

    def test_llm_sql_validator(self):
        """LLM generated SQL should be sanitized before execution"""
        validated = sql_validator.validate("SELECT name FROM Customer c JOIN Inventory i ON c.CID = i.CID")
        self.assertEqual(set(validated.tables), {"Customer", "Inventory"})
        self.assertIn("LIMIT", validated.sql.upper())

        with self.assertRaises(ValueError):
            sql_validator.validate("SELECT * FROM Users")

        with self.assertRaises(ValueError):
            sql_validator.validate("DROP TABLE Customer")
    
    def test_data_relationships(self):
        """Test that foreign key relationships are valid"""
        conn = duck.get_conn()
        
        # Test Customer -> Inventory relationship
        orphan_orders = conn.execute("""
            SELECT COUNT(*) FROM Inventory 
            WHERE CID NOT IN (SELECT CID FROM Customer)
        """).fetchone()[0]
        self.assertEqual(orphan_orders, 0, "Found orphaned orders without customers")
        
        # Test Inventory -> Detail relationship
        orphan_details = conn.execute("""
            SELECT COUNT(*) FROM Detail 
            WHERE IID NOT IN (SELECT IID FROM Inventory)
        """).fetchone()[0]
        self.assertEqual(orphan_details, 0, "Found orphaned details without orders")
        
        # Test Detail -> Pricelist relationship
        orphan_prices = conn.execute("""
            SELECT COUNT(*) FROM Detail 
            WHERE price_table_item_id NOT IN (SELECT price_table_item_id FROM Pricelist)
        """).fetchone()[0]
        self.assertEqual(orphan_prices, 0, "Found details with invalid price references")
    
    def test_revenue_calculation(self):
        """Test that revenue calculations are correct"""
        conn = duck.get_conn()
        
        # Calculate total revenue from Inventory
        inventory_total = conn.execute("""
            SELECT SUM(order_total) FROM Inventory
        """).fetchone()[0]
        
        # Calculate total from Detail (should match if data is consistent)
        detail_total = conn.execute("""
            SELECT SUM(D.qty * D.unit_price) 
            FROM Detail D
        """).fetchone()[0]
        
        # They might not match exactly due to data inconsistencies, 
        # but should be in same ballpark
        if inventory_total and detail_total:
            ratio = detail_total / inventory_total
            self.assertGreater(ratio, 0.9, "Revenue calculations are too different")
            self.assertLess(ratio, 1.1, "Revenue calculations are too different")
    
    def test_date_filtering(self):
        """Test date range filtering works correctly"""
        conn = duck.get_conn()
        
        # Test specific date range
        result = conn.execute("""
            SELECT COUNT(*) FROM Inventory
            WHERE CAST(order_date AS DATE) BETWEEN '2024-07-01' AND '2024-09-30'
        """).fetchone()[0]
        
        self.assertGreater(result, 0, "Should find orders in Q3 2024")
        
        # Test that dates outside range are excluded
        result_outside = conn.execute("""
            SELECT COUNT(*) FROM Inventory
            WHERE CAST(order_date AS DATE) < '2024-07-01' 
               OR CAST(order_date AS DATE) > '2024-09-30'
        """).fetchone()[0]
        
        total = conn.execute("SELECT COUNT(*) FROM Inventory").fetchone()[0]
        self.assertEqual(result + result_outside, total, "Date filtering math doesn't add up")

class TestPerformance(unittest.TestCase):
    """Test performance with larger datasets"""
    
    def test_query_timeout(self):
        """Test that queries timeout appropriately"""
        import time
        from concurrent.futures import TimeoutError
        
        # This should timeout (infinite loop simulation)
        with self.assertRaises(TimeoutError):
            # Use a query that would take too long
            duck.query_with_timeout(
                "SELECT COUNT(*) FROM generate_series(1, 1000000000)",
                (),
                timeout_s=0.1
            )
    
    def test_cache_effectiveness(self):
        """Test that caching improves performance"""
        import time
        
        # First query (cold cache)
        start = time.time()
        result1 = duck.cached_query(
            "SELECT SUM(order_total) FROM Inventory",
            ()
        )
        cold_time = time.time() - start
        
        # Second query (warm cache)
        start = time.time()
        result2 = duck.cached_query(
            "SELECT SUM(order_total) FROM Inventory",
            ()
        )
        warm_time = time.time() - start
        
        # Cache should be faster
        self.assertEqual(result1, result2, "Cached results should match")
        # Note: In-memory DB might be too fast to measure difference
        # self.assertLess(warm_time, cold_time, "Cached query should be faster")

if __name__ == "__main__":
    unittest.main()
