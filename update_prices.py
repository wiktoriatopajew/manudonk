"""
Update all product prices to varied amounts around $16.80-$17.00
Only use rounded values: .00, .80, .85, .90, .95, .99
"""
from database.models import Product, get_session
import random

# Allowed price points (only nice rounded values)
ALLOWED_PRICES = [
    16.80,
    16.85,
    16.90,
    16.95,
    16.99,
    17.00
]

def update_all_prices():
    """Update all product prices with varied rounded amounts"""
    session = get_session()
    try:
        # Get all products
        products = session.query(Product).all()
        total = len(products)
        
        print(f"Found {total} products to update")
        print(f"Updating prices to random values from: {ALLOWED_PRICES}")
        print("=" * 50)
        
        updated = 0
        for product in products:
            # Pick random price from allowed values
            new_price = random.choice(ALLOWED_PRICES)
            old_price = product.price
            
            product.price = new_price
            updated += 1
            
            if updated <= 10:  # Show first 10 as examples
                print(f"{product.title[:50]:50} | ${old_price:.2f} → ${new_price:.2f}")
        
        # Commit all changes
        session.commit()
        
        print("=" * 50)
        print(f"✅ Updated {updated} products successfully!")
        
        # Show distribution
        print("\nPrice distribution:")
        for price in sorted(set(ALLOWED_PRICES)):
            count = sum(1 for p in products if abs(p.price - price) < 0.01)
            print(f"  ${price:.2f}: {count} products")
            
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("🔄 Starting price update...")
    print()
    
    response = input("Update ALL product prices? (yes/no): ")
    if response.lower() == 'yes':
        update_all_prices()
    else:
        print("Cancelled.")
