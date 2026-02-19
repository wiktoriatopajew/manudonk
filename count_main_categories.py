from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    category = Column(String(256))

engine = create_engine('postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway')
Session = sessionmaker(bind=engine)
session = Session()

# Get all main categories
all_categories = session.query(Product.category).distinct().all()
main_cats = set()

for (cat,) in all_categories:
    if cat:
        main_cat = cat.split('/')[0] if '/' in cat else cat
        main_cats.add(main_cat)

print("=" * 50)
print("MAIN CATEGORIES:")
print("=" * 50)

for cat in sorted(main_cats):
    # Count products in this main category
    count = session.query(Product).filter(Product.category.like(f'{cat}%')).count()
    print(f"  {cat}: {count} products")

print(f"\nTotal: {len(main_cats)} main categories")

session.close()
