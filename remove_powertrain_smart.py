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
print("  REMOVE POWERTRAIN ENGINE/TRANSMISSION LIST")
print("=" * 70)

# Pattern to match Powertrain section with Engine and Transmission lists
# This will match from "Powertrain" through all the engine/transmission specs
# but stop before any normal descriptive text
pattern = r'''
    (REFERENCE\s+)?Powertrain\s*\n      # "Powertrain" or "REFERENCE Powertrain"
    .*?                                  # Any content
    Engine\s*\n                          # "Engine" heading
    .*?                                  # Any content (Petrol/Diesel lists)
    Transmission\s*\n                    # "Transmission" heading
    (?:.*?\n)*?                          # Transmission list items
    (?:                                  # Stop at:
        (?=\n\s*[A-Z][a-z]{10,})|       #   - Long word (start of description)
        (?=\n\s*$)|                      #   - Empty line followed by text
        $                                #   - End of string
    )
'''

all_products = session.query(Product).all()
print(f"\n[√] Checking {len(all_products)} products\n")

updated = 0
examples_shown = 0

for product in all_products:
    if not product.description:
        continue
    
    old_desc = product.description
    
    # Remove Powertrain/Engine/Transmission section
    new_desc = re.sub(pattern, '', old_desc, flags=re.IGNORECASE | re.VERBOSE | re.DOTALL)
    
    # Also try simpler pattern if above didn't work
    if new_desc == old_desc:
        # Match "Powertrain" followed by lines starting with specific keywords
        simple_pattern = r'\n\s*(REFERENCE\s+)?Powertrain.*?(?=\n\s*[A-Z][a-z]{20,}|\Z)'
        new_desc = re.sub(simple_pattern, '', old_desc, flags=re.IGNORECASE | re.DOTALL)
    
    new_desc = new_desc.strip()
    
    if new_desc != old_desc and examples_shown < 10:
        print(f"[{product.id}] {product.title[:60]}...")
        print(f"  Removed: {len(old_desc) - len(new_desc)} characters")
        examples_shown += 1
    
    if new_desc != old_desc:
        product.description = new_desc
        updated += 1

print(f"\n[√] Ready to update {updated} products")
print("Committing changes...")

session.commit()
print(f"\n[√] Successfully cleaned {updated} product descriptions!")
print("=" * 70)

session.close()
