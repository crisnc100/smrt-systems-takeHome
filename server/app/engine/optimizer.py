"""
Query optimization for large datasets
"""
import logging
from typing import Dict, Any, Tuple, List
from datetime import date, timedelta

logger = logging.getLogger(__name__)

class QueryOptimizer:
    """Optimizes queries for large datasets"""
    
    @staticmethod
    def optimize_date_range(from_date: date, to_date: date, row_estimate: int) -> Tuple[date, date, str]:
        """
        Optimize date range based on estimated data size.
        Returns (optimized_from, optimized_to, warning_message)
        """
        days_span = (to_date - from_date).days
        
        # If querying more than 90 days on large dataset, suggest narrowing
        if days_span > 90 and row_estimate > 100000:
            # Suggest last 30 days instead
            suggested_from = to_date - timedelta(days=30)
            warning = f"Large date range ({days_span} days) on {row_estimate:,} rows. Consider narrowing to last 30 days for better performance."
            return suggested_from, to_date, warning
        
        return from_date, to_date, ""
    
    @staticmethod
    def add_sampling_clause(sql: str, sample_rate: float = 0.1) -> str:
        """
        Add TABLESAMPLE clause for preview queries on large datasets.
        DuckDB supports: TABLESAMPLE BERNOULLI(percentage)
        """
        if sample_rate >= 1.0:
            return sql
        
        # Add sampling to FROM clause
        percentage = sample_rate * 100
        return sql.replace("FROM ", f"FROM TABLESAMPLE BERNOULLI({percentage}) ")
    
    @staticmethod
    def suggest_indexes(table: str, columns: List[str]) -> List[str]:
        """
        Suggest indexes for frequently queried columns
        """
        suggestions = []
        
        # Common index patterns
        if table == "Inventory":
            if "order_date" in columns:
                suggestions.append("CREATE INDEX idx_inventory_date ON Inventory(order_date)")
            if "CID" in columns:
                suggestions.append("CREATE INDEX idx_inventory_cid ON Inventory(CID)")
        
        elif table == "Detail":
            if "IID" in columns:
                suggestions.append("CREATE INDEX idx_detail_iid ON Detail(IID)")
            if "product_id" in columns:
                suggestions.append("CREATE INDEX idx_detail_product ON Detail(product_id)")
        
        return suggestions
    
    @staticmethod
    def estimate_query_cost(sql: str, row_count: int) -> Dict[str, Any]:
        """
        Estimate query cost and suggest optimizations
        """
        cost = {
            "estimated_rows_scanned": row_count,
            "estimated_time_ms": 0,
            "optimization_hints": []
        }
        
        # Rough estimates based on operation types
        if "GROUP BY" in sql.upper():
            cost["estimated_time_ms"] = row_count * 0.01  # 0.01ms per row for aggregation
            if row_count > 1000000:
                cost["optimization_hints"].append("Consider pre-aggregating data for frequent GROUP BY queries")
        
        if "JOIN" in sql.upper():
            cost["estimated_time_ms"] = row_count * 0.02  # 0.02ms per row for joins
            if row_count > 500000:
                cost["optimization_hints"].append("Consider denormalizing frequently joined tables")
        
        if cost["estimated_time_ms"] > 2000:
            cost["optimization_hints"].append("Query may timeout. Consider adding more specific filters")
        
        return cost
    
    @staticmethod
    def partition_strategy(table: str, row_count: int) -> Dict[str, Any]:
        """
        Suggest partitioning strategy for very large tables
        """
        if row_count < 1000000:
            return {"needs_partitioning": False}
        
        strategies = {
            "Inventory": {
                "needs_partitioning": True,
                "partition_by": "YEAR(order_date)",
                "reason": "Partition by year for time-based queries"
            },
            "Detail": {
                "needs_partitioning": True,
                "partition_by": "HASH(IID, 10)",
                "reason": "Hash partition on IID for parallel processing"
            },
            "Customer": {
                "needs_partitioning": row_count > 5000000,
                "partition_by": "RANGE(CID)",
                "reason": "Range partition on customer ID"
            }
        }
        
        return strategies.get(table, {"needs_partitioning": False})