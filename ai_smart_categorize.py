"""
AI Smart Product Categorization - Hierarchical Categories
Automatically categorizes products into proper hierarchical categories:
- Motorcycles/Honda, Motorcycles/Yamaha, etc.
- Engines/Toyota, Engines/Honda, etc.
- Automobiles/BMW, Automobiles/Toyota, etc.
- Construction/Caterpillar, Construction/Komatsu, etc.

Processes 100 products at a time
"""

import os
import time
import json
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from database.models import Product
import requests

# Database configuration
DATABASE_URL = "postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway"

# Google Gemini API
GEMINI_API_KEY = "AIzaSyC0qASA_biZle6ZQlLnG9S_U6NLSDYrNIc"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"

def categorize_batch_with_gemini(products_data):
    """
    Categorize batch of products using Google Gemini API
    Returns list of hierarchical categories
    """
    
    # Build product list for prompt
    product_list = []
    for idx, p in enumerate(products_data, 1):
        product_list.append(f"{idx}. {p['title']}")
    
    prompt = f"""Categorize these products using EXACTLY 3 levels: Home/MainCategory/Brand

MAIN CATEGORIES:
1. Cars - All car/automobile manuals
2. Motorcycles - All motorcycle manuals
3. Engines - Standalone engine manuals  
4. Trucks - Commercial trucks
5. Construction - Heavy machinery
6. Marine - Boats, marine engines
7. Agriculture - Tractors, farm equipment

FORMAT RULES - CRITICAL:
✓ CORRECT: "Home/Cars/BMW" "Home/Motorcycles/Honda" "Home/Engines/Toyota"
✗ WRONG: "Home/Cars/Aston Martin/ASTON" - NO 4th level!
✗ WRONG: "Home/Cars/BMW/X5" - NO model names!
✗ WRONG: "Cars/BMW" - MUST start with "Home/"!
✗ WRONG: "Other" or "Generic" - ALWAYS use real brand!

EXAMPLES:
- "ASTON MARTIN DB11" → "Home/Cars/Aston Martin"
- "ALFA ROMEO 145-146" → "Home/Cars/Alfa Romeo"
- "CBR1000RR HONDA" → "Home/Motorcycles/Honda"
- "4AGE TOYOTA ENGINE" → "Home/Engines/Toyota"
- "APRILIA CAPONORD 1200" → "Home/Motorcycles/Aprilia"
- "BMW 3 SERIES E46" → "Home/Cars/BMW"
- "YAMAHA R1" → "Home/Motorcycles/Yamaha"

STRICT RULES:
- Use EXACTLY 3 levels: Home/MainCategory/Brand
- ALWAYS start with "Home/"
- Extract brand name from title (Aston Martin, Alfa Romeo, BMW, Honda, etc.)
- NO 4th level, NO model names, NO extra slashes
- Brand names: proper capitalization (Aston Martin not ASTON MARTIN)

Products to categorize:
{chr(10).join(product_list)}

Return ONLY JSON array with {len(products_data)} categories:
["Home/Motorcycles/Honda", "Home/Cars/Toyota", ...]"""

    try:
        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 16384,
                }
            },
            timeout=120
        )
        
        if response.status_code != 200:
            print(f"  [!] API Error: {response.status_code}")
            print(f"  [!] Response: {response.text[:200]}")
            # Return error - don't categorize on API failure
            return None
        
        result = response.json()
        
        # Extract text from response
        if 'candidates' in result and len(result['candidates']) > 0:
            text = result['candidates'][0]['content']['parts'][0]['text']
            
            # Clean markdown
            text = text.strip()
            if text.startswith('```'):
                lines = text.split('\n')
                text = '\n'.join(lines[1:-1]) if len(lines) > 2 else text
                if text.startswith('json'):
                    text = text[4:].strip()
            
            # Parse JSON
            categories = json.loads(text)
            
            # Validate
            if len(categories) == len(products_data):
                # Fix categories with wrong format
                validated_categories = []
                for idx, cat in enumerate(categories):
                    # Count slashes
                    slash_count = cat.count('/')
                    
                    if slash_count == 2 and cat.startswith('Home/'):
                        # Perfect format: Home/MainCategory/Brand
                        validated_categories.append(cat)
                    elif slash_count > 2 and cat.startswith('Home/'):
                        # Too many levels like "Home/Cars/Aston Martin/ASTON"
                        # Extract first 3 levels only
                        parts = cat.split('/')
                        fixed = f"{parts[0]}/{parts[1]}/{parts[2]}"
                        print(f"  [FIX] '{cat}' → '{fixed}'")
                        validated_categories.append(fixed)
                    elif not cat.startswith('Home/'):
                        # Missing Home/ - add it
                        parts = cat.split('/')
                        if len(parts) >= 2:
                            fixed = f"Home/{parts[0]}/{parts[1]}"
                            print(f"  [FIX] '{cat}' → '{fixed}'")
                            validated_categories.append(fixed)
                        else:
                            print(f"  [!] Invalid '{cat}' for: {products_data[idx]['title'][:50]}")
                            validated_categories.append("Home/Cars/Unknown")
                    else:
                        # Other problem - use fallback
                        print(f"  [!] Invalid '{cat}' for: {products_data[idx]['title'][:50]}")
                        validated_categories.append("Home/Cars/Unknown")
                return validated_categories
            else:
                print(f"  [!] Length mismatch: got {len(categories)}, expected {len(products_data)}")
                return None
        else:
            print(f"  [!] Unexpected response format")
            return None
            
    except Exception as e:
        print(f"  [X] Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("\n" + "="*70)
    print("  AI SMART PRODUCT CATEGORIZATION - HIERARCHICAL CATEGORIES")
    print("="*70 + "\n")
    
    # Initialize database
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Get all products
    products = session.query(Product).order_by(Product.id).all()
    print(f"[√] Found {len(products)} products in database\n")
    
    # Process in batches of 50 (more stable)
    batch_size = 50
    total_updated = 0
    total_batches = (len(products) + batch_size - 1) // batch_size
    
    for i in range(0, len(products), batch_size):
        batch = products[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        
        print(f"\n{'='*70}")
        print(f"BATCH {batch_num}/{total_batches} - Processing {len(batch)} products")
        print(f"{'='*70}")
        
        # Prepare data for AI
        products_data = [{'id': p.id, 'title': p.title, 'old_category': p.category} for p in batch]
        
        # Call Gemini API
        print(f"[AI] Calling Google Gemini API...")
        categories = categorize_batch_with_gemini(products_data)
        
        # Check if categorization failed
        if categories is None:
            print(f"  [X] Batch failed - skipping and continuing...")
            continue
        
        # Update database
        # Update database
        updated_count = 0
        for product, new_category in zip(batch, categories):
            old_category = product.category or "None"
            
            if old_category != new_category:
                product.category = new_category
                updated_count += 1
                
                # Show changes
                old_display = old_category[:30].ljust(30)
                new_display = new_category[:30].ljust(30)
                title_display = product.title[:50] if len(product.title) <= 50 else product.title[:47] + "..."
                
                print(f"  [{product.id:5d}] {old_display} → {new_display} | {title_display}")
        
        if updated_count == 0:
            print(f"  [√] No changes needed in this batch")
        else:
            print(f"\n  [√] Updated {updated_count} products in this batch")
        
        total_updated += updated_count
        
        # Commit batch
        session.commit()
        print(f"  [√] Changes saved to database")
        
        # Rate limiting - wait between batches (except last batch)
        if i + batch_size < len(products):
            wait_time = 2
            print(f"  [⏳] Waiting {wait_time} seconds before next batch...")
            time.sleep(wait_time)
    
    # Final statistics
    print("\n" + "="*70)
    print("  CATEGORIZATION COMPLETE!")
    print("="*70)
    print(f"\n[√] Total products updated: {total_updated}")
    print(f"[√] Total products unchanged: {len(products) - total_updated}")
    
    # Show distribution
    print(f"\n{'='*70}")
    print("  CATEGORY DISTRIBUTION")
    print(f"{'='*70}\n")
    
    results = session.query(
        Product.category, 
        func.count(Product.id)
    ).group_by(Product.category).order_by(func.count(Product.id).desc()).all()
    
    for category, count in results:
        category_display = category or "None"
        print(f"  {category_display:40s} : {count:5d} products")
    
    print(f"\n{'='*70}\n")
    
    session.close()
    print("[√] Done!\n")

if __name__ == "__main__":
    main()
