"""
Schema alias map for defensive column normalization.
This is a minimal placeholder for Day 1; extend as needed.
"""

ALIAS_MAP = {
    "customer": {
        "cid": ["CID", "customer_id"],
        "name": ["name", "customer_name"],
        "email": ["email"],
    },
    "inventory": {
        "iid": ["IID", "order_id"],
        "cid": ["CID", "customer_id"],
        "order_date": ["order_date", "date"],
        "order_total": ["order_total", "total"],
    },
    "detail": {
        "did": ["DID"],
        "iid": ["IID", "order_id"],
        "product_id": ["product_id", "sku"],
        "qty": ["qty", "quantity"],
        "unit_price": ["unit_price", "price"],
        "price_table_item_id": ["price_table_item_id"],
    },
    "pricelist": {
        "price_table_item_id": ["price_table_item_id"],
        "product_id": ["product_id"],
        "unit_price": ["unit_price"],
    },
}

