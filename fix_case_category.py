from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    category = Column(String(256))
    brand = Column(String(256))
    title = Column(String(512))

engine = create_engine('postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway')
Session = sessionmaker(bind=engine)
session = Session()

# Fix Construction/Construction Equipment -> Construction/Case
products = session.query(Product).filter(
    Product.category == 'Construction/Construction Equipment'
).all()

print(f"Found {len(products)} products to fix")

for p in products:
    p.category = 'Construction/Case'
    p.brand = 'Case'
    print(f"[{p.id}] {p.title[:50]}... -> Construction/Case")

session.commit()
print(f"\n✓ Updated {len(products)} products to Construction/Case")

session.close()
