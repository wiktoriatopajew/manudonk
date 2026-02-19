"""
AI Product Categorization - Batch 100
Simple and effective categorization using Google Gemini
"""

import os
import time
import json
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from database.models import Product
from google import genai

# Database configuration
DATABASE_URL = "postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway"

# Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'YOUR_API_KEY_HERE')

# Categories
CATEGORIES = ["Automobiles", "Motorcycles", "Trucks", "Construction Equipment", "Engines", "Other"]

def categorize_batch(titles, client):
    """Categorize batch of 100 products"""
    
    prompt = f"""Categorize these products into: Automobiles, Motorcycles, Trucks, Construction Equipment, Engines, or Other.

Rules:
- Automobiles: Car manuals (BMW, Toyota, Honda Civic, Lexus, etc.)
- Motorcycles: Motorcycle manuals (Ducati, Yamaha R1, Honda CBR, Kawasaki Ninja, etc.)
- Trucks: Commercial trucks (ISUZU ELF, Hino, Scania, etc.)
- Construction Equipment: Heavy machinery (Caterpillar, Komatsu, JCB, etc.)
- Engines: Standalone engine manuals
- Other: Generic automotive books and training materials

Return ONLY a JSON array with categories in the same order as products.

Products:
{json.dumps(titles, indent=2)}

Response (JSON array only):"""

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        # Parse response
        result = response.text.strip()
        
        # Remove markdown code blocks if present
        if result.startswith('```'):
            lines = result.split('\n')
            result = '\n'.join(lines[1:-1]) if len(lines) > 2 else result
            if result.startswith('json'):
                result = result[4:].strip()
        
        categories = json.loads(result)
        
        # Validate
        if len(categories) != len(titles):
            print(f"  [!] Length mismatch: {len(categories)} != {len(titles)}, using Other")
            return ["Other"] * len(titles)
        
        return categories
        
    except Exception as e:
        print(f"  [X] Error: {e}")
        return ["Other"] * len(titles)

def main():
    print("\n=== AI Product Categorization (Batch 100) ===\n")
    
    # Check API key
    if GEMINI_API_KEY == 'YOUR_API_KEY_HERE':
        print("[X] Set GEMINI_API_KEY environment variable first!")
        print("    $env:GEMINI_API_KEY=\"your-key-here\"")
        return
    
    # Initialize
    client = genai.Client(api_key=GEMINI_API_KEY)
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Get all products
    products = session.query(Product).all()
    print(f"[√] Found {len(products)} products")
    
    # Process in batches of 100
    batch_size = 100
    total_updated = 0
    
    for i in range(0, len(products), batch_size):
        batch = products[i:i+batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(products) + batch_size - 1) // batch_size
        
        print(f"\n[>>] Batch {batch_num}/{total_batches} ({len(batch)} products)")
        
        # Get titles
        titles = [p.title for p in batch]
        
        # Categorize with AI
        print(f"  [AI] Asking Gemini...")
        categories = categorize_batch(titles, client)
        
        # Update database
        updated = 0
        for product, new_category in zip(batch, categories):
            if product.category != new_category:
                old = product.category or "None"
                product.category = new_category
                updated += 1
                print(f"    {old:20s} → {new_category:20s} | {product.title[:50]}")
        
        if updated == 0:
            print(f"  [√] No changes needed")
        else:
            print(f"  [√] Updated {updated} products")
        
        total_updated += updated
        
        # Commit this batch
        session.commit()
        print(f"  [√] Saved to database")
        
        # Rate limiting - wait 4 seconds between batches (15 RPM)
        if i + batch_size < len(products):
            print(f"  [~] Waiting 4 seconds (rate limit)...")
            time.sleep(4)
    
    # Final statistics
    print(f"\n{'='*60}")
    print(f"[√] DONE! Updated {total_updated} products")
    print(f"\n[FINAL DISTRIBUTION]")
    
    results = session.query(Product.category, func.count(Product.id)).group_by(Product.category).all()
    for category, count in sorted(results, key=lambda x: x[1], reverse=True):
        print(f"  {category:25s}: {count}")
    
    session.close()

if __name__ == "__main__":
    main()
