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
print("  REMOVE POWERTRAIN REFERENCE SECTION (COMPLETE)")
print("=" * 70)

# Get all products
all_products = session.query(Product).all()
print(f"\n[√] Checking {len(all_products)} products\n")

# Pattern to match Powertrain section as separate heading
# This matches "Powertrain" or "REFERENCE POWERTRAIN" when it's on its own line
# followed by Engine, Transmission sections
pattern = r'\n\s*(REFERENCE\s+)?Powertrain\s*\n.*'

updated = 0
examples_shown = 0

for product in all_products:
    if not product.description:
        continue
    
    old_desc = product.description
    
    # Remove Powertrain section from end of description
    new_desc = re.sub(pattern, '', old_desc, flags=re.IGNORECASE | re.DOTALL)
    new_desc = new_desc.strip()
    
    if new_desc != old_desc and examples_shown < 10:
        print(f"[{product.id}] {product.title[:60]}...")
        print(f"  Removed: {len(old_desc) - len(new_desc)} characters")
        print(f"  OLD ending: ...{old_desc[-150:].replace(chr(10), ' ')}")
        print(f"  NEW ending: ...{new_desc[-100:].replace(chr(10), ' ')}\n")
        examples_shown += 1
    
    if new_desc != old_desc:
        product.description = new_desc
        updated += 1

print(f"\n[?] Ready to update {updated} products. Commit changes? (showing first 10)")
input("Press ENTER to continue or Ctrl+C to cancel...")

session.commit()
print(f"\n[√] Successfully cleaned {updated} product descriptions!")
print("=" * 70)

session.close()
