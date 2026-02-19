"""
Add index on category column for faster related products queries
"""
from database.models import get_session
from sqlalchemy import text

def add_category_index():
    """Add index on category if it doesn't exist"""
    session = get_session()
    try:
        # Check if index exists
        result = session.execute(text("""
            SELECT COUNT(*) 
            FROM pg_indexes 
            WHERE indexname = 'idx_products_category';
        """))
        
        exists = result.scalar() > 0
        
        if exists:
            print("✅ Index idx_products_category already exists")
        else:
            print("📊 Creating index on products.category...")
            session.execute(text("""
                CREATE INDEX CONCURRENTLY idx_products_category 
                ON products(category);
            """))
            session.commit()
            print("✅ Index idx_products_category created successfully")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    add_category_index()
