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

# Find BMW 1 Series F20/F21
product = session.query(Product).filter(
    Product.title.ilike('%BMW 1 SERIES F20%F21%')
).first()

if product:
    print(f"Title: {product.title}\n")
    print("=" * 70)
    print("DESCRIPTION:")
    print("=" * 70)
    print(product.description)
    print("=" * 70)
    
    # Check what's in it
    if 'REFERENCE DRIVETRAIN' in product.description:
        print("\n✓ Contains 'REFERENCE DRIVETRAIN'")
    if 'REFERENCE POWERTRAIN' in product.description:
        print("✓ Contains 'REFERENCE POWERTRAIN'")
else:
    print("Product not found")

session.close()
