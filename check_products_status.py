"""
Check which products have PDF links configured
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Product

load_dotenv()

# Railway database
database_url = os.getenv('DATABASE_URL')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()

print("="*80)
print("📊 PRODUCTS STATUS REPORT")
print("="*80)

# Total products
total = session.query(Product).count()
print(f"\n📦 Total products: {total}")

# Products with pdf_url (from CSV)
with_pdf_url = session.query(Product).filter(Product.pdf_url.isnot(None)).count()
print(f"✅ Products with pdf_url (CSV links): {with_pdf_url}")

# Products with Google Drive links
with_google_drive = session.query(Product).filter(Product.google_drive_link.isnot(None)).count()
print(f"☁️  Products with Google Drive links: {with_google_drive}")

# Products needing processing
needs_processing = session.query(Product).filter(
    Product.pdf_url.isnot(None),
    Product.google_drive_link.is_(None)
).count()
print(f"⏳ Products needing Google Drive upload: {needs_processing}")

# Show some examples
print("\n" + "="*80)
print("📋 SAMPLE PRODUCTS NEEDING PROCESSING:")
print("="*80)

products_to_process = session.query(Product).filter(
    Product.pdf_url.isnot(None),
    Product.google_drive_link.is_(None)
).limit(10).all()

for p in products_to_process:
    print(f"\nID: {p.id}")
    print(f"Title: {p.title}")
    print(f"PDF URL: {p.pdf_url[:60]}...")
    print(f"Google Drive: {'❌ Not uploaded' if not p.google_drive_link else '✅ ' + p.google_drive_link[:50]}")

# Show products WITH Google Drive links
print("\n" + "="*80)
print("✅ PRODUCTS ALREADY ON GOOGLE DRIVE:")
print("="*80)

products_ready = session.query(Product).filter(
    Product.google_drive_link.isnot(None)
).limit(5).all()

if products_ready:
    for p in products_ready:
        print(f"\nID: {p.id}")
        print(f"Title: {p.title}")
        print(f"Google Drive: {p.google_drive_link[:60]}...")
else:
    print("\n❌ No products uploaded to Google Drive yet")

session.close()

print("\n" + "="*80)
print("💡 NEXT STEPS:")
print("="*80)
print(f"1. Add GOOGLE_DRIVE_CREDENTIALS_JSON to Railway Variables")
print(f"2. Add GOOGLE_DRIVE_FOLDER_ID=1fuchPndGleKsfyVYZSUvzsqwLSpVFqEG")
print(f"3. Run: python railway_pdf_processor.py all")
print(f"   → Will process {needs_processing} products")
