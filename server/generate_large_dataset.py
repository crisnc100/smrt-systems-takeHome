#!/usr/bin/env python3
"""
Generate large CSV datasets for scalability testing
"""
import csv
import random
from datetime import date, timedelta
import os

def generate_large_dataset(base_dir="data", scale_factor=1000):
    """
    Generate large CSV files for testing.
    scale_factor=1000 creates ~100k inventory records
    """
    
    print(f"Generating large dataset with scale factor {scale_factor}...")
    
    # Ensure directory exists
    os.makedirs(base_dir, exist_ok=True)
    
    # Generate Customers (scale_factor * 3)
    num_customers = scale_factor * 3
    print(f"Generating {num_customers} customers...")
    
    with open(os.path.join(base_dir, "Customer_large.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["CID", "name", "email"])
        
        for i in range(1, num_customers + 1):
            name = f"Customer_{i}"
            email = f"customer{i}@example.com"
            writer.writerow([i, name, email])
    
    # Generate Products for Pricelist (100 products)
    num_products = 100
    print(f"Generating {num_products} products...")
    
    with open(os.path.join(base_dir, "Pricelist_large.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["price_table_item_id", "product_id", "unit_price"])
        
        for i in range(1, num_products + 1):
            product_id = f"SKU-{i:04d}"
            price = round(random.uniform(10, 500), 2)
            writer.writerow([9000 + i, product_id, price])
    
    # Generate Inventory (scale_factor * 100 orders)
    num_orders = scale_factor * 100
    print(f"Generating {num_orders} orders...")
    
    start_date = date(2023, 1, 1)
    end_date = date(2024, 12, 31)
    
    with open(os.path.join(base_dir, "Inventory_large.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["IID", "CID", "order_date", "order_total"])
        
        for i in range(1, num_orders + 1):
            cid = random.randint(1, num_customers)
            # Random date in range
            days_between = (end_date - start_date).days
            random_days = random.randint(0, days_between)
            order_date = start_date + timedelta(days=random_days)
            
            # Order total will be calculated from details
            order_total = round(random.uniform(50, 2000), 2)
            writer.writerow([i, cid, order_date.isoformat(), order_total])
    
    # Generate Detail (average 3 items per order)
    num_details = num_orders * 3
    print(f"Generating {num_details} order details...")
    
    with open(os.path.join(base_dir, "Detail_large.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["DID", "IID", "product_id", "qty", "unit_price", "price_table_item_id"])
        
        detail_id = 1
        for order_id in range(1, num_orders + 1):
            # Random 1-5 items per order
            num_items = random.randint(1, 5)
            
            for _ in range(num_items):
                product_idx = random.randint(1, num_products)
                product_id = f"SKU-{product_idx:04d}"
                qty = random.randint(1, 10)
                unit_price = round(random.uniform(10, 500), 2)
                price_table_item_id = 9000 + product_idx
                
                writer.writerow([detail_id, order_id, product_id, qty, unit_price, price_table_item_id])
                detail_id += 1
    
    print(f"Large dataset generated in {base_dir}/")
    print(f"Files created: Customer_large.csv, Inventory_large.csv, Detail_large.csv, Pricelist_large.csv")
    print(f"Stats:")
    print(f"  - Customers: {num_customers:,}")
    print(f"  - Orders: {num_orders:,}")
    print(f"  - Order Details: ~{num_details:,}")
    print(f"  - Products: {num_products}")

if __name__ == "__main__":
    import sys
    
    scale = 1000  # Default: generate 100k orders
    if len(sys.argv) > 1:
        scale = int(sys.argv[1])
    
    generate_large_dataset(scale_factor=scale)