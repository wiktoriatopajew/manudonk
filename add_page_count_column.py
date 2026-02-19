"""
Quick migration script to add page_count column locally
"""
from database.models import get_engine
from sqlalchemy import text

engine = get_engine()

try:
    with engine.connect() as conn:
        # Check if column exists
        result = conn.execute(text("PRAGMA table_info(products)"))
        columns = [row[1] for row in result]
        
        if 'page_count' in columns:
            print("✅ page_count column already exists")
        else:
            conn.execute(text("ALTER TABLE products ADD COLUMN page_count INTEGER DEFAULT NULL"))
            conn.commit()
            print("✅ Added page_count column to products table")
            
except Exception as e:
    print(f"❌ Error: {e}")
