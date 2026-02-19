"""
Update all product prices in Railway database to nice random prices $16.85-$17.99
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

print("💰 Updating product prices in Railway database...")
print("=" * 60)

# Load ALL products
all_products = session.query(Product).all()
print(f"Found {len(all_products)} products")

# Show current price distribution
old_prices = [p.price for p in all_products]
print(f"\nCurrent price range: ${min(old_prices):.2f} - ${max(old_prices):.2f}")

updated = 0

print("\n🔄 Updating prices...")
for product in all_products:
    old_price = product.price
    new_price = generate_nice_price()
    product.price = new_price
    updated += 1
    
    # Commit every 25 products  
    if updated % 25 == 0:
        print(f"  ✅ Updated {updated} products, committing...")
        session.commit()

# Commit remaining
if updated % 25 != 0:
    print(f"\n💾 Committing final {updated % 25} changes...")
    session.commit()

print("\n" + "=" * 60)
print(f"✅ Updated {updated} products")
print("=" * 60)

# Show new price distribution
new_prices = [p.price for p in session.query(Product).all()]
price_counts = {}
for price in new_prices:
    price_counts[price] = price_counts.get(price, 0) + 1

print("\n💵 New price distribution:")
for price in sorted(price_counts.keys()):
    count = price_counts[price]
    print(f"  ${price:.2f}: {count} products")

print(f"\n📊 New price range: ${min(new_prices):.2f} - ${max(new_prices):.2f}")

# Show sample products
print("\n📝 Sample products with new prices:")
sample_products = session.query(Product).limit(10).all()
for p in sample_products:
    print(f"  • {p.title[:60]} - ${p.price:.2f}")

session.close()
print("\n✅ Done!")
