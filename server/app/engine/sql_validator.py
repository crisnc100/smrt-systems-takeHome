"""Validation helpers for LLM generated SQL."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from ..validators import guards
from .schema_context import TABLE_NAME_MAP

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


def validate(sql: str, *, default_limit: int = 200) -> ValidatedSQL:
    """Validate and sanitize LLM generated SQL before execution."""
    if not sql or not sql.strip():
        raise ValueError("SQL is empty")

    candidate = sql.strip()
    if candidate.endswith(";"):
        candidate = candidate[:-1].strip()

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
            raise ValueError(f"Unsupported table referenced: {identifier}")
        discovered.append(TABLE_NAME_MAP[key])

    if not discovered:
        # Even if not found, ensure query references at least one allowed table using heuristic
        raise ValueError("No known tables referenced in SQL")

    safe_sql = guards.enforce_limit(candidate, max_limit=default_limit)

    return ValidatedSQL(sql=safe_sql, tables=sorted(set(discovered)))
