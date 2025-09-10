"""
Debug endpoint for troubleshooting data issues
"""
from fastapi import APIRouter
from ..engine import duck
import logging

router = APIRouter(prefix="/debug", tags=["debug"])
logger = logging.getLogger(__name__)

@router.get("/data-status")
def data_status():
    """Check data loading status and sample data"""
    try:
        # Ensure views
        created = duck.ensure_views()
        
        # Get connection
        conn = duck.get_conn()
        
        # Check each table
        status = {
            "views_created": created,
            "tables": {},
            "sample_data": {},
            "date_analysis": {}
        }
        
        tables = ["Customer", "Inventory", "Detail", "Pricelist"]
        for table in tables:
            try:
                # Count rows
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                status["tables"][table] = {"count": count}
                
                # Get sample data
                sample = conn.execute(f"SELECT * FROM {table} LIMIT 2").fetchall()
                status["sample_data"][table] = [str(row) for row in sample]
                
            except Exception as e:
                status["tables"][table] = {"error": str(e)}
        
        # Analyze dates in Inventory
        try:
            dates = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    MIN(order_date) as min_date,
                    MAX(order_date) as max_date
                FROM Inventory
            """).fetchone()
            
            status["date_analysis"]["inventory"] = {
                "total_orders": dates[0],
                "min_date": str(dates[1]),
                "max_date": str(dates[2])
            }
            
            # Test date filtering
            test_result = conn.execute("""
                SELECT COUNT(*) 
                FROM Inventory 
                WHERE CAST(order_date AS DATE) BETWEEN '2024-07-01' AND '2024-09-30'
            """).fetchone()[0]
            
            status["date_analysis"]["test_filter_2024_q3"] = test_result
            
        except Exception as e:
            status["date_analysis"]["error"] = str(e)
        
        return status
        
    except Exception as e:
        return {"error": str(e)}

@router.get("/test-queries")
def test_queries():
    """Test common queries and return results"""
    try:
        duck.ensure_views()
        conn = duck.get_conn()
        
        results = {}
        
        # Test revenue query
        try:
            revenue = conn.execute("""
                SELECT SUM(order_total) as total
                FROM Inventory
                WHERE CAST(order_date AS DATE) BETWEEN '2024-07-01' AND '2024-09-30'
            """).fetchone()
            results["revenue_q3_2024"] = float(revenue[0]) if revenue[0] else 0
        except Exception as e:
            results["revenue_q3_2024"] = f"ERROR: {e}"
        
        # Test top products
        try:
            products = conn.execute("""
                SELECT Detail.product_id,
                       SUM(Detail.qty * Detail.unit_price) AS total_revenue
                FROM Detail
                GROUP BY Detail.product_id
                ORDER BY total_revenue DESC
                LIMIT 5
            """).fetchall()
            results["top_5_products"] = [
                {"product": row[0], "revenue": float(row[1]) if row[1] else 0}
                for row in products
            ]
        except Exception as e:
            results["top_5_products"] = f"ERROR: {e}"
        
        # Test customer orders
        try:
            orders = conn.execute("""
                SELECT IID, order_date, order_total
                FROM Inventory
                WHERE CID = 1001
                ORDER BY order_date DESC
            """).fetchall()
            results["orders_cid_1001"] = [
                {"iid": row[0], "date": str(row[1]), "total": float(row[2]) if row[2] else 0}
                for row in orders
            ]
        except Exception as e:
            results["orders_cid_1001"] = f"ERROR: {e}"
        
        # Test order details
        try:
            details = conn.execute("""
                SELECT DID, product_id, qty, unit_price
                FROM Detail
                WHERE IID = 2001
            """).fetchall()
            results["details_iid_2001"] = [
                {"did": row[0], "product": row[1], "qty": row[2], "price": float(row[3]) if row[3] else 0}
                for row in details
            ]
        except Exception as e:
            results["details_iid_2001"] = f"ERROR: {e}"
        
        return results
        
    except Exception as e:
        return {"error": str(e)}