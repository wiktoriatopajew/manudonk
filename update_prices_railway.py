"""
Update all product prices on RAILWAY production database
Only use rounded values: .00, .80, .85, .90, .95, .99
"""
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import random

# RAILWAY DATABASE URL - paste it here
RAILWAY_DATABASE_URL = input("Paste Railway DATABASE_URL: ").strip()

# Allowed price points (only nice rounded values)
ALLOWED_PRICES = [
    16.80,
    16.85,
    16.90,
    16.95,
    16.99,
    17.00
]

Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(500))
    price = Column(Float)
    brand = Column(String(200))
    model = Column(String(200))

def update_railway_prices():
    """Update all product prices on Railway with varied rounded amounts"""
    
    print("🚀 Connecting to Railway database...")
    engine = create_engine(RAILWAY_DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Get all products
        products = session.query(Product).all()
        total = len(products)
        
        print(f"✅ Connected! Found {total} products to update")
        print(f"Updating prices to random values from: {ALLOWED_PRICES}")
        
        confirm = input(f"\n⚠️  Update {total} products on RAILWAY? (yes/no): ").lower()
        if confirm != 'yes':
            print("❌ Cancelled")
            return
        
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
        print(f"✅ Updated {updated} products successfully on RAILWAY!")
        
        # Show distribution
        print("\nPrice distribution on RAILWAY:")
        for price in sorted(set(ALLOWED_PRICES)):
            count = session.query(Product).filter(Product.price == price).count()
            print(f"  ${price:.2f}: {count} products")
            
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("🔄 RAILWAY PRICE UPDATE SCRIPT")
    print("=" * 50)
    update_railway_prices()
