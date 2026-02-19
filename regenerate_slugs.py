"""
Regenerate product slugs based on corrected brand and model
"""
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Product

DATABASE_URL = "postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway"

def generate_slug(brand, model, year=None):
    """Generate URL-friendly slug from brand, model and year"""
    # Combine brand and model
    text = f"{brand} {model}"
    if year:
        text += f" {year}"
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters
    text = re.sub(r'[^\w\s-]', '', text)
    
    # Replace spaces with hyphens
    text = re.sub(r'[\s_]+', '-', text)
    
    # Remove multiple hyphens
    text = re.sub(r'-+', '-', text)
    
    # Trim hyphens from ends
    text = text.strip('-')
    
    # Limit length
    if len(text) > 100:
        text = text[:100].rsplit('-', 1)[0]
    
    return text

def main():
    print("\n" + "="*70)
    print("  REGENERATE PRODUCT SLUGS")
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
        
        # Generate new slug
        new_slug = generate_slug(product.brand, product.model, product.year)
        
        # Make slug unique if needed
        base_slug = new_slug
        counter = 1
        while session.query(Product).filter(Product.slug == new_slug, Product.id != product.id).first():
            new_slug = f"{base_slug}-{counter}"
            counter += 1
        
        if product.slug != new_slug:
            old_slug = product.slug
            product.slug = new_slug
            updated += 1
            
            # Show first 10 changes
            if updated <= 10:
                print(f"  [{product.id}] {old_slug} → {new_slug}")
        
        # Commit in batches
        if i % batch_size == 0:
            session.commit()
    
    # Final commit
    session.commit()
    
    print("\n" + "="*70)
    print(f"[√] COMPLETE! Updated {updated} slugs")
    print("="*70 + "\n")
    
    session.close()

if __name__ == "__main__":
    main()
