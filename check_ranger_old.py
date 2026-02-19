from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Text

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    title = Column(String(512))
    description = Column(Text)

engine = create_engine('postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway')
Session = sessionmaker(bind=engine)
session = Session()

# Find Ford Ranger PE/PG/PH product
product = session.query(Product).filter(
    Product.title.ilike('%FORD RANGER PE%PG%PH%1998-2005%')
).first()

if product:
    print(f"Title: {product.title}\n")
    print("=" * 70)
    print("FULL DESCRIPTION:")
    print("=" * 70)
    print(product.description)
    print("=" * 70)
    print(f"\nLength: {len(product.description)} characters")
else:
    print("Product not found")

session.close()
