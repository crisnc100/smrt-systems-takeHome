"""
Data quality validation and confidence scoring.
"""
from typing import Dict, List, Tuple, Any
from ..engine import duck


def calculate_data_quality_metrics() -> Dict[str, Any]:
    """
    Calculate data quality metrics for the entire dataset.
    Returns orphan rates, null percentages, and other quality indicators.
    """
    metrics = {}
    
    try:
        # Check for orphaned records
        orphan_inventories = duck.query_with_timeout(
            "SELECT COUNT(*) FROM Inventory WHERE CID NOT IN (SELECT CID FROM Customer)", 
            (), timeout_s=2.0
        )[0][0]
        
        orphan_details = duck.query_with_timeout(
            "SELECT COUNT(*) FROM Detail WHERE IID NOT IN (SELECT IID FROM Inventory)", 
            (), timeout_s=2.0
        )[0][0]
        
        orphan_price_refs = duck.query_with_timeout(
            "SELECT COUNT(*) FROM Detail WHERE price_table_item_id NOT IN (SELECT price_table_item_id FROM Pricelist)", 
            (), timeout_s=2.0
        )[0][0]
        
        total_inventories = duck.query_with_timeout("SELECT COUNT(*) FROM Inventory", (), timeout_s=2.0)[0][0]
        total_details = duck.query_with_timeout("SELECT COUNT(*) FROM Detail", (), timeout_s=2.0)[0][0]
        
        metrics['orphan_inventory_rate'] = orphan_inventories / max(total_inventories, 1)
        metrics['orphan_detail_rate'] = orphan_details / max(total_details, 1)
        metrics['orphan_price_rate'] = orphan_price_refs / max(total_details, 1)
        
        # Check for negative values
        negative_totals = duck.query_with_timeout(
            "SELECT COUNT(*) FROM Inventory WHERE order_total < 0", 
            (), timeout_s=2.0
        )[0][0]
        
        negative_prices = duck.query_with_timeout(
            "SELECT COUNT(*) FROM Detail WHERE unit_price < 0", 
            (), timeout_s=2.0
        )[0][0]
        
        metrics['negative_totals'] = negative_totals
        metrics['negative_prices'] = negative_prices
        
        # Check for null values in critical fields
        null_dates = duck.query_with_timeout(
            "SELECT COUNT(*) FROM Inventory WHERE order_date IS NULL", 
            (), timeout_s=2.0
        )[0][0]
        
        metrics['null_date_rate'] = null_dates / max(total_inventories, 1)
        
    except Exception as e:
        metrics['error'] = str(e)
    
    return metrics


def calculate_confidence(
    validations: List[Dict[str, Any]], 
    rows_found: int, 
    tables_used: List[str],
    quality_metrics: Dict[str, Any] = None
) -> Tuple[float, List[Dict[str, str]]]:
    """
    Calculate confidence score based on validations and data quality.
    Returns (confidence_score, quality_badges)
    """
    confidence = 0.75  # Start with moderate confidence (more realistic for demo)
    badges = []
    
    # Check validation results
    for v in validations:
        if v.get("status") != "pass":
            confidence -= 0.3
            badges.append({
                "type": "warning",
                "label": f"Validation: {v.get('name', 'unknown')}",
                "severity": "medium"
            })
    
    # Check if we found data
    if rows_found == 0:
        confidence -= 0.5
        badges.append({
            "type": "warning",
            "label": "No data found",
            "severity": "high"
        })
    
    # Get quality metrics if not provided
    if quality_metrics is None:
        quality_metrics = calculate_data_quality_metrics()
    
    # Check orphan rates
    if quality_metrics.get('orphan_inventory_rate', 0) > 0.1:
        confidence -= 0.1
        badges.append({
            "type": "info",
            "label": f"Orphan orders: {quality_metrics['orphan_inventory_rate']:.0%}",
            "severity": "low"
        })
    
    if quality_metrics.get('orphan_detail_rate', 0) > 0.1:
        confidence -= 0.1
        badges.append({
            "type": "info",
            "label": f"Orphan details: {quality_metrics['orphan_detail_rate']:.0%}",
            "severity": "low"
        })
    
    if quality_metrics.get('orphan_price_rate', 0) > 0.1:
        confidence -= 0.1
        badges.append({
            "type": "warning",
            "label": f"Missing prices: {quality_metrics['orphan_price_rate']:.0%}",
            "severity": "medium"
        })
    
    # Check for negative values
    if quality_metrics.get('negative_totals', 0) > 0:
        confidence -= 0.15
        badges.append({
            "type": "warning",
            "label": f"Negative totals: {quality_metrics['negative_totals']}",
            "severity": "medium"
        })
    
    if quality_metrics.get('negative_prices', 0) > 0:
        confidence -= 0.15
        badges.append({
            "type": "warning",
            "label": f"Negative prices: {quality_metrics['negative_prices']}",
            "severity": "medium"
        })
    
    # Check for null dates
    if quality_metrics.get('null_date_rate', 0) > 0.05:
        confidence -= 0.05
        badges.append({
            "type": "info",
            "label": f"Missing dates: {quality_metrics['null_date_rate']:.0%}",
            "severity": "low"
        })
    
    # Add positive badges for good data quality
    if len(badges) == 0:
        badges.append({
            "type": "success",
            "label": "High data quality",
            "severity": "none"
        })
        
    # Ensure confidence stays in valid range
    confidence = max(0.1, min(1.0, confidence))
    
    return confidence, badges


def get_follow_up_suggestions(intent: str, params: List[Any]) -> List[str]:
    """
    Generate intelligent follow-up suggestions based on the query.
    """
    suggestions = []
    
    if intent == "revenue_by_period":
        suggestions = [
            "Compare to previous period",
            "Show top products this period",
            "Show top customers this period",
            "Break down by month"
        ]
    elif intent == "orders_by_customer":
        if params and params[0]:
            cid = params[0]
            suggestions = [
                f"Total revenue for CID {cid}",
                f"Most purchased products by CID {cid}",
                "Compare to other customers",
                "Show order trend over time"
            ]
    elif intent == "top_products":
        suggestions = [
            "Show revenue trend for top product",
            "Compare product performance by quarter",
            "Show customers buying these products",
            "Analyze pricing effectiveness"
        ]
    elif intent == "order_details":
        if params and params[0]:
            iid = params[0]
            suggestions = [
                f"Customer info for order {iid}",
                f"Similar orders to {iid}",
                "Product performance in this order",
                "Order timeline analysis"
            ]
    else:
        suggestions = [
            "Revenue last 30 days",
            "Top 5 products",
            "Top customers",
            "Recent orders"
        ]
    
    return suggestions[:4]  # Limit to 4 suggestions