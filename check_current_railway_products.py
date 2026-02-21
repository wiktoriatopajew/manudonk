"""
Check products in current Railway database
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

print("Checking products in Railway database...")
print("=" * 60)

# Check total
total = session.query(Product).count()
print(f"Total products: {total}")

# Check categories
print("\nCategories:")
cats = session.query(Product.category).distinct().all()
for cat in sorted(cats):
    count = session.query(Product).filter(Product.category == cat[0]).count()
    print(f"  {cat[0]:15} {count:5} products")

# Check title patterns
workshop_count = session.query(Product).filter(Product.title.ilike('%Workshop Repair Service Manual%')).count()
print(f"\nProducts with 'Workshop Repair Service Manual': {workshop_count}")

# Sample titles
print("\nSample titles (first 10):")
products = session.query(Product).limit(10).all()
for p in products:
    print(f"  {p.title[:80]}")

session.close()
