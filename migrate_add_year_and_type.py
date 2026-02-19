"""
Migration script: Add year and product_type columns to products table
Automatically detects year from title/model and categorizes products
"""
import re
from database.models import get_engine, Base, Product, get_session
from sqlalchemy import text

def extract_year(text_input):
    """
    Extract year from text (title or model)
    Looks for 4-digit years between 1900-2099
    Returns the most recent year found or None
    """
    if not text_input:
        return None
    
    # Find all 4-digit numbers that could be years
    years = re.findall(r'\b(19\d{2}|20\d{2})\b', str(text_input))
    
    if years:
        # Return the most recent year found
        return int(max(years))
    
    return None


def determine_product_type(category):
    """
    Determine product type based on category
    Returns: vehicles, electronics, publications, or other
    """
    if not category:
        return 'other'
    
    category_lower = category.lower()
    
    # Vehicles
    vehicle_keywords = ['automotive', 'car', 'truck', 'motorcycle', 'bike', 'bus', 
                       'airplane', 'aircraft', 'boat', 'marine', 'vehicle', 'atv',
                       'scooter', 'van', 'suv', 'trailer', 'jet ski']
    
    # Electronics
    electronics_keywords = ['electronics', 'phone', 'computer', 'laptop', 'tablet',
                           'camera', 'photography', 'audio', 'tv', 'television',
                           'smartphone', 'watch', 'gaming', 'console', 'printer',
                           'scanner', 'monitor', 'speaker', 'headphones']
    
    # Publications
    publication_keywords = ['manual', 'magazine', 'book', 'publication', 'guide',
                           'journal', 'catalog', 'brochure', 'document']
    
    # Check category against keywords
    for keyword in vehicle_keywords:
        if keyword in category_lower:
            return 'vehicles'
    
    for keyword in electronics_keywords:
        if keyword in category_lower:
            return 'electronics'
    
    for keyword in publication_keywords:
        if keyword in category_lower:
            return 'publications'
    
    return 'other'


def migrate():
    """Add year and product_type columns and populate them"""
    engine = get_engine()
    
    print("=" * 60)
    print("🔄 Starting migration: Add year and product_type columns")
    print("=" * 60)
    
    # Add columns to database
    with engine.connect() as conn:
        # First check and add page_count if missing (needed for model compatibility)
        print("\n📝 Checking 'page_count' column...")
        try:
            conn.execute(text("ALTER TABLE products ADD COLUMN page_count INTEGER"))
            conn.commit()
            print("✅ Column 'page_count' added successfully")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("⚠️  Column 'page_count' already exists, skipping...")
            else:
                print(f"⚠️  Could not add 'page_count': {e}")
        
        print("\n📝 Adding 'year' column...")
        try:
            conn.execute(text("ALTER TABLE products ADD COLUMN year INTEGER"))
            conn.commit()
            print("✅ Column 'year' added successfully")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("⚠️  Column 'year' already exists, skipping...")
            else:
                print(f"❌ Error adding 'year' column: {e}")
                raise
        
        print("\n📝 Adding 'product_type' column...")
        try:
            conn.execute(text("ALTER TABLE products ADD COLUMN product_type VARCHAR(50)"))
            conn.commit()
            print("✅ Column 'product_type' added successfully")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("⚠️  Column 'product_type' already exists, skipping...")
            else:
                print(f"❌ Error adding 'product_type' column: {e}")
                raise
        
        # Add indexes
        print("\n📝 Adding indexes...")
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_products_year ON products(year)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_products_product_type ON products(product_type)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_year_type ON products(year, product_type)"))
            conn.commit()
            print("✅ Indexes added successfully")
        except Exception as e:
            print(f"⚠️  Index creation warning: {e}")
    
    # Now populate the new columns
    print("\n🔍 Analyzing existing products...")
    session = get_session()
    
    try:
        products = session.query(Product).all()
        total = len(products)
        print(f"📊 Found {total} products to process")
        
        updated_count = 0
        years_detected = 0
        
        for i, product in enumerate(products, 1):
            if i % 100 == 0:
                print(f"  Processing: {i}/{total}...")
            
            # Extract year from title and model
            year_from_title = extract_year(product.title)
            year_from_model = extract_year(product.model)
            
            # Prefer year from model, fallback to title
            detected_year = year_from_model or year_from_title
            
            # Determine product type from category
            detected_type = determine_product_type(product.category)
            
            # Update product
            if detected_year:
                product.year = detected_year
                years_detected += 1
            
            product.product_type = detected_type
            updated_count += 1
        
        session.commit()
        
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
        print(f"📊 Products updated: {updated_count}/{total}")
        print(f"📅 Years detected: {years_detected}/{total}")
        
        # Show statistics
        print("\n📈 Product Type Distribution:")
        type_stats = session.query(
            Product.product_type, 
            func.count(Product.id)
        ).group_by(Product.product_type).all()
        
        for ptype, count in type_stats:
            print(f"  - {ptype or 'unknown'}: {count} products")
        
        print("\n📅 Year Range:")
        year_stats = session.query(
            func.min(Product.year),
            func.max(Product.year),
            func.count(Product.year)
        ).first()
        
        if year_stats[0]:
            print(f"  - Oldest: {year_stats[0]}")
            print(f"  - Newest: {year_stats[1]}")
            print(f"  - Products with year: {year_stats[2]}")
        else:
            print("  - No years detected")
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        session.rollback()
        raise
    finally:
        session.close()
    
    print("\n✨ Migration complete! New columns ready to use.")


if __name__ == "__main__":
    from sqlalchemy import func
    migrate()
