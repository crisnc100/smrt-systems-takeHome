"""Shared schema context for AI Smart Mode.

These constants are used when guiding the LLM to generate compliant DuckDB SQL
queries. Keeping them centralized makes it easier to adjust column mappings or
relationships without touching the query engine logic.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class TableSchema:
    name: str
    description: str
    columns: Dict[str, str]

    def render(self) -> str:
        lines = [f"- {self.name}: {self.description}"]
        for col, detail in self.columns.items():
            lines.append(f"    - {col}: {detail}")
        return "\n".join(lines)


TABLE_SCHEMAS: List[TableSchema] = [
    TableSchema(
        name="Customer",
        description="customer master data. CID links to Inventory.CID",
        columns={
            "CID": "integer primary key",
            "name": "full name string",
            "email": "customer email address",
            "phone": "phone number",
            "address": "street address",
            "city": "city",
            "state": "state",
            "zip": "postal code",
        },
    ),
    TableSchema(
        name="Inventory",
        description="high level orders. Links to Customer via CID",
        columns={
            "IID": "integer primary key (order id)",
            "CID": "customer id",
            "order_date": "date the order was placed",
            "order_total": "numeric total",
            "CATEGORY": "category label",
            "PIECES": "number of pieces",
            "READYDATE": "date order ready",
            "OUTDATE": "pickup date",
            "PIF": "boolean paid in full flag",
            "payment_type": "payment method text",
        },
    ),
    TableSchema(
        name="Detail",
        description="line items for orders. Links to Inventory via IID and Pricelist via price_table_item_id",
        columns={
            "DID": "integer primary key",
            "IID": "order id",
            "price_table_item_id": "foreign key to Pricelist",
            "product_id": "item label",
            "qty": "quantity ordered",
            "unit_price": "unit price",
            "line_total": "line total (qty * unit_price)",
        },
    ),
    TableSchema(
        name="Pricelist",
        description="catalog information for items",
        columns={
            "price_table_item_id": "primary key",
            "product_id": "item display name",
            "unit_price": "base or current price",
        },
    ),
]

TABLE_NAMES = [schema.name for schema in TABLE_SCHEMAS]
TABLE_NAME_MAP = {name.lower(): name for name in TABLE_NAMES}
COLUMN_NAME_SET = {
    col.lower()
    for schema in TABLE_SCHEMAS
    for col in schema.columns.keys()
}


RELATIONSHIP_NOTES = (
    "Relationships: Inventory.CID -> Customer.CID, Detail.IID -> Inventory.IID, "
    "Detail.price_table_item_id -> Pricelist.price_table_item_id. Use LEFT JOINs "
    "when unsure to avoid unintentionally dropping rows."
)


def build_schema_markdown() -> str:
    rendered = [schema.render() for schema in TABLE_SCHEMAS]
    rendered.append(RELATIONSHIP_NOTES)
    return "\n".join(rendered)


SCHEMA_SUMMARY = build_schema_markdown()


AI_SYSTEM_PROMPT = (
    "You are a careful data analyst that only writes DuckDB compatible SQL. "
    "You must reference only the tables and columns provided. Always return a "
    "JSON object with keys 'sql', 'summary', and 'follow_ups'. The 'sql' field "
    "must be a single SELECT statement. If the question cannot be answered, "
    "set 'sql' to an empty string and explain why in 'summary'."
)


AI_USER_PROMPT_TEMPLATE = (
    "Available tables and columns:\n"
    f"{SCHEMA_SUMMARY}\n\n"
    "Active filters (JSON): {filters}\n"
    "Helpful DuckDB snippets: date_trunc('month', order_date), current_date - INTERVAL '30' DAY, dateadd('day', -7, current_date), strftime(order_date, '%Y-%m').\n"
    "Avoid SQLite-style strftime('now', ...) chains.\n"
    "User question: {question}.\n"
    "Respond with JSON only, no prose."
)
