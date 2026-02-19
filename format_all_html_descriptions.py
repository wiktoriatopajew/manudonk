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
print("  FORMAT HTML DESCRIPTIONS (ALL CATEGORIES)")
print("=" * 70)

# Get ALL products
products = session.query(Product).all()

print(f"\n[√] Checking {len(products)} products in all categories\n")

updated = 0
examples_shown = 0

for product in products:
    if not product.description:
        continue
    
    # Only process if it contains <p> tag
    if '<p>' not in product.description:
        continue
    
    old_desc = product.description
    new_desc = old_desc
    
    # Remove HTML tags
    new_desc = re.sub(r'<p>|</p>', '', new_desc)
    
    # Decode HTML entities
    new_desc = new_desc.replace('&amp;', '&')
    new_desc = new_desc.replace('&nbsp;', ' ')
    
    # Add line breaks before major sections
    new_desc = re.sub(r'\s+(ENGINE FEATURED IN THIS MANUAL:)', r'\n\n\1', new_desc)
    new_desc = re.sub(r'\s+(WHAT\'S INSIDE \?)', r'\n\n\1', new_desc)
    new_desc = re.sub(r'\s+(TRANSMISSION COVERED BY THIS MANUAL:)', r'\n\n\1', new_desc)
    
    # Add line breaks after sentences (period followed by 2+ spaces)
    new_desc = re.sub(r'\.\s{2,}', '.\n\n', new_desc)
    
    # Clean up multiple spaces
    new_desc = re.sub(r' {2,}', ' ', new_desc)
    
    # Clean up multiple newlines (max 2)
    new_desc = re.sub(r'\n{3,}', '\n\n', new_desc)
    
    new_desc = new_desc.strip()
    
    if new_desc != old_desc:
        if examples_shown < 5:
            print(f"[{product.id}] {product.title[:50]}...")
            print(f"  Category: {product.category}")
            print(f"  OLD length: {len(old_desc)}, NEW length: {len(new_desc)}\n")
            examples_shown += 1
        
        product.description = new_desc
        updated += 1
        
        # Commit every 100 products
        if updated % 100 == 0:
            session.commit()
            print(f"[PROGRESS] Saved {updated} products...")

session.commit()
print(f"\n[√] Successfully formatted {updated} product descriptions!")
print("=" * 70)

session.close()
