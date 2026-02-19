"""
Update products in Railway with multiple images - using slug/handle matching
"""
import os
os.environ['DATABASE_URL'] = 'postgresql://postgres:oqaUYkSoHsdnycMDGTyflRMRBeWQOOdY@caboose.proxy.rlwy.net:54886/railway'

import csv
from database.models import Product
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ['DATABASE_URL']
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

print("📊 Collecting images from CSV...")
print("=" * 60)

# Collect all images for each product (by handle)
products_data = {}  # handle -> images[]

with open('shopify.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    
    for row in reader:
        handle = row.get('Handle', '').strip()
        img = row.get('Image Src', '').strip()
        
        if not handle:
            continue
            
        if handle not in products_data:
            products_data[handle] = []
        
        if img and img not in products_data[handle]:
            products_data[handle].append(img)

print(f"Found {len(products_data)} unique products")
multi_image = sum(1 for imgs in products_data.values() if len(imgs) > 1)
print(f"Products with multiple images: {multi_image}")

# Sample products with multiple images
sample_multi = [(h, imgs) for h, imgs in products_data.items() if len(imgs) > 1][:5]
print("\nSample products with multiple images:")
for handle, imgs in sample_multi:
    print(f"  {handle}: {len(imgs)} images")

# Update database
print("\n🔄 Updating products in Railway database...")
print("=" * 60)

updated = 0
skipped = 0

for handle, images in products_data.items():
    if len(images) == 0:
        continue
    
    # Find product by slug (slug should match handle from CSV)
    product = session.query(Product).filter(Product.slug == handle).first()
    
    if product:
        new_image_url = ','.join(images)
        old_count = len(product.image_url.split(',')) if product.image_url else 0
        new_count = len(images)
        
        if new_count > old_count:
            product.image_url = new_image_url
            updated += 1
            
            if updated % 100 == 0:
                print(f"  ✅ Updated {updated} products...")
                session.commit()
    else:
        skipped += 1

session.commit()

print("\n" + "=" * 60)
print(f"✅ Updated: {updated} products")
print(f"⏭️  Skipped: {skipped} (not found in DB)")
print("=" * 60)

# Show sample products with multiple images
print("\n📸 Sample products with multiple images:")
products = session.query(Product).filter(Product.image_url.like('%,%')).limit(10).all()
for p in products:
    img_count = len(p.image_url.split(',')) if p.image_url else 0
    print(f"  • {p.title[:70]} - {img_count} images")

session.close()
print("\n✅ Done!")