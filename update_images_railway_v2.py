"""
Update products in Railway with multiple images - optimized version
Loads all products first, then matches in memory
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

print("📊 Step 1: Collecting images from CSV...")
print("=" * 60)

# Collect all images for each product (by handle)
csv_products = {}  # handle -> images[]

with open('shopify.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    
    for row in reader:
        handle = row.get('Handle', '').strip()
        img = row.get('Image Src', '').strip()
        
        if not handle:
            continue
            
        if handle not in csv_products:
            csv_products[handle] = []
        
        if img and img not in csv_products[handle]:
            csv_products[handle].append(img)

print(f"Found {len(csv_products)} unique products in CSV")
multi_image = sum(1 for imgs in csv_products.values() if len(imgs) > 1)
print(f"Products with multiple images: {multi_image}")

# Sample products with multiple images
sample_multi = [(h, imgs) for h, imgs in csv_products.items() if len(imgs) > 1][:5]
print("\nSample products with multiple images:")
for handle, imgs in sample_multi:
    print(f"  {handle}: {len(imgs)} images")

print("\n📊 Step 2: Loading all products from Railway database...")
print("=" * 60)

# Load ALL products from database at once
db_products = session.query(Product).all()
print(f"Found {len(db_products)} products in database")

# Create dictionary of products by slug
db_by_slug = {p.slug: p for p in db_products}
print(f"Indexed {len(db_by_slug)} products by slug")

print("\n🔄 Step 3: Updating products...")
print("=" * 60)

updated = 0
skipped = 0

for handle, images in csv_products.items():
    if len(images) == 0:
        continue
    
    # Find product by slug (slug should match handle from CSV)
    product = db_by_slug.get(handle)
    
    if product:
        new_image_url = ','.join(images)
        old_count = len(product.image_url.split(',')) if product.image_url else 0
        new_count = len(images)
        
        if new_count > old_count:
            product.image_url = new_image_url
            updated += 1
            
            if updated % 100 == 0:
                print(f"  ✅ Updated {updated} products...")
    else:
        skipped += 1

# Commit all changes
print("\n💾 Committing changes to database...")
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
