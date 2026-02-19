"""
Import products from test2.csv to Railway with Google Drive integration
"""
import os
import csv
import re
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Railway PostgreSQL connection
DATABASE_URL = os.getenv("DATABASE_URL")

def generate_slug(title, product_id):
    """Generate SEO-friendly slug"""
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    slug = slug[:50]  # Limit length
    return f"{slug}-{product_id}"

print("🚀 Importing test2.csv products to Railway...")
print(f"🔗 Connecting to Railway PostgreSQL...")

# Read CSV
products = []
with open('test2.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        product = {
            'id': row['ID'],
            'title': row['English Title'],
            'description': f"{row['Category']} - {row['Original HTML Name']}",
            'price': 29.99,  # Default price
            'category': row['Category'],
            'brand': row['Category'].split()[0] if row['Category'] else 'Generic',
            'model': row['ID'],
            'image_url': 'https://via.placeholder.com/400x300?text=Manual',  # Placeholder
            'pdf_link': row['Link PDF']
        }
        products.append(product)

print(f"✅ Found {len(products)} products in CSV")

# Connect to Railway PostgreSQL
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Insert products
imported = 0
skipped = 0

for product in products:
    slug = generate_slug(product['title'], product['id'])
    
    try:
        cursor.execute("""
            INSERT INTO products (title, description, price, category, brand, model, image_url, slug, pdf_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (slug) DO NOTHING
        """, (
            product['title'],
            product['description'],
            product['price'],
            product['category'],
            product['brand'],
            product['model'],
            product['image_url'],
            slug,
            product['pdf_link']  # Store the original PDF download link
        ))
        
        if cursor.rowcount > 0:
            imported += 1
            print(f"✅ Imported: {product['title'][:50]}... (ID: {product['id']})")
        else:
            skipped += 1
            print(f"⏭️  Skipped (exists): {product['title'][:50]}...")
            
    except Exception as e:
        print(f"❌ Error importing {product['title']}: {e}")
        skipped += 1

conn.commit()
cursor.close()
conn.close()

print(f"\n🎉 Import complete!")
print(f"✅ Imported: {imported}")
print(f"⏭️  Skipped: {skipped}")
print(f"📊 Total: {len(products)}")
