"""
Analytics endpoint for large dataset queries with optimization
"""
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from ..engine import duck
from ..engine.optimizer import QueryOptimizer
from ..validators import guards

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)


class AnalyticsRequest(BaseModel):
    query_type: str  # "preview", "full", "aggregate"
    table: str
    filters: Optional[Dict[str, Any]] = None
    limit: int = 1000
    sample_rate: Optional[float] = None  # For preview mode


class AnalyticsResponse(BaseModel):
    data: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    performance: Dict[str, Any]
    suggestions: List[str]


@router.post("/query")
def analytics_query(req: AnalyticsRequest):
    """
    Optimized query endpoint for large datasets
    """
    try:
        duck.ensure_views()
        conn = duck.get_conn()
        
        # Get table statistics
        table_count = conn.execute(f"SELECT COUNT(*) FROM {req.table}").fetchone()[0]
        
        metadata = {
            "table": req.table,
            "total_rows": table_count,
            "query_type": req.query_type
        }
        
        suggestions = []
        
        # Build base query
        if req.query_type == "preview":
            # Use sampling for preview
            sample_rate = req.sample_rate or min(10000 / max(table_count, 1), 1.0)
            sql = f"SELECT * FROM {req.table} TABLESAMPLE BERNOULLI({sample_rate * 100})"
            metadata["sample_rate"] = sample_rate
            suggestions.append(f"Showing {sample_rate:.1%} sample of data")
            
        elif req.query_type == "aggregate":
            # Optimized aggregation query
            if req.table == "Inventory":
                sql = """
                    SELECT 
                        DATE_TRUNC('month', order_date) as month,
                        COUNT(*) as order_count,
                        SUM(order_total) as total_revenue,
                        AVG(order_total) as avg_order_value
                    FROM Inventory
                    GROUP BY month
                    ORDER BY month DESC
                """
            elif req.table == "Detail":
                sql = """
                    SELECT 
                        product_id,
                        COUNT(*) as order_count,
                        SUM(qty) as total_quantity,
                        SUM(qty * unit_price) as total_revenue
                    FROM Detail
                    GROUP BY product_id
                    ORDER BY total_revenue DESC
                """
            else:
                sql = f"SELECT COUNT(*) as count FROM {req.table}"
                
        else:  # full query
            sql = f"SELECT * FROM {req.table}"
            if table_count > 100000:
                suggestions.append("Consider using preview mode for large datasets")
        
        # Apply filters if provided
        if req.filters:
            where_clauses = []
            for key, value in req.filters.items():
                if isinstance(value, dict) and "from" in value and "to" in value:
                    where_clauses.append(f"{key} BETWEEN '{value['from']}' AND '{value['to']}'")
                else:
                    where_clauses.append(f"{key} = '{value}'")
            
            if where_clauses:
                if "WHERE" in sql:
                    sql += " AND " + " AND ".join(where_clauses)
                else:
                    sql += " WHERE " + " AND ".join(where_clauses)
        
        # Apply limit
        sql = guards.enforce_limit(sql, req.limit)
        
        # Estimate query cost
        optimizer = QueryOptimizer()
        cost_estimate = optimizer.estimate_query_cost(sql, table_count)
        
        # Execute with timeout
        import time
        start_time = time.time()
        
        try:
            rows = duck.query_with_timeout(sql, (), timeout_s=5.0)
            execution_time = (time.time() - start_time) * 1000
            
            # Convert to dict format
            if rows:
                # Get column names from first query
                columns = conn.execute(f"SELECT * FROM {req.table} LIMIT 0").description
                col_names = [col[0] for col in columns]
                
                data = [dict(zip(col_names, row)) for row in rows[:req.limit]]
            else:
                data = []
            
            performance = {
                "execution_time_ms": execution_time,
                "rows_returned": len(data),
                "rows_scanned": cost_estimate["estimated_rows_scanned"],
                "optimizations_applied": ["parquet_cache", "columnar_storage"]
            }
            
            # Add optimization hints
            suggestions.extend(cost_estimate.get("optimization_hints", []))
            
            # Check if partitioning would help
            partition_strategy = optimizer.partition_strategy(req.table, table_count)
            if partition_strategy.get("needs_partitioning"):
                suggestions.append(f"Consider partitioning: {partition_strategy.get('reason')}")
            
            return AnalyticsResponse(
                data=data,
                metadata=metadata,
                performance=performance,
                suggestions=suggestions
            )
            
        except TimeoutError:
            raise HTTPException(
                status_code=503,
                detail="Query timeout. Try using preview mode or adding more specific filters."
            )
            
    except Exception as e:
        logger.error(f"Analytics query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{table}")
def table_statistics(table: str):
    """
    Get detailed statistics for a table
    """
    try:
        duck.ensure_views()
        conn = duck.get_conn()
        
        # Basic stats
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        
        stats = {
            "table": table,
            "row_count": count,
            "columns": [],
            "performance_tips": []
        }
        
        # Get column info
        columns = conn.execute(f"SELECT * FROM {table} LIMIT 0").description
        for col in columns:
            col_name = col[0]
            
            # Get basic stats for each column
            col_stats = {
                "name": col_name,
                "type": str(col[1]),
                "null_count": conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {col_name} IS NULL").fetchone()[0],
                "distinct_count": conn.execute(f"SELECT COUNT(DISTINCT {col_name}) FROM {table}").fetchone()[0]
            }
            
            stats["columns"].append(col_stats)
        
        # Performance recommendations
        if count > 100000:
            stats["performance_tips"].append("Use preview mode for exploratory queries")
            stats["performance_tips"].append("Apply date filters to reduce data scanned")
        
        if count > 1000000:
            stats["performance_tips"].append("Consider partitioning by date or key columns")
            stats["performance_tips"].append("Use aggregate queries instead of full scans")
        
        return stats
        
    except Exception as e:
        logger.error(f"Stats error for {table}: {e}")
        raise HTTPException(status_code=500, detail=str(e))