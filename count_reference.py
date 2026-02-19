from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Text

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    description = Column(Text)
    category = Column(String(256))

engine = create_engine('postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway')
Session = sessionmaker(bind=engine)
session = Session()

count = session.query(Product).filter(
    (Product.category.like('Cars%')) | (Product.category.like('Trucks%'))
).filter(
    Product.description.ilike('%REFERENCE%')
).count()

print(f'{count} products with REFERENCE in description')

session.close()
