"""
Clean product descriptions - remove PEN DRIVE and REFERENCE POWERTRAIN sections
"""
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Product

DATABASE_URL = "postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway"

def clean_description(desc):
    """Remove PEN DRIVE mentions and REFERENCE POWERTRAIN sections"""
    if not desc:
        return desc
    
    original = desc
    
    # Remove PEN DRIVE related phrases (case insensitive)
    patterns_to_remove = [
        r'\s*AND PEN DRIVE SHIPPED\.?',
        r'\s*AND USB DRIVE SHIPPED\.?',
        r'\s*PEN DRIVE SHIPPED\.?',
        r'\s*USB DRIVE SHIPPED\.?',
        r'\s*\(PEN DRIVE SHIPPED\)\.?',
        r'\s*\(USB DRIVE SHIPPED\)\.?',
        r'AVAILABLE AS DOWNLOADABLE LINK AND PEN DRIVE SHIPPED',
        r'DOWNLOADABLE LINK AND PEN DRIVE',
        r'DOWNLOADABLE PDF AND PEN DRIVE',
    ]
    
    for pattern in patterns_to_remove:
        desc = re.sub(pattern, '', desc, flags=re.IGNORECASE)
    
    # Remove REFERENCE POWERTRAIN section and everything after it until next section or end
    # Pattern: Find "REFERENCE POWERTRAIN" and remove everything until we hit a new section (all caps heading) or double newline
    desc = re.sub(
        r'REFERENCE POWERTRAIN.*?(?=\n\n[A-Z]{3,}|\Z)',
        '',
        desc,
        flags=re.IGNORECASE | re.DOTALL
    )
    
    # Also try alternative patterns for REFERENCE POWERTRAIN
    desc = re.sub(
        r'REFERENCE POWERTRAIN:.*?(?=\n\n|\Z)',
        '',
        desc,
        flags=re.IGNORECASE | re.DOTALL
    )
    
    # Clean up multiple spaces and newlines
    desc = re.sub(r'\n\n\n+', '\n\n', desc)
    desc = re.sub(r'  +', ' ', desc)
    desc = desc.strip()
    
    return desc

def main():
    print("\n" + "="*70)
    print("  CLEAN PRODUCT DESCRIPTIONS")
    print("="*70 + "\n")
    
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    products = session.query(Product).all()
    
    print(f"[√] Found {len(products)} products\n")
    
    updated = 0
    batch_size = 100
    
    for i, product in enumerate(products, 1):
        if i % batch_size == 0:
            print(f"[PROGRESS] Processed {i}/{len(products)}...")
        
        if not product.description:
            continue
        
        cleaned = clean_description(product.description)
        
        if cleaned != product.description:
            # Show first 10 changes
            if updated < 10:
                print(f"\n[{product.id}] {product.title[:60]}")
                print(f"  OLD: {product.description[:100]}...")
                print(f"  NEW: {cleaned[:100]}...")
            
            product.description = cleaned
            updated += 1
        
        # Commit in batches
        if i % batch_size == 0:
            session.commit()
    
    # Final commit
    session.commit()
    
    print("\n" + "="*70)
    print(f"[√] COMPLETE! Cleaned {updated} descriptions")
    print("="*70 + "\n")
    
    session.close()

if __name__ == "__main__":
    main()
