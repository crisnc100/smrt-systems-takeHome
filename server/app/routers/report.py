from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter
from pydantic import BaseModel

from ..engine import duck
from ..validators import guards


router = APIRouter(prefix="/report", tags=["report"])


class DateRange(BaseModel):
    from_: Optional[date] = None
    to: Optional[date] = None

    class Config:
        fields = {"from_": "from"}


class ReportRequest(BaseModel):
    type: str
    filters: Optional[Dict[str, Any]] = None


class ChartSeries(BaseModel):
    name: str
    data: List[Tuple[str, float]]


class Chart(BaseModel):
    type: str
    series: List[ChartSeries]


class ReportResponse(BaseModel):
    summary_text: str
    tables_used: List[str]
    sql: List[str]
    charts: List[Chart]


def _parse_date_range(filters: Optional[Dict[str, Any]]) -> DateRange:
    if filters and isinstance(filters.get("date_range"), dict):
        dr = filters["date_range"]
        f = dr.get("from") or dr.get("from_")
        t = dr.get("to")
        return DateRange(from_=date.fromisoformat(f) if f else None, to=date.fromisoformat(t) if t else None)
    # Default: last 12 months (approximate)
    to = date.today()
    frm = to.replace(day=1) - timedelta(days=365)
    return DateRange(from_=frm, to=to)


def _run_guarded(sql: str, params: Tuple[Any, ...] = ()) -> List[tuple]:
    ok, reason = guards.assert_select_only(sql)
    if not ok:
        raise ValueError(f"Guard failed: {reason}")
    w_ok, violations = guards.validate_whitelist(sql)
    if not w_ok:
        raise ValueError(f"Unknown columns referenced: {', '.join(violations)}")
    safe_sql = guards.enforce_limit(sql, 5000)
    try:
        return duck.cached_query(safe_sql, params)
    except Exception:
        return duck.query_with_timeout(safe_sql, params, timeout_s=2.0)


@router.post("")
def report(req: ReportRequest):
    try:
        duck.ensure_views()
        if req.type == "revenue_by_month":
            dr = _parse_date_range(req.filters)
            sql = (
                "SELECT strftime(Inventory.order_date, '%Y-%m') AS month, "
                "SUM(Inventory.order_total) AS revenue FROM Inventory "
                "WHERE CAST(Inventory.order_date AS DATE) BETWEEN ? AND ? "
                "GROUP BY month ORDER BY month"
            )
            rows = _run_guarded(sql, (dr.from_, dr.to))
            series = [(r[0], float(r[1]) if r[1] is not None else 0.0) for r in rows]
            total = sum(v for _, v in series)
            summary = f"Revenue by month between {dr.from_.isoformat()} and {dr.to.isoformat()}: ${total:,.2f}."
            return ReportResponse(
                summary_text=summary,
                tables_used=["Inventory"],
                sql=[sql],
                charts=[Chart(type="bar", series=[ChartSeries(name="Revenue", data=series)])],
            )

        if req.type == "top_customers":
            k = 5
            if req.filters and isinstance(req.filters.get("k"), int):
                k = max(1, min(1000, req.filters["k"]))
            # Group by the full expression to avoid binder errors
            sql = (
                "SELECT COALESCE(Customer.name, CAST(Inventory.CID AS VARCHAR)) AS customer, "
                "SUM(Inventory.order_total) AS revenue "
                "FROM Inventory LEFT JOIN Customer ON Customer.CID = Inventory.CID "
                "GROUP BY COALESCE(Customer.name, CAST(Inventory.CID AS VARCHAR)) "
                "ORDER BY revenue DESC LIMIT ?"
            )
            rows = _run_guarded(sql, (k,))
            series = [(str(r[0]), float(r[1]) if r[1] is not None else 0.0) for r in rows]
            summary = f"Top {len(series)} customers by revenue."
            return ReportResponse(
                summary_text=summary,
                tables_used=["Inventory", "Customer"],
                sql=[sql],
                charts=[Chart(type="bar", series=[ChartSeries(name="Revenue", data=series)])],
            )

        if req.type == "top_products":
            k = 5
            if req.filters and isinstance(req.filters.get("k"), int):
                k = max(1, min(1000, req.filters["k"]))
            dr = _parse_date_range(req.filters)
            
            # Get top products by revenue with date filtering
            sql = (
                "SELECT Detail.product_id, "
                "SUM(Detail.qty) AS total_qty, "
                "SUM(Detail.qty * Detail.unit_price) AS total_revenue "
                "FROM Detail "
                "JOIN Inventory ON Detail.IID = Inventory.IID "
                "WHERE CAST(Inventory.order_date AS DATE) BETWEEN ? AND ? "
                "GROUP BY Detail.product_id "
                "ORDER BY total_revenue DESC "
                "LIMIT ?"
            )
            rows = _run_guarded(sql, (dr.from_, dr.to, k))
            
            # Create two series - quantity and revenue
            qty_series = [(str(r[0]), float(r[1]) if r[1] is not None else 0.0) for r in rows]
            rev_series = [(str(r[0]), float(r[2]) if r[2] is not None else 0.0) for r in rows]
            
            total_revenue = sum(r[2] if r[2] is not None else 0.0 for r in rows)
            summary = f"Top {len(rows)} products by revenue ({dr.from_.isoformat()} to {dr.to.isoformat()}): ${total_revenue:,.2f} total."
            
            return ReportResponse(
                summary_text=summary,
                tables_used=["Detail", "Inventory"],
                sql=[sql],
                charts=[
                    Chart(type="bar", series=[
                        ChartSeries(name="Revenue", data=rev_series),
                        ChartSeries(name="Quantity", data=qty_series)
                    ])
                ],
            )

        if req.type == "revenue_trend":
            dr = _parse_date_range(req.filters)
            
            # Daily revenue trend
            sql = (
                "SELECT CAST(Inventory.order_date AS DATE) AS day, "
                "SUM(Inventory.order_total) AS revenue "
                "FROM Inventory "
                "WHERE CAST(Inventory.order_date AS DATE) BETWEEN ? AND ? "
                "GROUP BY day "
                "ORDER BY day"
            )
            rows = _run_guarded(sql, (dr.from_, dr.to))
            series = [(str(r[0]), float(r[1]) if r[1] is not None else 0.0) for r in rows]
            
            total = sum(v for _, v in series)
            avg_daily = total / max(len(series), 1)
            
            summary = f"Revenue trend from {dr.from_.isoformat()} to {dr.to.isoformat()}: ${total:,.2f} total, ${avg_daily:,.2f} daily average."
            
            return ReportResponse(
                summary_text=summary,
                tables_used=["Inventory"],
                sql=[sql],
                charts=[Chart(type="line", series=[ChartSeries(name="Daily Revenue", data=series)])],
            )

        return {"error": "Unknown report type", "suggestion": "Use 'revenue_by_month', 'top_customers', 'top_products', or 'revenue_trend'"}
    except Exception as e:
        return {"error": str(e), "suggestion": "Adjust filters or try again."}
