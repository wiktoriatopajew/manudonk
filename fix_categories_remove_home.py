"""
Fix Categories - Remove "Home/" prefix
Removes "Home/" from all categories in database
Example: "Home/Cars/Porsche" → "Cars/Porsche"
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Product

# Database configuration
DATABASE_URL = "postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway"

def main():
    print("\n" + "="*70)
    print("  FIX CATEGORIES - REMOVE 'Home/' PREFIX")
    print("="*70 + "\n")
    
    # Initialize database
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Get all products
    products = session.query(Product).all()
    total = len(products)
    print(f"[√] Found {total} products in database\n")
    
    updated_count = 0
    processed_count = 0
    
    for product in products:
        processed_count += 1
        
        # Show progress every 100 products
        if processed_count % 100 == 0:
            print(f"\n[PROGRESS] Processed {processed_count}/{total} products ({updated_count} updated so far)...\n")
        
        if product.category and product.category.startswith('Home/'):
            # Remove "Home/" prefix
            old_category = product.category
            new_category = product.category[5:]  # Remove first 5 characters: "Home/"
            
            product.category = new_category
            updated_count += 1
            
            print(f"  [{product.id:5d}] {old_category:40s} → {new_category}")
    
    if updated_count > 0:
        # Commit all changes
        session.commit()
        print(f"\n[√] Updated {updated_count} products")
        print("[√] Changes saved to database")
    else:
        print("[√] No products need updating")
    
    # Show final distribution
    print(f"\n{'='*70}")
    print("  FINAL CATEGORY DISTRIBUTION")
    print(f"{'='*70}\n")
    
    from sqlalchemy import func
    results = session.query(
        Product.category, 
        func.count(Product.id)
    ).group_by(Product.category).order_by(func.count(Product.id).desc()).all()
    
    for category, count in results:
        category_display = category or "None"
        print(f"  {category_display:40s} : {count:5d} products")
    
    print(f"\n{'='*70}\n")
    
    session.close()
    print("[√] Done!\n")

if __name__ == "__main__":
    main()
