"""
Update products in Railway with multiple images - match by title
"""
import os
os.environ['DATABASE_URL'] = 'postgresql://postgres:oqaUYkSoHsdnycMDGTyflRMRBeWQOOdY@caboose.proxy.rlwy.net:54886/railway'

import csv
from database.models import Product
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ['DATABASE_URL']
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine, expire_on_commit=False)  # Don't expire objects after commit
session = Session()

print("📊 Step 1: Collecting images from CSV...")
print("=" * 60)

# Collect all images for each product title
csv_products = {}  # title -> images[]

with open('shopify.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    
    current_handle = None
    current_title = None
    
    for row in reader:
        handle = row.get('Handle', '').strip()
        title = row.get('Title', '').strip()
        img = row.get('Image Src', '').strip()
        
        # First row of a product (has title)
        if title:
            current_handle = handle
            current_title = title
            if title not in csv_products:
                csv_products[title] = []
        
        # Add image to current product
        if current_title and img and img not in csv_products[current_title]:
            csv_products[current_title].append(img)

print(f"Found {len(csv_products)} unique products in CSV")
multi_image = sum(1 for imgs in csv_products.values() if len(imgs) > 1)
print(f"Products with multiple images: {multi_image}")

# Sample products with multiple images
sample_multi = [(t, imgs) for t, imgs in csv_products.items() if len(imgs) > 1][:5]
print("\nSample products with multiple images:")
for title, imgs in sample_multi:
    print(f"  {title[:60]}: {len(imgs)} images")

print("\n📊 Step 2: Loading all products from Railway database...")
print("=" * 60)

# Load ALL products from database at once
db_products = session.query(Product).all()
print(f"Found {len(db_products)} products in database")

# Create dictionary of products by title
db_by_title = {p.title: p for p in db_products}
print(f"Indexed {len(db_by_title)} products by title")

print("\n🔄 Step 3: Updating products...")
print("=" * 60)

updated = 0
skipped = 0

for title, images in csv_products.items():
    if len(images) == 0:
        continue
    
    # Find product by title
    product = db_by_title.get(title)
    
    if product:
        new_image_url = ','.join(images)
        old_count = len(product.image_url.split(',')) if product.image_url else 0
        new_count = len(images)
        
        if new_count > old_count:
            product.image_url = new_image_url
            updated += 1
            
            # Commit every 50 products to avoid timeout
            if updated % 50 == 0:
                print(f"  ✅ Updated {updated} products, committing...")
                session.commit()
    else:
        skipped += 1
        if skipped <= 5:  # Show first few skipped
            print(f"  ⏭️  Skipped: {title[:60]}")

# Commit remaining changes
print(f"\n💾 Committing final {updated % 50} changes...")
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
