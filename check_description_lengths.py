"""
Check description lengths in Railway database
"""
import os
os.environ['DATABASE_URL'] = 'postgresql://postgres:oqaUYkSoHsdnycMDGTyflRMRBeWQOOdY@caboose.proxy.rlwy.net:54886/railway'

from database.models import Product
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func

DATABASE_URL = os.environ['DATABASE_URL']
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Count products by description length
total = session.query(Product).count()
truncated = session.query(Product).filter(
    func.length(Product.description) <= 500
).count()
full = session.query(Product).filter(
    func.length(Product.description) > 500
).count()

print("=" * 60)
print(f"Total products: {total}")
print(f"Short descriptions (≤500 chars): {truncated}")
print(f"Full descriptions (>500 chars): {full}")
print("=" * 60)

# Show sample
print("\n📝 Sample products:")
products = session.query(Product).limit(5).all()
for p in products:
    desc_len = len(p.description) if p.description else 0
    print(f"\n• {p.title[:70]}")
    print(f"  Length: {desc_len} chars")
    if p.description and desc_len > 200:
        preview = p.description[:200].replace('\n', ' ')
        print(f"  {preview}...")

session.close()
