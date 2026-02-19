import os
os.environ['DATABASE_URL'] = 'postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway'

from database.models import *
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

engine = create_engine(os.environ['DATABASE_URL'])
Session = sessionmaker(bind=engine)
session = Session()

total = session.query(Product).count()
print(f'✅ Total products in Manual Bear database: {total}')

cats = session.query(Product.category, func.count(Product.id)).group_by(Product.category).all()
print('\n📊 Category distribution:')
for cat, count in sorted(cats, key=lambda x: x[1], reverse=True):
    print(f'  {cat}: {count}')

print(f'\n🖼️ Products with multiple images:')
multi = session.query(Product.title, Product.image_url).filter(Product.image_url.like('%,%')).limit(5).all()
for m in multi:
    images_count = len(m[1].split(',')) if m[1] else 0
    print(f'  {m[0][:60]}: {images_count} images')

session.close()
