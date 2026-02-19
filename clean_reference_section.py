from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Text
import re

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    title = Column(String(512))
    description = Column(Text)

engine = create_engine('postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway')
Session = sessionmaker(bind=engine)
session = Session()

print("=" * 70)
print("  REMOVE REFERENCE POWERTRAIN SECTION (COMPLETE)")
print("=" * 70)

# Find all products with REFERENCE in description
products = session.query(Product).filter(
    Product.description.ilike('%REFERENCE%POWERTRAIN%')
).all()

print(f"\n[√] Found {len(products)} products with REFERENCE POWERTRAIN\n")

updated = 0
for product in products[:10]:  # Show first 10
    old_desc = product.description
    
    # Remove everything from REFERENCE POWERTRAIN to the end
    # This regex finds REFERENCE POWERTRAIN and removes everything after it
    new_desc = re.sub(
        r'REFERENCE\s+POWERTRAIN.*',
        '',
        old_desc,
        flags=re.IGNORECASE | re.DOTALL
    )
    
    # Also clean up trailing whitespace
    new_desc = new_desc.strip()
    
    if new_desc != old_desc:
        print(f"[{product.id}] {product.title[:50]}...")
        print(f"  OLD LENGTH: {len(old_desc)} chars")
        print(f"  NEW LENGTH: {len(new_desc)} chars")
        print(f"  REMOVED: {len(old_desc) - len(new_desc)} chars\n")

print("\nApplying to ALL products...")

# Now apply to all products
updated = 0
for product in products:
    old_desc = product.description
    
    new_desc = re.sub(
        r'REFERENCE\s+POWERTRAIN.*',
        '',
        old_desc,
        flags=re.IGNORECASE | re.DOTALL
    )
    
    new_desc = new_desc.strip()
    
    if new_desc != old_desc:
        product.description = new_desc
        updated += 1

session.commit()

print(f"\n[√] Successfully cleaned {updated} product descriptions!")
print("=" * 70)

session.close()
