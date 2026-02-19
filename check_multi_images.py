"""
Check if products now have multiple images
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

# Check how many products have multiple images
total = session.query(Product).count()
multi_image = session.query(Product).filter(Product.image_url.like('%,%')).count()

print("=" * 60)
print(f"Total products: {total}")
print(f"Products with multiple images: {multi_image}")
print("=" * 60)

# Show sample products
products = session.query(Product).filter(Product.image_url.like('%,%')).limit(15).all()
print("\n📸 Sample products with multiple images:")
for p in products:
    img_count = len(p.image_url.split(',')) if p.image_url else 0
    print(f"  • {p.title[:70]} - {img_count} images")

session.close()
