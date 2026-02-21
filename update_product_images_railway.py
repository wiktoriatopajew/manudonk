"""
Update products in Railway database with multiple images from CSV
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

print("Collecting images from CSV...")
print("=" * 60)

# Collect all images for each handle
product_images = {}
with open('shopify.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        handle = row.get('Handle', '').strip()
        img = row.get('Image Src', '').strip()
        
        if handle and img:
            if handle not in product_images:
                product_images[handle] = []
            if img not in product_images[handle]:
                product_images[handle].append(img)

print(f"Found {len(product_images)} products with images")
multi_image_products = {h: imgs for h, imgs in product_images.items() if len(imgs) > 1}
print(f"Products with multiple images: {len(multi_image_products)}")

# Update products in database
print("\nUpdating products in database...")
updated = 0
not_found = 0

for handle, images in product_images.items():
    # Try to find product by slug (handle is used as basis for slug)
    slug_base = handle.lower().replace('_', '-')
    
    # Try multiple slug variations
    products = session.query(Product).filter(
        Product.slug.like(f"{slug_base}%")
    ).all()
    
    if not products:
        # Try finding by first part of handle
        first_part = handle.split('-')[0] if '-' in handle else handle
        products = session.query(Product).filter(
            Product.slug.like(f"%{first_part}%")
        ).limit(1).all()
    
    if products:
        for product in products[:1]:  # Update first match
            image_url = ','.join(images)
            if product.image_url != image_url:
                product.image_url = image_url
                updated += 1
                if updated % 100 == 0:
                    print(f"  Updated {updated} products...")
    else:
        not_found += 1

session.commit()

print("\n" + "=" * 60)
print(f"✅ Updated {updated} products with images")
print(f"   Products with multiple images: {len([h for h,imgs in product_images.items() if len(imgs) > 1 and h in [p.slug for p in session.query(Product).all()]])}")
print(f"⚠️  Not found: {not_found} handles")
print("=" * 60)

# Sample updated products
print("\nSample products with multiple images:")
products = session.query(Product).filter(Product.image_url.like('%,%')).limit(5).all()
for p in products:
    img_count = len(p.image_url.split(',')) if p.image_url else 0
    print(f"  {p.title[:60]}: {img_count} images")

session.close()
