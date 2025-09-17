"""
Debug endpoint for troubleshooting data issues
"""
from datetime import date, timedelta
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
        
        # Get sample IDs for frontend suggestions
        sample_ids = {}
        try:
            # Get first IID from Inventory
            iid_result = conn.execute("SELECT IID FROM Inventory LIMIT 1").fetchone()
            sample_ids["first_iid"] = str(iid_result[0]) if iid_result else None
            
            # Get first CID from Customer
            cid_result = conn.execute("SELECT CID FROM Customer LIMIT 1").fetchone()
            sample_ids["first_cid"] = str(cid_result[0]) if cid_result else None
        except Exception:
            pass
        
        status["sample_ids"] = sample_ids
        
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

        def _to_date(value) -> date:
            if isinstance(value, date):
                return value
            return date.fromisoformat(str(value))

        # Revenue last 30 days – matches the primary chat prompt
        try:
            max_row = conn.execute("SELECT MAX(CAST(order_date AS DATE)) FROM Inventory").fetchone()
            if not max_row or not max_row[0]:
                raise ValueError("Inventory has no orders")
            max_date = _to_date(max_row[0])
            start_date = max_date - timedelta(days=29)
            revenue = conn.execute(
                """
                SELECT SUM(order_total) AS total, COUNT(*) AS orders
                FROM Inventory
                WHERE CAST(order_date AS DATE) BETWEEN ? AND ?
                """,
                (start_date, max_date),
            ).fetchone()
            total = float(revenue[0]) if revenue and revenue[0] is not None else 0.0
            order_count = int(revenue[1]) if revenue and revenue[1] is not None else 0
            if order_count == 0:
                raise ValueError("No orders in the last 30 days")
            results["revenue_last_30_days"] = {
                "amount": total,
                "orders": order_count,
                "start": start_date.isoformat(),
                "end": max_date.isoformat(),
            }
        except Exception as exc:  # pylint: disable=broad-except
            results["revenue_last_30_days"] = f"ERROR: {exc}"

        # Top 5 products
        try:
            products = conn.execute(
                """
                SELECT Detail.product_id,
                       SUM(Detail.qty * Detail.unit_price) AS total_revenue,
                       SUM(Detail.qty) AS total_qty
                FROM Detail
                GROUP BY Detail.product_id
                ORDER BY total_revenue DESC
                LIMIT 5
                """
            ).fetchall()
            if not products:
                raise ValueError("No product detail records")
            results["top_products"] = [
                {
                    "product": row[0],
                    "revenue": float(row[1]) if row[1] is not None else 0.0,
                    "qty": float(row[2]) if row[2] is not None else 0.0,
                }
                for row in products
            ]
        except Exception as exc:  # pylint: disable=broad-except
            results["top_products"] = f"ERROR: {exc}"

        # Top customers by revenue
        try:
            customers = conn.execute(
                """
                SELECT COALESCE(c.name, CAST(i.CID AS VARCHAR)) AS customer,
                       i.CID,
                       SUM(i.order_total) AS revenue
                FROM Inventory i
                LEFT JOIN Customer c ON c.CID = i.CID
                GROUP BY customer, i.CID
                ORDER BY revenue DESC
                LIMIT 5
                """
            ).fetchall()
            if not customers:
                raise ValueError("No customer revenue found")
            results["top_customers"] = [
                {
                    "customer": row[0],
                    "cid": row[1],
                    "revenue": float(row[2]) if row[2] is not None else 0.0,
                }
                for row in customers
            ]
        except Exception as exc:  # pylint: disable=broad-except
            results["top_customers"] = f"ERROR: {exc}"

        # Orders for a representative CID (prefer one with recent activity)
        try:
            cid_row = conn.execute(
                """
                SELECT CID
                FROM Inventory
                WHERE CID IS NOT NULL
                GROUP BY CID
                ORDER BY COUNT(*) DESC
                LIMIT 1
                """
            ).fetchone()
            if not cid_row:
                raise ValueError("No customers with orders found")
            cid = cid_row[0]
            orders = conn.execute(
                """
                SELECT IID, order_date, order_total
                FROM Inventory
                WHERE CID = ?
                ORDER BY order_date DESC
                LIMIT 10
                """,
                (cid,),
            ).fetchall()
            if not orders:
                raise ValueError(f"CID {cid} has no orders")
            results[f"orders_cid_{cid}"] = [
                {
                    "iid": row[0],
                    "date": str(row[1]),
                    "total": float(row[2]) if row[2] is not None else 0.0,
                }
                for row in orders
            ]
        except Exception as exc:  # pylint: disable=broad-except
            results["orders_sample"] = f"ERROR: {exc}"

        # Order details for a representative IID
        try:
            iid_row = conn.execute(
                """
                SELECT IID
                FROM Detail
                GROUP BY IID
                ORDER BY COUNT(*) DESC
                LIMIT 1
                """
            ).fetchone()
            if not iid_row:
                raise ValueError("No order details found")
            iid = iid_row[0]
            details = conn.execute(
                """
                SELECT DID, product_id, qty, unit_price, (qty * unit_price) AS line_total
                FROM Detail
                WHERE IID = ?
                ORDER BY DID
                LIMIT 15
                """,
                (iid,),
            ).fetchall()
            if not details:
                raise ValueError(f"Order {iid} has no line items")
            results[f"details_iid_{iid}"] = [
                {
                    "did": row[0],
                    "product": row[1],
                    "qty": float(row[2]) if row[2] is not None else 0.0,
                    "price": float(row[3]) if row[3] is not None else 0.0,
                    "line_total": float(row[4]) if row[4] is not None else 0.0,
                }
                for row in details
            ]
        except Exception as exc:  # pylint: disable=broad-except
            results["details_sample"] = f"ERROR: {exc}"

        return results
        
    except Exception as e:
        return {"error": str(e)}
