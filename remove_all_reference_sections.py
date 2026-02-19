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
    category = Column(String(256))

engine = create_engine('postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway')
Session = sessionmaker(bind=engine)
session = Session()

print("=" * 70)
print("  REMOVE ALL REFERENCE POWERTRAIN/DRIVETRAIN SECTIONS")
print("=" * 70)

# Get only Cars and Trucks products
products = session.query(Product).filter(
    (Product.category.like('Cars%')) | (Product.category.like('Trucks%'))
).all()

print(f"\n[√] Checking {len(products)} products in Cars & Trucks categories\n")

# Patterns to match various reference sections:
# 1. "REFERENCE DRIVETRAIN:" + everything after
# 2. "REFERENCE POWERTRAIN" + everything after  
# 3. "Powertrain\nEngine" as standalone section
# 4. "DRIVETRAIN:\nEngine" as standalone section
patterns = [
    r'REFERENCE\s+DRIVETRAIN:?\s*\n.*?(?=\n\n[A-Z]{3,}|$)',
    r'REFERENCE\s+POWERTRAIN:?\s*\n.*?(?=\n\n[A-Z]{3,}|$)',
    r'\n\s*Powertrain\s*\n\s*Engine.*?(?=\n\n[A-Z]{3,}|$)',
    r'\n\s*DRIVETRAIN:?\s*\n\s*Engine.*?(?=\n\n[A-Z]{3,}|$)',
]

updated = 0
examples_shown = 0

for product in products:
    if not product.description:
        continue
    
    old_desc = product.description
    new_desc = old_desc
    
    # Try each pattern
    for pattern in patterns:
        new_desc = re.sub(pattern, '', new_desc, flags=re.IGNORECASE | re.DOTALL)
    
    new_desc = new_desc.strip()
    
    if new_desc != old_desc:
        if examples_shown < 5:
            print(f"[{product.id}] {product.title[:55]}...")
            print(f"  Category: {product.category}")
            print(f"  Removed: {len(old_desc) - len(new_desc)} chars")
            if 'REFERENCE DRIVETRAIN' in old_desc.upper():
                print(f"  Found: REFERENCE DRIVETRAIN")
            if 'REFERENCE POWERTRAIN' in old_desc.upper():
                print(f"  Found: REFERENCE POWERTRAIN")
            print()
            examples_shown += 1
        
        product.description = new_desc
        updated += 1
        
        # Commit every 100 products
        if updated % 100 == 0:
            session.commit()
            print(f"[PROGRESS] Saved {updated} products...")

session.commit()
print(f"\n[√] Successfully cleaned {updated} product descriptions!")
print("=" * 70)

session.close()
