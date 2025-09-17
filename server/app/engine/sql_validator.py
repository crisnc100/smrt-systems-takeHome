"""Validation helpers for LLM generated SQL."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from ..validators import guards
from .schema_context import TABLE_NAME_MAP, COLUMN_NAME_SET

ALLOWED_SPECIAL_IDENTIFIERS = {
    "current_date",
    "current_timestamp",
    "today",
}

FORBIDDEN_KEYWORDS = {
    "--",
    "/*",
    "*/",
    "ATTACH",
    "DETACH",
    "PRAGMA",
    "COPY",
    "INSERT",
    "UPDATE",
    "DELETE",
    "ALTER",
    "DROP",
    "CREATE",
    "REPLACE",
}

TABLE_PATTERN = re.compile(r"\b(from|join)\s+([A-Za-z_\"`][\w\"`\.]*)", re.IGNORECASE)


@dataclass
class ValidatedSQL:
    sql: str
    tables: List[str]


def _strip_identifier(value: str) -> str:
    value = value.strip()
    if value.startswith("("):
        # Subquery, skip
        return ""
    if value.startswith(('"', "`")) and value.endswith(('"', "`")):
        value = value[1:-1]
    # Remove alias (split on whitespace)
    value = value.split()[0]
    # Remove schema prefix if present (not expected but safe)
    if "." in value:
        value = value.split(".")[-1]
    return value


def _normalize_functions(candidate: str) -> str:
    """Apply small rewrites so common vendor SQL works in DuckDB."""
    def _rewrite_dateadd(match: re.Match) -> str:
        unit = match.group(1).strip().strip("'\"").upper() or "DAY"
        amount_raw = match.group(2).strip().strip("'\"")
        expr = match.group(3).strip()
        if not re.fullmatch(r"-?\d+", amount_raw):
            return match.group(0)
        return f"DATE_ADD({expr}, INTERVAL '{amount_raw}' {unit})"

    candidate = re.sub(
        r"DATEADD\(\s*([^,]+?)\s*,\s*([^,]+?)\s*,\s*([^)]+?)\)",
        _rewrite_dateadd,
        candidate,
        flags=re.IGNORECASE,
    )
    candidate = re.sub(r"\bDATEADD\s*\(", "DATE_ADD(", candidate, flags=re.IGNORECASE)
    # DuckDB expects quoted units in DATEADD; some models emit DATEADD(day, ...)
    candidate = re.sub(r"DATE_ADD\(\s*day\s*,", "DATE_ADD('day',", candidate, flags=re.IGNORECASE)
    candidate = re.sub(r"DATE_ADD\(\s*month\s*,", "DATE_ADD('month',", candidate, flags=re.IGNORECASE)
    candidate = re.sub(r"DATE_ADD\(\s*year\s*,", "DATE_ADD('year',", candidate, flags=re.IGNORECASE)
    return candidate


def validate(sql: str, *, default_limit: int = 200) -> ValidatedSQL:
    """Validate and sanitize LLM generated SQL before execution."""
    if not sql or not sql.strip():
        raise ValueError("SQL is empty")

    candidate = sql.strip()
    if candidate.endswith(";"):
        candidate = candidate[:-1].strip()

    candidate = _normalize_functions(candidate)

    for keyword in FORBIDDEN_KEYWORDS:
        if keyword.lower() in candidate.lower():
            raise ValueError(f"Forbidden keyword detected: {keyword}")

    ok, reason = guards.assert_select_only(candidate)
    if not ok:
        raise ValueError(reason)

    # Collect table names from simple FROM/JOIN patterns
    discovered = []
    for match in TABLE_PATTERN.finditer(candidate):
        identifier = _strip_identifier(match.group(2))
        if not identifier:
            continue
        key = identifier.lower()
        if key not in TABLE_NAME_MAP:
            if key in COLUMN_NAME_SET or key in ALLOWED_SPECIAL_IDENTIFIERS:
                # False positive from constructs like EXTRACT(... FROM column)
                continue
            raise ValueError(f"Unsupported table referenced: {identifier}")
        discovered.append(TABLE_NAME_MAP[key])

    if not discovered:
        # Even if not found, ensure query references at least one allowed table using heuristic
        raise ValueError("No known tables referenced in SQL")

    safe_sql = guards.enforce_limit(candidate, max_limit=default_limit)

    return ValidatedSQL(sql=safe_sql, tables=sorted(set(discovered)))
