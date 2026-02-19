from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from database.models import Product

DATABASE_URL = "postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Get category distribution
results = session.query(
    Product.category, 
    func.count(Product.id)
).group_by(Product.category).order_by(func.count(Product.id).desc()).limit(25).all()

print('\n' + '='*70)
print('  FINALNA DYSTRYBUCJA KATEGORII')
print('='*70 + '\n')

for cat, count in results:
    category_display = cat or "None"
    print(f'{category_display[:50]:50s} : {count:5d}')

# Check for remaining Home/ prefixes
total_with_home = session.query(func.count(Product.id)).filter(
    Product.category.like('Home/%')
).scalar()

print(f'\n[CHECK] Produkty z "Home/" prefix: {total_with_home}')
print('='*70 + '\n')

session.close()
