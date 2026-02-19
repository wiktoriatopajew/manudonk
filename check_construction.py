from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Text, Float

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    category = Column(String(256))
    title = Column(String(512))

engine = create_engine('postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway')
Session = sessionmaker(bind=engine)
session = Session()

# Get all construction-related categories
cats = session.query(Product.category).distinct().all()
construction_cats = [c for (c,) in cats if c and 'onstruction' in c]

print("Construction-related categories:")
for cat in sorted(construction_cats):
    count = session.query(Product).filter(Product.category == cat).count()
    print(f"  {cat}: {count} products")

session.close()
