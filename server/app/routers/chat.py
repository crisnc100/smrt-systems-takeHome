from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple, Literal
import logging

from fastapi import APIRouter
from pydantic import BaseModel
from time import perf_counter

from ..engine import duck, llm_query, sql_validator
from ..engine.llm_query import LLMQueryError
from ..validators import guards
from ..validators.quality import calculate_confidence, get_follow_up_suggestions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter(prefix="/chat", tags=["chat"])


class DateRange(BaseModel):
    from_: Optional[date] = None
    to: Optional[date] = None

    class Config:
        fields = {"from_": "from"}


class ChatRequest(BaseModel):
    message: str
    filters: Optional[Dict[str, Any]] = None
    ai_assist: bool = False
    query_mode: Literal["classic", "ai"] = "classic"


class EvidenceSnippet(BaseModel):
    date: Optional[str] = None
    revenue: Optional[float] = None


class ChatResponse(BaseModel):
    answer_text: str
    tables_used: List[str]
    sql: str
    rows_scanned: int
    exec_ms: float
    data_snippets: List[EvidenceSnippet]
    validations: List[Dict[str, Any]]
    confidence: float
    follow_ups: List[str]
    chart_suggestion: Dict[str, Any]
    quality_badges: Optional[List[Dict[str, str]]] = []
    chart: Optional[Dict[str, Any]] = None
    query_mode: Literal["classic", "ai"] = "classic"


def _get_inventory_max_date() -> Optional[date]:
    try:
        duck.ensure_views()  # Ensure tables are loaded
        rows = duck.query_with_timeout(
            "SELECT MAX(CAST(order_date AS DATE)) FROM Inventory",
            (),
            timeout_s=1.0,
        )
        if rows and rows[0][0] is not None:
            # rows[0][0] is already a date object in DuckDB Python API
            return rows[0][0]
    except Exception as e:
        logger.warning(f"Failed to get max date from Inventory: {e}")
    return None


def _get_sample_ids() -> Tuple[Optional[str], Optional[str]]:
    """Get sample IID and CID from actual data for suggestions."""
    try:
        duck.ensure_views()
        # Get first order ID
        iid_rows = duck.query_with_timeout("SELECT IID FROM Inventory LIMIT 1", (), timeout_s=0.5)
        iid = str(iid_rows[0][0]) if iid_rows else None
        
        # Get first customer ID
        cid_rows = duck.query_with_timeout("SELECT CID FROM Customer LIMIT 1", (), timeout_s=0.5)
        cid = str(cid_rows[0][0]) if cid_rows else None
        
        return iid, cid
    except Exception:
        return None, None


def _parse_date_range(msg: str, filt: Optional[Dict[str, Any]]) -> DateRange:
    # Priority to explicit filters
    if filt and isinstance(filt.get("date_range"), dict):
        dr = filt["date_range"]
        f = dr.get("from") or dr.get("from_")
        t = dr.get("to")
        return DateRange(from_=date.fromisoformat(f) if f else None, to=date.fromisoformat(t) if t else None)

    import re
    text = msg.lower()
    today = date.today()
    # Get the actual max date from data
    actual_max = _get_inventory_max_date()
    if actual_max is None:
        # If we can't get the max date, use August 2024 as a reasonable default
        # based on the sample data we've seen
        data_max = date(2024, 8, 31)
        logger.info(f"Using fallback date {data_max} since max date query failed")
    else:
        data_max = actual_max
        logger.info(f"Using actual max date from data: {data_max}")

    def start_of_month(d: date) -> date:
        return d.replace(day=1)

    def end_of_month(d: date) -> date:
        # move to next month start then minus one day
        if d.month == 12:
            next_start = date(d.year + 1, 1, 1)
        else:
            next_start = date(d.year, d.month + 1, 1)
        return next_start - timedelta(days=1)

    def month_from_name(name: str) -> int:
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
            'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        return months.get(name, 0)

    def quarter_bounds(y: int, q: int) -> Tuple[date, date]:
        m_start = (q - 1) * 3 + 1
        start = date(y, m_start, 1)
        end = end_of_month(date(y, m_start + 2, 1))
        return start, end

    # last N days/weeks/months
    m = re.search(r"last\s+(\d+)\s+days?", text)
    if m:
        n = int(m.group(1))
        return DateRange(from_=data_max - timedelta(days=n), to=data_max)
    m = re.search(r"last\s+(\d+)\s+weeks?", text)
    if m:
        n = int(m.group(1))
        return DateRange(from_=data_max - timedelta(days=7*n), to=data_max)
    m = re.search(r"last\s+(\d+)\s+months?", text)
    if m:
        # approximate months as 30 days windows
        n = int(m.group(1))
        return DateRange(from_=data_max - timedelta(days=30*n), to=data_max)

    # simple phrases
    if "last 30 days" in text:
        return DateRange(from_=data_max - timedelta(days=30), to=data_max)
    if "this month" in text:
        return DateRange(from_=start_of_month(data_max), to=data_max)
    if "last month" in text:
        first_this = start_of_month(data_max)
        last_month_end = first_this - timedelta(days=1)
        return DateRange(from_=start_of_month(last_month_end), to=last_month_end)
    if "this year" in text:
        return DateRange(from_=date(data_max.year, 1, 1), to=data_max)
    if "last year" in text:
        return DateRange(from_=date(data_max.year - 1, 1, 1), to=date(data_max.year - 1, 12, 31))
    if "this week" in text:
        # ISO week: Monday=0
        start = data_max - timedelta(days=data_max.weekday())
        return DateRange(from_=start, to=data_max)
    if "last week" in text:
        # previous week Monday..Sunday
        start = data_max - timedelta(days=data_max.weekday() + 7)
        end = start + timedelta(days=6)
        return DateRange(from_=start, to=end)
    if "this quarter" in text:
        q = (data_max.month - 1) // 3 + 1
        start, _ = quarter_bounds(data_max.year, q)
        return DateRange(from_=start, to=data_max)
    if "last quarter" in text:
        q = (data_max.month - 1) // 3 + 1
        if q == 1:
            y = data_max.year - 1
            q = 4
        else:
            y = data_max.year
            q -= 1
        start, end = quarter_bounds(y, q)
        return DateRange(from_=start, to=end)

    # Qn YYYY
    m = re.search(r"\bq([1-4])\s*(\d{4})\b", text)
    if m:
        q = int(m.group(1))
        y = int(m.group(2))
        start, end = quarter_bounds(y, q)
        return DateRange(from_=start, to=end)

    # Named month (Month YYYY)
    m = re.search(r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})\b", text)
    if m:
        mon = month_from_name(m.group(1))
        y = int(m.group(2))
        start = date(y, mon, 1)
        return DateRange(from_=start, to=end_of_month(start))

    # Named month without year: assume data_max year
    m = re.search(r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b", text)
    if m:
        mon = month_from_name(m.group(1))
        start = date(data_max.year, mon, 1)
        return DateRange(from_=start, to=end_of_month(start))

    # last N days default handled above; if nothing recognized, return empty range
    return DateRange(from_=None, to=None)


def _format_currency(v: Optional[float]) -> str:
    if v is None:
        return "$0"
    return f"${v:,.2f}"


def _intent_revenue_by_period(message: str, filters: Optional[Dict[str, Any]]) -> Optional[Tuple[str, Tuple[Any, ...], List[str], str, List[EvidenceSnippet], List[str]]]:
    # Only match if message contains revenue/sales keywords
    import re
    if not re.search(r"(revenue|sales|income|earnings)", message, re.IGNORECASE):
        return None
    
    dr = _parse_date_range(message, filters)
    if not (dr.from_ and dr.to):
        return None
    sql = (
        "SELECT CAST(order_date AS DATE) AS day, SUM(order_total) AS revenue "
        "FROM Inventory "
        "WHERE CAST(order_date AS DATE) BETWEEN ? AND ? "
        "GROUP BY day ORDER BY day"
    )
    followups = ["Top products last 30 days", "Compare vs prior 30 days"]
    return sql, (dr.from_, dr.to), ["Inventory"], "revenue_by_period", [], followups


def _intent_orders_by_customer(message: str) -> Optional[Tuple[str, Tuple[Any, ...], List[str], str, List[EvidenceSnippet], List[str]]]:
    import re

    # More flexible pattern - matches "orders for CID 1001", "orders cid 1001", "orders 1001", etc.
    m = re.search(r"orders?\s*(?:for\s*)?(?:customer|cid)?\s*([0-9]+)", message, re.IGNORECASE)
    logger.info(f"Orders pattern match for '{message}': {m is not None}")
    if not m:
        # Try reversed form: "customer 1001 orders"
        m2 = re.search(r"(?:customer|cid)?\s*([0-9]+)\s+orders?", message, re.IGNORECASE)
        if m2:
            cid = m2.group(1)
        else:
            # Try name-based: "orders for John Smith" or "orders John Smith"
            m3 = re.search(r"orders?\s*(?:for\s*)?(?:customer\s*)?([A-Za-z][A-Za-z\s\.'-]{1,60})$", message, re.IGNORECASE)
            if not m3:
                return None
            name = m3.group(1).strip()
            try:
                rows = duck.query_with_timeout(
                    "SELECT CID, name FROM Customer WHERE LOWER(name) LIKE ? OR LOWER(email) LIKE ? ORDER BY CID LIMIT 3",
                    (f"%{name.lower()}%", f"%{name.lower()}%"),
                    timeout_s=1.0,
                )
                if not rows:
                    return None
                cid = str(rows[0][0])
            except Exception:
                return None
    else:
        cid = m.group(1)
    sql = (
        "SELECT Inventory.IID, CAST(Inventory.order_date AS DATE) AS order_date, Inventory.order_total "
        "FROM Inventory WHERE Inventory.CID = ? ORDER BY Inventory.order_date DESC"
    )
    followups = [f"Order details for IID …", "Revenue last 30 days"]
    return sql, (cid,), ["Inventory"], "orders_by_customer", [], followups


def _intent_top_products(message: str) -> Optional[Tuple[str, Tuple[Any, ...], List[str], str, List[EvidenceSnippet], List[str]]]:
    import re
    
    # More flexible pattern - matches "top products", "best selling", etc.
    m = re.search(r"(top|best|popular)\s*(\d+)?\s*(?:best[-\s]*)?(selling|sellers|products?|items?)", message, re.IGNORECASE)
    logger.info(f"Top products pattern match for '{message}': {m is not None}")
    if not m:
        return None
    k = int(m.group(2)) if m.group(2) else 10 if "best" in message.lower() else 5
    # Default to revenue ordering
    order_expr = "SUM(Detail.qty * Detail.unit_price)"
    k = max(1, min(k, 1000))
    sql = (
        "SELECT Detail.product_id, SUM(Detail.qty) AS total_qty, SUM(Detail.qty * Detail.unit_price) AS total_revenue "
        "FROM Detail GROUP BY Detail.product_id ORDER BY " + order_expr + f" DESC LIMIT {k}"
    )
    followups = ["Top customers", "Revenue last 30 days"]
    return sql, tuple(), ["Detail"], "top_products", [], followups


def _intent_top_customers(message: str) -> Optional[Tuple[str, Tuple[Any, ...], List[str], str, List[EvidenceSnippet], List[str]]]:
    import re
    m = re.search(r"(top|best|largest)\s*(\d+)?\s*(customers?)", message, re.IGNORECASE)
    if not m:
        return None
    k = int(m.group(2)) if m.group(2) else 5
    k = max(1, min(k, 1000))
    sql = (
        "SELECT COALESCE(Customer.name, CAST(Inventory.CID AS VARCHAR)) AS customer, "
        "SUM(Inventory.order_total) AS revenue "
        "FROM Inventory LEFT JOIN Customer ON Customer.CID = Inventory.CID "
        "GROUP BY COALESCE(Customer.name, CAST(Inventory.CID AS VARCHAR)) "
        "ORDER BY revenue DESC LIMIT " + str(k)
    )
    return sql, tuple(), ["Inventory", "Customer"], "top_customers", [], ["Revenue last 30 days"]


def _intent_order_details(message: str) -> Optional[Tuple[str, Tuple[Any, ...], List[str], str, List[EvidenceSnippet], List[str]]]:
    import re

    # More flexible pattern - matches "order details IID 2001", "order details 2001", "details for 2001", etc.
    m = re.search(r"(?:order\s*)?(?:details?|lines?)\s*(?:for\s*)?(?:iid|order)?\s*([0-9]+)", message, re.IGNORECASE)
    logger.info(f"Order details pattern match for '{message}': {m is not None}")
    if not m:
        return None
    iid = m.group(1)
    sql = (
        "SELECT Detail.DID, Detail.product_id, Detail.qty, Detail.unit_price, (Detail.qty * Detail.unit_price) AS line_total "
        "FROM Detail WHERE Detail.IID = ? ORDER BY Detail.DID"
    )
    followups = ["Top products last 30 days", "Orders for CID …"]
    return sql, (iid,), ["Detail"], "order_details", [], followups


def _detect_intent(message: str, filters: Optional[Dict[str, Any]]):
    message_l = message.lower()
    logger.info(f"Detecting intent for: '{message_l}'")
    
    # Check more specific patterns first, revenue last since it has date parsing fallback
    planners = [
        ("order_details", lambda: _intent_order_details(message)),
        ("orders_by_customer", lambda: _intent_orders_by_customer(message)),
        ("top_customers", lambda: _intent_top_customers(message)),
        ("top_products", lambda: _intent_top_products(message)),
        ("revenue_by_period", lambda: _intent_revenue_by_period(message, filters)),
    ]
    
    for name, plan in planners:
        spec = plan()
        if spec:
            logger.info(f"Intent matched: {name}")
            return spec
    
    logger.warning(f"No intent matched for: '{message}'")
    return None


def _run_with_guards(sql: str, params: Tuple[Any, ...], limit_default: int = 1000) -> Tuple[List[tuple], List[Dict[str, Any]], str, float]:
    # Enforce SELECT-only
    ok, reason = guards.assert_select_only(sql)
    if not ok:
        raise ValueError(f"Guard failed: {reason}")
    # Enforce whitelist
    w_ok, violations = guards.validate_whitelist(sql)
    if not w_ok:
        raise ValueError(f"Unknown columns referenced: {', '.join(violations)}")
    # Enforce LIMIT
    safe_sql = guards.enforce_limit(sql, limit_default)

    # Execute with timeout and caching
    start = perf_counter()
    try:
        rows = duck.cached_query(safe_sql, params)
    except Exception:
        # Fallback to direct with timeout if not in cache
        rows = duck.query_with_timeout(safe_sql, params, timeout_s=2.0)
    exec_ms = (perf_counter() - start) * 1000.0

    validations: List[Dict[str, Any]] = []
    if len(rows) == 0:
        validations.append({"name": "non_empty_result", "status": "fail"})
    else:
        validations.append({"name": "non_empty_result", "status": "pass"})
    return rows, validations, safe_sql, exec_ms


def _error(message: str, suggestion: str = "Try a supported question or adjust filters.", mode: Literal["classic", "ai"] = "classic"):
    return {"error": message, "suggestion": suggestion, "query_mode": mode}


@router.post("")
def chat(req: ChatRequest):
    try:
        mode: Literal["classic", "ai"] = "ai" if req.ai_assist else req.query_mode
        logger.info(f"Chat request: mode={mode}, message='{req.message}', filters={req.filters}")
        duck.ensure_views()
        if mode == "ai":
            try:
                generation = llm_query.run(req.message, req.filters or {})
            except LLMQueryError as exc:
                logger.warning(f"AI generation failed: {exc}")
                return _error(str(exc), "Switch to Classic Mode or try again shortly.", mode)
            except Exception as exc:  # pylint: disable=broad-except
                logger.exception(f"Unexpected AI error: {exc}")
                return _error("AI Smart Mode is temporarily unavailable.", "Switch to Classic Mode or try again shortly.", mode)

            if not generation.sql:
                summary = generation.summary or "AI Smart Mode could not generate a safe query."
                suggestion = (generation.follow_ups or ["Try rephrasing your request", "Switch to Classic Mode"])[0]
                return _error(summary, suggestion, mode)

            try:
                validated = sql_validator.validate(generation.sql)
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning(f"AI SQL rejected: {exc}")
                return _error(f"Generated SQL was rejected: {exc}", "Try rephrasing your request or switch to Classic Mode.", mode)

            exec_start = perf_counter()
            try:
                rows = duck.query_with_timeout(validated.sql, (), timeout_s=3.0)
            except Exception as exc:  # pylint: disable=broad-except
                logger.exception(f"AI SQL execution failed: {exc}")
                return _error("Generated SQL failed to run.", "Try rephrasing or adjust the request.", mode)
            exec_ms = (perf_counter() - exec_start) * 1000.0

            validations: List[Dict[str, Any]] = [
                {"name": "sql_generated", "status": "pass"},
                {
                    "name": "non_empty_result",
                    "status": "pass" if rows else "fail",
                    "message": "" if rows else "AI Smart Mode did not find matching rows",
                },
            ]

            confidence, badges = calculate_confidence(validations, len(rows), validated.tables)
            followups = generation.follow_ups or get_follow_up_suggestions(validated.tables) or []
            if not followups:
                followups = ["Try a more specific question", "Switch back to Classic Mode"]
            else:
                followups = list(dict.fromkeys(followups))

            if generation.summary:
                answer = generation.summary.replace("{count}", str(len(rows)))
            else:
                answer = f"AI Smart Mode returned {len(rows)} rows." if rows else "AI Smart Mode could not find matching rows."

            return ChatResponse(
                answer_text=answer,
                tables_used=validated.tables,
                sql=validated.sql,
                rows_scanned=len(rows),
                exec_ms=exec_ms,
                data_snippets=[],
                validations=validations,
                confidence=confidence,
                follow_ups=followups[:4],
                chart_suggestion={"type": "table"},
                quality_badges=badges,
                chart=None,
                query_mode=mode,
            )
        spec = _detect_intent(req.message, req.filters)
        if not spec:
            logger.warning(f"No intent matched for: {req.message}")
            # Tailored suggestions based on partial signals
            msg_l = req.message.lower()
            
            # Check for customer names
            if any(name in msg_l for name in ["alice", "bob", "carol", "smith", "jones", "white"]):
                suggestion = "I found a customer reference. Try: 'Orders for Alice Smith', 'Revenue from Bob Jones', or 'Customer 1001 orders'."
                return _error(
                    f"Please be more specific about what you want to know about this customer.",
                    suggestion,
                    mode,
                )
            
            # Check for revenue/sales without time period
            if any(k in msg_l for k in ["revenue", "sales", "income", "money"]):
                suggestion = "Choose a time period: 'Revenue last 30 days', 'Revenue this month', 'Revenue August 2024', or 'Revenue this year'."
                return _error(
                    "Revenue queries need a time period.",
                    suggestion,
                    mode,
                )
            
            # Check for products without specifics
            elif any(k in msg_l for k in ["product", "item", "inventory"]):
                suggestion = "Try: 'Top 5 products', 'Product P001 sales', or 'Most sold products'."
                return _error(
                    "Please specify what you want to know about products.",
                    suggestion,
                    mode,
                )
            
            # Check for customer queries
            elif any(k in msg_l for k in ["customer", "client", "buyer"]):
                suggestion = "Try: 'Top customers', 'Customer 1001 orders', or 'Best customers by revenue'."
                return _error(
                    "Please specify what you want to know about customers.",
                    suggestion,
                    mode,
                )
            
            # Check for order queries
            elif "orders" in msg_l and not any(ch.isdigit() for ch in msg_l):
                # Get actual CID from data
                _, sample_cid = _get_sample_ids()
                cid_example = f"orders for CID {sample_cid}" if sample_cid else "orders for CID [customer_id]"
                suggestion = f"Include a customer ID, e.g. '{cid_example}'."
                return _error(
                    "Please specify which customer's orders you want to see.",
                    suggestion,
                    mode,
                )
            elif "detail" in msg_l or "line" in msg_l:
                # Get actual IID from data
                sample_iid, _ = _get_sample_ids()
                iid_example = f"order details {sample_iid}" if sample_iid else "order details [order_id]"
                suggestion = f"Include an order ID, e.g. '{iid_example}'."
                return _error(
                    "Please specify an order ID.",
                    suggestion,
                    mode,
                )
            
            # Generic fallback with dynamic examples
            sample_iid, sample_cid = _get_sample_ids()
            order_example = f"Order details {sample_iid}" if sample_iid else "Order details [order_id]"
            customer_example = f"Orders for CID {sample_cid}" if sample_cid else "Orders for CID [customer_id]"
            suggestion = f"Try: 'Revenue last 30 days', 'Top 5 products', 'Top customers', '{order_example}', or '{customer_example}'."
            return _error(
                "I couldn't understand your question.",
                suggestion,
                mode,
            )

        sql, params, tables, intent_name, snippets_seed, followups = spec
        logger.info(f"Intent: {intent_name}, SQL: {sql}, Params: {params}")
        rows, validations, safe_sql, exec_ms = _run_with_guards(sql, params)
        logger.info(f"Query result: {len(rows)} rows, validations: {validations}")

        if validations and validations[0].get("status") == "fail":
            # Provide a consistent cannot-answer response
            return ChatResponse(
                answer_text=(
                    "Cannot answer: no matching rows. Refine your question or expand the time range."
                ),
                tables_used=tables,
                sql=safe_sql,
                rows_scanned=0,
                data_snippets=[],
                validations=validations,
                confidence=0.2,
                follow_ups=[
                    "Revenue last 30 days",
                    "Top 5 products",
                    "Orders for CID 1001",
                ],
                chart_suggestion={"type": "line"},
                exec_ms=exec_ms,
                query_mode=mode,
            )

        # Compute per-intent response
        if intent_name == "revenue_by_period":
            # Total
            dr = _parse_date_range(req.message, req.filters)
            total_sql = (
                "SELECT SUM(order_total) AS total FROM Inventory WHERE CAST(order_date AS DATE) BETWEEN ? AND ?"
            )
            total_row = duck.query_with_timeout(total_sql, (dr.from_, dr.to), timeout_s=2.0)
            total = float(total_row[0][0]) if total_row and total_row[0][0] is not None else 0.0
            # Rows scanned approximation
            scanned_sql = "SELECT COUNT(*) FROM Inventory WHERE CAST(order_date AS DATE) BETWEEN ? AND ?"
            scanned = int(duck.query_with_timeout(scanned_sql, (dr.from_, dr.to), timeout_s=2.0)[0][0])

            snippets: List[EvidenceSnippet] = []
            for r in rows[:3]:
                day_str = r[0].isoformat() if hasattr(r[0], 'isoformat') else str(r[0])
                snippets.append(EvidenceSnippet(date=day_str, revenue=float(r[1]) if r[1] is not None else 0.0))
            answer = f"Revenue from {dr.from_.isoformat()} to {dr.to.isoformat()}: {_format_currency(total)}."
            confidence, badges = calculate_confidence(validations, len(rows), tables)
            # Minimal, supported follow-ups only
            followups = [
                "Top 5 products",
                "Top customers",
            ]
            # Build chart payload
            chart = {
                "type": "line",
                "series": [
                    {
                        "name": "Revenue",
                        "data": [
                            (
                                (r[0].isoformat() if hasattr(r[0], 'isoformat') else str(r[0])),
                                float(r[1]) if r[1] is not None else 0.0,
                            ) for r in rows
                        ],
                    }
                ],
            }
            return ChatResponse(
                answer_text=answer,
                tables_used=tables,
                sql=safe_sql,
                rows_scanned=scanned,
                exec_ms=exec_ms,
                data_snippets=snippets,
                validations=validations,
                confidence=confidence,
                follow_ups=followups,
                chart_suggestion={"type": "line", "x": "order_date", "y": "revenue"},
                quality_badges=badges,
                chart=chart,
                query_mode=mode,
            )

        if intent_name == "orders_by_customer":
            # Scanned rows (before limit)
            cid = params[0]
            scanned_sql = "SELECT COUNT(*) FROM Inventory I WHERE I.CID = ?"
            scanned = int(duck.query_with_timeout(scanned_sql, (cid,), timeout_s=2.0)[0][0])
            # Fetch customer name if present
            cust_name = None
            try:
                rname = duck.query_with_timeout("SELECT name FROM Customer WHERE CID = ?", (cid,), timeout_s=1.0)
                if rname and rname[0][0]:
                    cust_name = str(rname[0][0])
            except Exception:
                pass
            # Snippets: first 3 orders
            snippets: List[EvidenceSnippet] = []
            for r in rows[:3]:
                snippets.append(EvidenceSnippet(date=str(r[1]), revenue=float(r[2]) if r[2] is not None else 0.0))
            if cust_name:
                answer = f"Found {min(scanned, len(rows))} orders for {cust_name} (CID {cid})."
            else:
                answer = f"Found {min(scanned, len(rows))} orders for CID {cid}."
            confidence, badges = calculate_confidence(validations, len(rows), tables)
            # Dynamic follow-ups: suggest up to 3 order detail links
            followups: List[str] = []
            for r in rows[:3]:
                try:
                    followups.append(f"Order details {str(r[0])}")
                except Exception:
                    pass
            # Do not append unsupported suggestions
            return ChatResponse(
                answer_text=answer,
                tables_used=tables,
                sql=safe_sql,
                rows_scanned=scanned,
                exec_ms=exec_ms,
                data_snippets=snippets,
                validations=validations,
                confidence=confidence,
                follow_ups=followups,
                chart_suggestion={"type": "bar", "x": "order_date", "y": "order_total"},
                quality_badges=badges,
                query_mode=mode,
            )

        if intent_name == "top_products":
            # Scanned rows
            scanned = int(duck.query_with_timeout("SELECT COUNT(*) FROM Detail", (), timeout_s=2.0)[0][0])
            snippets: List[EvidenceSnippet] = []
            for r in rows[:3]:
                # pack "revenue" as total_revenue
                snippets.append(EvidenceSnippet(date=str(r[0]), revenue=float(r[2]) if r[2] is not None else 0.0))
            answer = f"Top {len(rows)} products by performance returned."
            confidence, badges = calculate_confidence(validations, len(rows), tables)
            followups = ["Top customers", "Revenue last 30 days"]
            chart = {
                "type": "bar",
                "series": [
                    {
                        "name": "Revenue",
                        "data": [
                            (str(r[0]), float(r[2]) if r[2] is not None else 0.0) for r in rows
                        ],
                    }
                ],
            }
            return ChatResponse(
                answer_text=answer,
                tables_used=tables,
                sql=safe_sql,
                rows_scanned=scanned,
                exec_ms=exec_ms,
                data_snippets=snippets,
                validations=validations,
                confidence=confidence,
                follow_ups=followups,
                chart_suggestion={"type": "bar", "x": "product_id", "y": "total_revenue"},
                quality_badges=badges,
                chart=chart,
                query_mode=mode,
            )

        if intent_name == "order_details":
            iid = params[0]
            scanned = int(duck.query_with_timeout("SELECT COUNT(*) FROM Detail WHERE Detail.IID = ?", (iid,), timeout_s=2.0)[0][0])
            snippets: List[EvidenceSnippet] = []
            for r in rows[:3]:
                snippets.append(EvidenceSnippet(date=str(r[1]), revenue=float(r[4]) if r[4] is not None else 0.0))
            answer = f"Order {iid} has {len(rows)} lines (limited)."
            confidence, badges = calculate_confidence(validations, len(rows), tables)
            followups = []
            return ChatResponse(
                answer_text=answer,
                tables_used=tables,
                sql=safe_sql,
                rows_scanned=scanned,
                exec_ms=exec_ms,
                data_snippets=snippets,
                validations=validations,
                confidence=confidence,
                follow_ups=followups,
                chart_suggestion={"type": "table"},
                quality_badges=badges,
                query_mode=mode,
            )

        if intent_name == "top_customers":
            scanned = int(duck.query_with_timeout("SELECT COUNT(*) FROM Inventory", (), timeout_s=2.0)[0][0])
            snippets: List[EvidenceSnippet] = []
            for r in rows[:3]:
                snippets.append(EvidenceSnippet(date=str(r[0]), revenue=float(r[1]) if r[1] is not None else 0.0))
            answer = f"Top {len(rows)} customers by revenue returned."
            confidence, badges = calculate_confidence(validations, len(rows), tables)
            chart = {
                "type": "bar",
                "series": [
                    {"name": "Revenue", "data": [(str(r[0]), float(r[1]) if r[1] is not None else 0.0) for r in rows]},
                ],
            }
            return ChatResponse(
                answer_text=answer,
                tables_used=tables,
                sql=safe_sql,
                rows_scanned=scanned,
                exec_ms=exec_ms,
                data_snippets=snippets,
                validations=validations,
                confidence=confidence,
                follow_ups=["Revenue last 30 days"],
                chart_suggestion={"type": "bar", "x": "customer", "y": "revenue"},
                quality_badges=badges,
                chart=chart,
                query_mode=mode,
            )

        return _error("Unhandled intent.", mode=mode)
    except TimeoutError as te:
        return _error(str(te), "Narrow the date range or reduce result size.", mode)
    except Exception as e:
        return _error(str(e), "Try a supported query or adjust parameters.", mode)
