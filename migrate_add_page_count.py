"""
Migration script to add page_count column to products table
Run this once to update existing database
"""
from database.models import get_engine
from sqlalchemy import text

def migrate():
    """Add page_count column to products table"""
    engine = get_engine()
    
    with engine.connect() as conn:
        try:
            # Add page_count column
            conn.execute(text("""
                ALTER TABLE products 
                ADD COLUMN IF NOT EXISTS page_count INTEGER DEFAULT NULL
            """))
            conn.commit()
            print("✅ Migration complete! page_count column added to products table.")
        except Exception as e:
            print(f"⚠️  Migration error (may already exist): {e}")

if __name__ == "__main__":
    migrate()
