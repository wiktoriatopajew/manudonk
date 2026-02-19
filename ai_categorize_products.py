"""
AI-powered product categorization using Google Gemini
Automatically categorizes products based on their titles
Saves progress to continue after interruption
"""

import os
import time
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Product
from google import genai

# Progress file
PROGRESS_FILE = 'ai_categorization_progress.json'

# Manual Bear database
os.environ['DATABASE_URL'] = 'postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway'

# Configure Gemini API
# Get your free API key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'YOUR_API_KEY_HERE')
client = genai.Client(api_key=GEMINI_API_KEY)

# Available categories
CATEGORIES = [
    "Automobiles",
    "Motorcycles", 
    "Trucks",
    "Construction Equipment",
    "Engines",
    "Other"
]

# Batch size for processing
BATCH_SIZE = 100

BATCH_CATEGORIZATION_PROMPT = """Categorize these products into: Automobiles, Motorcycles, Trucks, Construction Equipment, Engines, or Other.

Rules:
- Automobiles: Cars (BMW, Toyota, Honda Civic, etc.)
- Motorcycles: Bikes (Ducati, CBR, Ninja, etc.)
- Trucks: Commercial trucks (ISUZU ELF, Hino, etc.)
- Engines: Standalone engine manuals
- Other: Generic publications

Return JSON array of categories matching order of products.

Products:
{products_json}
"""

def load_progress():
    """Load processed product IDs from progress file"""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                data = json.load(f)
                return set(data.get('processed_ids', []))
        except:
            return set()
    return set()

def save_progress(processed_ids, category_changes):
    """Save progress to file"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump({
            'processed_ids': list(processed_ids),
            'category_changes': category_changes,
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
        }, f, indent=2)

def categorize_batch_with_ai(products_batch, client) -> dict:
    """Use Gemini to categorize batch"""
    try:
        products_list = [{"id": p.id, "title": p.title} for p in products_batch]
        products_json = json.dumps([p["title"] for p in products_list])
        
        prompt = BATCH_CATEGORIZATION_PROMPT.format(products_json=products_json)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        categories_text = response.text.strip()
        if categories_text.startswith('```'):
            categories_text = categories_text.split('\n', 1)[1].rsplit('\n', 1)[0]
        
        categories = json.loads(categories_text)
        
        result = {}
        for i, product_data in enumerate(products_list):
            if i < len(categories) and categories[i] in CATEGORIES:
                result[product_data["id"]] = categories[i]
            else:
                result[product_data["id"]] = "Other"
        
        return result
        
    except Exception as e:
        print(f"[X] Error: {e}")
        return {p.id: "Other" for p in products_batch}

def main():
    # Check API key
    if GEMINI_API_KEY == 'YOUR_API_KEY_HERE':
        print("[X] Please set GEMINI_API_KEY environment variable")
        print("Get your free API key from: https://makersuite.google.com/app/apikey")
        print("\nOn Windows PowerShell:")
        print('$env:GEMINI_API_KEY="your-api-key-here"')
        return
    
    print("[AI] AI-Powered Product Categorization")
    print(f"[DB] Database: {os.environ['DATABASE_URL'][:50]}...")
    print(f"[AI] Using Google Gemini 2.5 Flash")
    
    # Load previous progress
    processed_ids = load_progress()
    if processed_ids:
        print(f"[>>] Resuming from previous session - {len(processed_ids)} products already processed")
    
    # Initialize Gemini client
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Connect to database
    engine = create_engine(os.environ['DATABASE_URL'])
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Get all products
    products = session.query(Product).all()
    total = len(products)
    
    print(f"\n[>>] Found {total} products")
    print(f"[>>] Processing {BATCH_SIZE} products per batch\n")
    
    updated_count = 0
    skipped_count = len(processed_ids)
    category_changes = {}
    
    # Filter unprocessed
    products_to_process = [p for p in products if p.id not in processed_ids]
    print(f"[>>] {len(products_to_process)} need categorization\n")
    
    # Process in batches
    for batch_start in range(0, len(products_to_process), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(products_to_process))
        batch = products_to_process[batch_start:batch_end]
        
        print(f"[>>] Batch {batch_start//BATCH_SIZE + 1}: {batch_start+1}-{batch_end}/{len(products_to_process)}")
        
        # Get categories
        batch_categories = categorize_batch_with_ai(batch, client)
        
        # Update
        for product in batch:
            old_category = product.category or "None"
            new_category = batch_categories.get(product.id, "Other")
            
            if old_category != new_category:
                product.category = new_category
                updated_count += 1
                
                change_key = f"{old_category} → {new_category}"
                category_changes[change_key] = category_changes.get(change_key, 0) + 1
                
                print(f"  {old_category:20} → {new_category:20} | {product.title[:60]}")
            
            processed_ids.add(product.id)
        
        # Save
        session.commit()
        save_progress(processed_ids, category_changes)
        print(f"  [OK] Saved! {batch_end}/{len(products_to_process)}\n")
        
        # Rate limit
        if batch_end < len(products_to_process):
            time.sleep(4)
    
    # Final commit and save
    session.commit()
    save_progress(processed_ids, category_changes)
    
    print(f"\n[OK] AI Categorization completed!")
    print(f"   Total products: {total}")
    print(f"   Updated: {updated_count} products")
    print(f"   Skipped: {skipped_count} products (already processed)")
    print(f"   Unchanged: {total - updated_count - skipped_count} products")
    
    if category_changes:
        print(f"\n[STATS] Category changes:")
        for change, count in sorted(category_changes.items(), key=lambda x: x[1], reverse=True):
            print(f"   {change}: {count} products")
    
    # Show final distribution
    print(f"\n[STATS] Final category distribution:")
    categories = session.query(Product.category, 
                               session.query(Product).filter(Product.category == Product.category).count()
                               ).group_by(Product.category).all()
    
    from sqlalchemy import func
    category_counts = session.query(
        Product.category,
        func.count(Product.id)
    ).group_by(Product.category).order_by(func.count(Product.id).desc()).all()
    
    for category, count in category_counts:
        print(f"   {category}: {count}")
    
    session.close()

if __name__ == '__main__':
    main()
