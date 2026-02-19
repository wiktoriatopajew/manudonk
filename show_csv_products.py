"""
Show which products are from test2.csv (have pdf_url)
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
print("📦 PRODUKTY Z test2.csv (mają pdf_url)")
print("="*80)

# Products from test2.csv have pdf_url
products_from_csv = session.query(Product).filter(
    Product.pdf_url.isnot(None)
).order_by(Product.id).all()

print(f"\n✅ Znaleziono: {len(products_from_csv)} produktów z test2.csv\n")

for i, p in enumerate(products_from_csv, 1):
    print(f"{i}. ID: {p.id}")
    print(f"   Tytuł: {p.title}")
    print(f"   Kategoria: {p.category}")
    print(f"   Cena: ${p.price}")
    print(f"   PDF URL: {p.pdf_url[:70]}...")
    print(f"   Google Drive: {'✅ ' + p.google_drive_link[:50] + '...' if p.google_drive_link else '❌ Nie uploadowane'}")
    print(f"   Slug: /manuals/{p.slug}")
    print()

session.close()

print("="*80)
print("💡 Te produkty czekają na upload do Google Drive")
print("="*80)
