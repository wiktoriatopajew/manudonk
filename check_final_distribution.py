"""
Verify final category distribution
"""
from database.models import Product
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///./database/products.db')
Session = sessionmaker(bind=engine)
session = Session()

print('='*60)
print('FINAL CATEGORY DISTRIBUTION')
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
