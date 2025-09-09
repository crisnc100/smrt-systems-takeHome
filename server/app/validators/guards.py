import re
from typing import Dict, List, Tuple


# Basic SQL keyword sets
SQL_FORBIDDEN = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "REPLACE",
    "TRUNCATE",
    "ATTACH",
    "DETACH",
    "COPY",
    "PRAGMA",
    "CALL",
    "SET",
    ";",
}

SQL_KEYWORDS = {
    "SELECT",
    "FROM",
    "WHERE",
    "GROUP",
    "BY",
    "ORDER",
    "LIMIT",
    "AS",
    "AND",
    "OR",
    "ON",
    "JOIN",
    "LEFT",
    "RIGHT",
    "INNER",
    "OUTER",
    "BETWEEN",
    "CAST",
    "DATE",
    "SUM",
    "COUNT",
    "DESC",
    "ASC",
}


ALLOWED: Dict[str, List[str]] = {
    # Case-insensitive allowlist for table->columns
    "customer": ["cid", "name", "email"],
    "inventory": ["iid", "cid", "order_date", "order_total"],
    "detail": ["did", "iid", "product_id", "qty", "unit_price", "price_table_item_id"],
    "pricelist": ["price_table_item_id", "product_id", "unit_price"],
}


def _normalize_identifier(token: str) -> str:
    return token.strip().strip('`"').lower()


def assert_select_only(sql: str) -> Tuple[bool, str]:
    text = sql.strip().upper()
    if not text.startswith("SELECT") and not text.startswith("WITH"):
        return False, "Only SELECT statements are allowed"
    for forb in SQL_FORBIDDEN:
        if forb in text:
            return False, f"Statement contains forbidden keyword: {forb}"
    if sql.count(";") > 0:
        return False, "Multiple statements are not allowed"
    return True, "ok"


def enforce_limit(sql: str, max_limit: int = 1000) -> str:
    # If LIMIT exists, ensure it's <= max_limit; otherwise append LIMIT
    pattern = re.compile(r"\bLIMIT\s+(\d+)", re.IGNORECASE)
    m = pattern.search(sql)
    if m:
        try:
            val = int(m.group(1))
            if val > max_limit:
                return pattern.sub(f"LIMIT {max_limit}", sql)
            return sql
        except Exception:
            return sql
    else:
        # Append LIMIT at end
        return sql.rstrip() + f" LIMIT {max_limit}"


def validate_whitelist(sql: str) -> Tuple[bool, List[str]]:
    # Extract patterns like Table.Column and bare identifiers and ensure within allowlist
    tokens = re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)", sql)
    violations: List[str] = []
    for tbl, col in tokens:
        t = _normalize_identifier(tbl)
        c = _normalize_identifier(col)
        if t not in ALLOWED or c not in ALLOWED.get(t, []):
            violations.append(f"{tbl}.{col}")
    # Bare columns without table qualifier are allowed in our templates; skip strict checks here
    return (len(violations) == 0), violations

