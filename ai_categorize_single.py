"""
AI Product Categorization - Single Product Mode
Processes one product at a time for maximum reliability
"""

import os
import time
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from database.models import Product
from google import genai

# Database configuration
DATABASE_URL = "postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway"

# Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'YOUR_API_KEY_HERE')

def categorize_one(title, client):
    """Categorize single product"""
    
    prompt = f"""Categorize this product manual into ONE category: Automobiles, Motorcycles, Trucks, Construction Equipment, Engines, or Other.

Rules:
- Automobiles: Car manuals (BMW, Toyota, Honda Civic, Lexus, Mercedes, Ford, etc.)
- Motorcycles: Motorcycle manuals (Ducati, Yamaha R1, Honda CBR, Kawasaki Ninja, Suzuki GSXR, KTM, etc.)  
- Trucks: Commercial trucks (ISUZU ELF, Hino, Scania, Volvo Truck, etc.)
- Construction Equipment: Heavy machinery (Caterpillar, Komatsu, JCB, Hitachi excavator, etc.)
- Engines: Standalone engine manuals (Ford Engine, Isuzu Engine, etc.)
- Other: Generic automotive books

Product: "{title}"

Reply with ONLY the category name, nothing else."""

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        category = response.text.strip()
        
        # Validate
        valid_categories = ["Automobiles", "Motorcycles", "Trucks", "Construction Equipment", "Engines", "Other"]
        if category in valid_categories:
            return category
        else:
            return "Other"
        
    except Exception as e:
        print(f"    [X] Error: {e}")
        return "Other"

def main():
    print("\n=== AI Product Categorization (Single Mode) ===\n")
    
    # Check API key
    if GEMINI_API_KEY == 'YOUR_API_KEY_HERE':
        print("[X] Set GEMINI_API_KEY first: $env:GEMINI_API_KEY=\"your-key\"")
        return
    
    # Initialize
    client = genai.Client(api_key=GEMINI_API_KEY)
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Get all products
    products = session.query(Product).all()
    print(f"[√] Found {len(products)} products\n")
    
    total_updated = 0
    
    for i, product in enumerate(products, 1):
        print(f"[{i}/{len(products)}] {product.title[:60]}")
        
        # Categorize
        new_category = categorize_one(product.title, client)
        
        if product.category != new_category:
            old = product.category or "None"
            product.category = new_category
            total_updated += 1
            print(f"    {old} → {new_category}")
        else:
            print(f"    ✓ {product.category}")
        
        # Save every 10 products
        if i % 10 == 0:
            session.commit()
            print(f"    [Saved progress: {i}/{len(products)}]\n")
            time.sleep(1)  # Rate limit: 60 RPM
    
    # Final save
    session.commit()
    
    # Statistics
    print(f"\n{'='*60}")
    print(f"[√] DONE! Updated {total_updated} products\n")
    print(f"[FINAL DISTRIBUTION]")
    
    results = session.query(Product.category, func.count(Product.id)).group_by(Product.category).all()
    for category, count in sorted(results, key=lambda x: x[1], reverse=True):
        print(f"  {category:25s}: {count}")
    
    session.close()

if __name__ == "__main__":
    main()
