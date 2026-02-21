"""
Check product categories in Railway database
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

print('='*60)
print('CATEGORY DISTRIBUTION IN RAILWAY DATABASE')
print('='*60)

cats = session.query(Product.category).distinct().all()
total = 0

for cat in sorted(cats):
    count = session.query(Product).filter(Product.category == cat[0]).count()
    print(f'{cat[0]:15} {count:5} products')
    total += count

print('='*60)
print(f'TOTAL: {total} products')
print('='*60)

session.close()
