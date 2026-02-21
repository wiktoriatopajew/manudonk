"""
Update product categories to simplified 6-category system
"""
from database.models import Product, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database connection - use SQLite for local
DATABASE_URL = "sqlite:///./database/products.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
session = Session()

# Category mapping
CATEGORY_MAP = {
    'Automobiles': 'cars',
    'Construction Equipment': 'construction',
    'Engines': 'engines',
    'Motorcycles': 'motorcycles',
    'Other Manuals': 'other',
    'Tractors & Agriculture': 'other',  # Move to other
    'Trucks & Commercial Vehicles': 'trucks',
    'ATVs & Off-Road': 'other',
    'Marine & Boats': 'other',
    'Home Appliances': 'other',
    'Electronics': 'other',
    'Tools & Equipment': 'other'
}

def update_categories():
    """Update all products to use new category names"""
    print("🔄 Starting category update...\n")
    
    # Get current categories
    old_categories = session.query(Product.category).distinct().all()
    
    print("Old categories found:")
    for cat in old_categories:
        count = session.query(Product).filter(Product.category == cat[0]).count()
        new_name = CATEGORY_MAP.get(cat[0], 'other')
        print(f"  {cat[0]:40} → {new_name:15} ({count} products)")
    
    print("\n" + "="*60)
    
    # Update each category
    total_updated = 0
    for old_cat, new_cat in CATEGORY_MAP.items():
        count = session.query(Product).filter(Product.category == old_cat).update(
            {Product.category: new_cat}, synchronize_session=False
        )
        if count > 0:
            print(f"✅ Updated {count} products: {old_cat} → {new_cat}")
            total_updated += count
    
    session.commit()
    
    print("\n" + "="*60)
    print(f"\n✅ Total products updated: {total_updated}")
    
    # Show new distribution
    print("\nNew category distribution:")
    new_categories = session.query(Product.category).distinct().all()
    for cat in new_categories:
        count = session.query(Product).filter(Product.category == cat[0]).count()
        print(f"  {cat[0]:15} {count:5} products")
    
    print(f"\nTotal products: {session.query(Product).count()}")
    print("\n✅ Category update completed!")

if __name__ == "__main__":
    update_categories()
