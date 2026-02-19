"""
Update ONLY products with old prices (>$18) to new prices $16.85-$17.99
"""
import os
os.environ['DATABASE_URL'] = 'postgresql://postgres:oqaUYkSoHsdnycMDGTyflRMRBeWQOOdY@caboose.proxy.rlwy.net:54886/railway'

import random
from database.models import Product
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def generate_nice_price():
    """Generate nice random price between $16.85-$17.99"""
    nice_prices = [
        16.85, 16.89, 16.95, 16.99,
        17.49, 17.79, 17.85, 17.89, 17.95, 17.99
    ]
    return random.choice(nice_prices)

DATABASE_URL = os.environ['DATABASE_URL']
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine, expire_on_commit=False)
session = Session()

print("💰 Updating ONLY products with old prices...")
print("=" * 60)

# Load ONLY products with old prices (>$18)
old_price_products = session.query(Product).filter(Product.price > 18.0).all()
print(f"Found {len(old_price_products)} products with old prices")

if len(old_price_products) == 0:
    print("\n✅ All products already have new prices!")
    session.close()
    exit(0)

updated = 0

print("\n🔄 Updating prices...")
for product in old_price_products:
    old_price = product.price
    new_price = generate_nice_price()
    product.price = new_price
    updated += 1
    
    # Commit every 10 products  
    if updated % 10 == 0:
        print(f"  ✅ Updated {updated} products, committing...")
        session.commit()

# Commit remaining
if updated % 10 != 0:
    print(f"\n💾 Committing final {updated % 10} changes...")
    session.commit()

print("\n" + "=" * 60)
print(f"✅ Updated {updated} products")
print("=" * 60)

# Verify all done
remaining = session.query(Product).filter(Product.price > 18.0).count()
print(f"\n📊 Products still with old prices: {remaining}")

if remaining == 0:
    print("✅ SUCCESS! All products now have new prices!")

# Show sample
print("\n📝 Sample products:")
sample = session.query(Product).limit(10).all()
for p in sample:
    print(f"  • {p.title[:60]} - ${p.price:.2f}")

session.close()
print("\n✅ Done!")
