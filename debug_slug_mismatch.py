"""
Debug: Check slug mismatch between CSV and database
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

# Get sample from CSV
csv_handles = []
with open('shopify.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        if i >= 10:
            break
        handle = row.get('Handle', '').strip()
        title = row.get('Title', ' ').strip()
        if handle:
            csv_handles.append((handle, title))

print("SAMPLE FROM CSV:")
print("=" * 80)
for handle, title in csv_handles[:5]:
    print(f"Handle: {handle}")
    print(f"Title:  {title}")
    print()

# Get sample from database
db_products = session.query(Product).limit(10).all()

print("\nSAMPLE FROM DATABASE:")
print("=" * 80)
for p in db_products[:5]:
    print(f"Slug:  {p.slug}")
    print(f"Title: {p.title}")
    print()

session.close()
