"""
Quick check of product prices in Railway
"""
import os
os.environ['DATABASE_URL'] = 'postgresql://postgres:oqaUYkSoHsdnycMDGTyflRMRBeWQOOdY@caboose.proxy.rlwy.net:54886/railway'

from database.models import Product
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ['DATABASE_URL']
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Get all products
all_products = session.query(Product).all()
prices = [p.price for p in all_products]

# Count by price range
new_prices = [p for p in prices if 16.80 <= p <= 18.00]
old_prices = [p for p in prices if p > 18.00]

print("=" * 60)
print(f"Total products: {len(all_products)}")
print(f"New prices ($16.85-$17.99): {len(new_prices)}")
print(f"Old prices (>$18): {len(old_prices)}")
print("=" * 60)

if new_prices:
    print(f"\nNew price range: ${min(new_prices):.2f} - ${max(new_prices):.2f}")

if old_prices:
    print(f"Old price range: ${min(old_prices):.2f} - ${max(old_prices):.2f}")
    print(f"\nProducts still needing update: {len(old_prices)}")

session.close()
