"""
Update product descriptions in Railway database with full text (no truncation)
"""
import os
os.environ['DATABASE_URL'] = 'postgresql://postgres:oqaUYkSoHsdnycMDGTyflRMRBeWQOOdY@caboose.proxy.rlwy.net:54886/railway'

import csv
from database.models import Product
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def normalize_text(text):
    if not text:
        return ""
    text = str(text).strip()
    # Remove HTML tags
    import re
    text = re.sub(r'<[^>]+>', '', text)
    # Clean up encoding issues
    text = text.replace('â€"', '-').replace('â€™', "'").replace('Â', ' ')
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
    return text.strip()

DATABASE_URL = os.environ['DATABASE_URL']
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine, expire_on_commit=False)
session = Session()

print("📊 Step 1: Collecting full descriptions from CSV...")
print("=" * 60)

# Collect descriptions by product title
csv_descriptions = {}  # title -> description

with open('shopify.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    
    for row in reader:
        title = row.get('Title', '').strip()
        description = normalize_text(row.get('Body (HTML)', ''))
        
        # Only store if this is a main product row (has title and description)
        if title and description:
            csv_descriptions[title] = description

print(f"Found {len(csv_descriptions)} products with descriptions in CSV")

# Check how many need updating (have truncated descriptions)
truncated_count = sum(1 for desc in csv_descriptions.values() if len(desc) > 500)
print(f"Products with descriptions > 500 chars: {truncated_count}")

print("\n📊 Step 2: Loading products from Railway database...")
print("=" * 60)

# Load ALL products from database
db_products = session.query(Product).all()
print(f"Found {len(db_products)} products in database")

# Create dictionary by title
db_by_title = {p.title: p for p in db_products}

print("\n🔄 Step 3: Updating product descriptions...")
print("=" * 60)

updated = 0
skipped = 0
already_full = 0

for title, full_description in csv_descriptions.items():
    product = db_by_title.get(title)
    
    if product:
        # Check if current description is truncated or missing
        current_len = len(product.description) if product.description else 0
        new_len = len(full_description)
        
        if new_len > current_len:
            product.description = full_description
            updated += 1
            
            # Commit every 25 products to avoid timeout
            if updated % 25 == 0:
                print(f"  ✅ Updated {updated} products, committing...")
                session.commit()
        else:
            already_full += 1
    else:
        skipped += 1

# Commit remaining changes
if updated % 25 != 0:
    print(f"\n💾 Committing final {updated % 25} changes...")
    session.commit()

print("\n" + "=" * 60)
print(f"✅ Updated: {updated} products")
print(f"⏭️  Already full: {already_full} products")
print(f"⏭️  Skipped: {skipped} (not found in DB)")
print("=" * 60)

# Show sample of updated products
print("\n📝 Sample products with full descriptions:")
updated_products = session.query(Product).limit(5).all()
for p in updated_products:
    desc_len = len(p.description) if p.description else 0
    print(f"  • {p.title[:70]}")
    print(f"    Description length: {desc_len} chars")
    if p.description:
        preview = p.description[:150].replace('\n', ' ')
        print(f"    Preview: {preview}...")
    print()

session.close()
print("✅ Done!")
