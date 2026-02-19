from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Text, Float

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    category = Column(String(256))
    title = Column(String(512))
    brand = Column(String(256))

engine = create_engine('postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway')
Session = sessionmaker(bind=engine)
session = Session()

print("=" * 70)
print("  MERGE CONSTRUCTION EQUIPMENT INTO CONSTRUCTION")
print("=" * 70)

# Find products with "Construction Equipment" category
products = session.query(Product).filter(Product.category == 'Construction Equipment').all()

print(f"\n[√] Found {len(products)} products with 'Construction Equipment' category\n")

if products:
    for product in products:
        print(f"[{product.id}] {product.title[:60]}...")
        print(f"    OLD: {product.category}")
        
        # Try to extract brand and use it, or use Generic
        if product.brand and product.brand != 'Unknown':
            new_category = f"Construction/{product.brand}"
        else:
            new_category = "Construction/Generic"
        
        product.category = new_category
        print(f"    NEW: {new_category}\n")
    
    session.commit()
    print(f"\n[√] Successfully updated {len(products)} products!")
else:
    print("\n[!] No products to update")

# Show final counts
print("\n" + "=" * 70)
print("FINAL CONSTRUCTION CATEGORIES:")
print("=" * 70)
cats = session.query(Product.category).distinct().all()
construction_cats = [c for (c,) in cats if c and 'onstruction' in c]

for cat in sorted(construction_cats):
    count = session.query(Product).filter(Product.category == cat).count()
    print(f"  {cat}: {count} products")

session.close()
