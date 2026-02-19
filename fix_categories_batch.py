"""
Fix Categories - Remove 'Home/' prefix
Commits in smaller batches (100 at a time)
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Product

# Database configuration
DATABASE_URL = "postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway"

def main():
    print("\n" + "="*70)
    print("  REMOVE 'Home/' PREFIX FROM CATEGORIES - BATCH MODE")
    print("="*70 + "\n")
    
    # Initialize database
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Get all products with 'Home/' prefix
    products = session.query(Product).filter(
        Product.category.like('Home/%')
    ).order_by(Product.id).all()
    
    total = len(products)
    print(f"[√] Found {total} products with 'Home/' prefix\n")
    
    if total == 0:
        print("No products to fix!\n")
        session.close()
        return
    
    # Process in batches of 100
    batch_size = 100
    updated_count = 0
    
    for i in range(0, total, batch_size):
        batch = products[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total + batch_size - 1) // batch_size
        
        print(f"[BATCH {batch_num}/{total_batches}] Processing {len(batch)} products...")
        
        batch_updated = 0
        for product in batch:
            if product.category and product.category.startswith('Home/'):
                old_category = product.category
                new_category = product.category[5:]  # Remove 'Home/'
                product.category = new_category
                batch_updated += 1
                
                # Show first 5 changes in batch
                if batch_updated <= 5:
                    print(f"  [{product.id}] {old_category} → {new_category}")
        
        if batch_updated > 5:
            print(f"  ... and {batch_updated - 5} more changes")
        
        # Commit this batch
        session.commit()
        updated_count += batch_updated
        print(f"  [√] Batch saved! ({updated_count}/{total} total)\n")
    
    print("="*70)
    print(f"[√] COMPLETE! Updated {updated_count} products")
    print("="*70 + "\n")
    
    session.close()

if __name__ == "__main__":
    main()
