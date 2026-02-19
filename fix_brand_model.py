"""
Fix Brand and Model fields
Extract correct brand from category and model from title
"""
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Product

DATABASE_URL = "postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway"

def extract_model_from_title(title, brand):
    """Extract model name from title by removing brand and common words"""
    # Remove brand from title
    title_clean = title.upper().replace(brand.upper(), '').strip()
    
    # Remove common words
    remove_words = ['FULL', 'MANUAL', 'SET', 'SERVICE', 'REPAIR', 'WORKSHOP', 
                    'MAINTENANCE', 'ELECTRICAL', 'WIRING', 'DIAGRAMS', 'OWNER',
                    'OWNERS', 'GUIDE', 'HANDBOOK', 'INSTRUCTIONS']
    
    for word in remove_words:
        title_clean = re.sub(r'\b' + word + r'\b', '', title_clean, flags=re.IGNORECASE)
    
    # Remove special characters and multiple spaces
    title_clean = re.sub(r'[–—\-]+', ' ', title_clean)
    title_clean = re.sub(r'\s+', ' ', title_clean).strip()
    
    # Take first meaningful part (before year or special markers)
    parts = title_clean.split()
    model_parts = []
    for part in parts:
        # Stop at year (4 digits)
        if re.match(r'^\d{4}$', part):
            break
        # Stop at special markers
        if part in ['–', '—', '-']:
            break
        model_parts.append(part)
        # Limit to 5 words
        if len(model_parts) >= 5:
            break
    
    return ' '.join(model_parts).strip() or 'UNKNOWN'

def main():
    print("\n" + "="*70)
    print("  FIX BRAND AND MODEL FIELDS")
    print("="*70 + "\n")
    
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Get all products with categories
    products = session.query(Product).filter(Product.category.isnot(None)).all()
    
    print(f"[√] Found {len(products)} products\n")
    
    updated = 0
    batch_size = 100
    
    for i, product in enumerate(products, 1):
        if i % batch_size == 0:
            print(f"[PROGRESS] Processed {i}/{len(products)}...")
        
        # Extract brand from category (second part after /)
        if product.category and '/' in product.category:
            parts = product.category.split('/')
            correct_brand = parts[1] if len(parts) > 1 else parts[0]
        else:
            correct_brand = product.category or 'UNKNOWN'
        
        # Extract model from title
        correct_model = extract_model_from_title(product.title, correct_brand)
        
        # Update if different
        if product.brand != correct_brand or product.model != correct_model:
            old_brand = product.brand
            old_model = product.model
            
            product.brand = correct_brand
            product.model = correct_model
            updated += 1
            
            # Show first 10 changes
            if updated <= 10:
                print(f"  [{product.id}] {product.title[:50]}")
                print(f"         Brand: {old_brand} → {correct_brand}")
                print(f"         Model: {old_model} → {correct_model}\n")
        
        # Commit in batches
        if i % batch_size == 0:
            session.commit()
    
    # Final commit
    session.commit()
    
    print("\n" + "="*70)
    print(f"[√] COMPLETE! Updated {updated} products")
    print("="*70 + "\n")
    
    session.close()

if __name__ == "__main__":
    main()
