"""
Import products directly to Railway PostgreSQL database
Run this script to populate production database with products from shopify.csv
"""
import os
import sys

# Set DATABASE_URL BEFORE any imports
os.environ['DATABASE_URL'] = 'postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway'

import csv
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, Product
from dotenv import load_dotenv
from datetime import datetime

# Category mapping - simplified to 6 main categories
CATEGORY_MAPPING = {
    'car': 'cars',
    'truck': 'trucks',
    'motorcycle': 'motorcycles',
    'engine': 'engines',
    'construction': 'construction',
    'other': 'other'
}

def normalize_text(text):
    if not text:
        return ""
    text = str(text).strip()
    text = text.replace('â€"', '-').replace('â€™', "'").replace('Â', ' ')
    return text

def extract_brand_from_type(type_str):
    if not type_str or '>' not in type_str:
        return None
    parts = type_str.split('>')
    return normalize_text(parts[-1]) if len(parts) > 1 else None

def extract_brand_model_from_title(title):
    title = normalize_text(title)
    title_clean = title
    for word in ['Full', 'Manual', 'Set', 'Repair', 'Maintenance', 'Service', 'Workshop', 
                 'Guide', 'Owner', 'Handbook', 'Book', 'Online', 'ONLINE', '–', '-']:
        title_clean = title_clean.replace(word, ' ')
    
    words = [w.strip() for w in title_clean.split() if len(w.strip()) > 0]
    if len(words) >= 2:
        brand = words[0].upper()
        model = words[1].upper()
        model = re.sub(r'[^\w-]', '', model)
        
        if len(model) < 2 or model.isdigit():
            if len(words) >= 3:
                model = words[2].upper()
                model = re.sub(r'[^\w-]', '', model)
        
        return brand, model
    elif len(words) == 1:
        word = words[0].upper()
        return word, word
    
    return None, None

def categorize_product(title, type_str):
    """Determine category based on title and type - returns one of 6 categories"""
    title_lower = title.lower()
    type_lower = type_str.lower() if type_str else ""
    
    # Check type field first
    if 'car' in type_lower or 'volkswagen' in type_lower or 'toyota' in type_lower or 'ford' in type_lower:
        return 'cars'
    elif 'motorcycle' in type_lower or 'bike' in type_lower:
        return 'motorcycles'
    elif 'truck' in type_lower:
        return 'trucks'
    
    # Check title - Cars
    if any(word in title_lower for word in ['car', 'auto', 'vehicle', 'vw', 'toyota', 'ford', 'honda', 'bmw', 'audi', 'mercedes', 'nissan', 'mazda', 'lexus', 'volkswagen', 'chevrolet', 'hyundai', 'kia', 'subaru', 'volvo', 'jaguar', 'land rover', 'tesla', 'peugeot', 'renault', 'citroen', 'fiat', 'alfa romeo', 'skoda', 'seat', 'opel', 'vauxhall', 'chrysler', 'dodge', 'jeep', 'ram', 'buick', 'cadillac', 'gmc', 'lincoln', 'acura', 'infiniti', 'pontiac', 'saturn', 'mercury', 'oldsmobile', 'plymouth', 'saab', 'hummer', 'scion', 'smart', 'mini', 'porsche', 'ferrari', 'lamborghini', 'maserati', 'bentley', 'rolls-royce', 'aston martin', 'bugatti', 'mclaren', 'lotus', 'morgan', 'tvr', 'caterham', 'dacia', 'lada', 'tata', 'mahindra', 'proton', 'perodua', 'geely', 'chery', 'byd', 'great wall', 'haval', 'mg', 'rover', 'austin', 'triumph', 'hillman', 'singer', 'sunbeam', 'talbot', 'humber', 'riley', 'wolseley']):
        return 'cars'
    
    # Motorcycles
    elif any(word in title_lower for word in ['motorcycle', 'bike', 'yamaha', 'kawasaki', 'suzuki', 'ducati', 'harley', 'ktm', 'triumph', 'indian', 'victory', 'buell', 'aprilia', 'mv agusta', 'moto guzzi', 'benelli', 'husqvarna', 'beta', 'gas gas', 'sherco', 'ossa', 'montesa', 'bultaco', 'norton', 'bsa', 'royal enfield', 'jawa', 'cz', 'ural']):
        return 'motorcycles'
    
    # Trucks
    elif any(word in title_lower for word in ['truck', 'semi', 'lorry', 'pickup', 'freightliner', 'kenworth', 'peterbilt', 'mack', 'international', 'volvo truck', 'scania', 'man truck', 'iveco', 'daf', 'mercedes truck', 'renault truck']):
        return 'trucks'
    
    # Construction Equipment
    elif any(word in title_lower for word in ['excavator', 'bulldozer', 'loader', 'crane', 'forklift', 'construction', 'bobcat', 'caterpillar', 'komatsu', 'hitachi', 'doosan', 'hyundai construction', 'jcb', 'case construction', 'new holland construction', 'volvo construction', 'liebherr', 'terex', 'kobelco', 'kubota construction', 'yanmar construction']):
        return 'construction'
    
    # Engines
    elif any(word in title_lower for word in ['engine', 'motor', 'cummins', 'caterpillar engine', 'detroit diesel', 'perkins', 'yanmar engine', 'kubota engine', 'kohler', 'briggs', 'tecumseh', 'onan']):
        return 'engines'
    
    # Everything else goes to other
    else:
        return 'other'

def create_slug(brand, model):
    text = f"{brand}-{model}".lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def extract_year_from_title(title):
    year_pattern = r'20[0-2O][0-9O]'
    matches = re.findall(year_pattern, title)
    if matches:
        year = matches[0].replace('O', '0')
        return year
    return None

print("Connecting to Railway PostgreSQL...")
DATABASE_URL = os.environ['DATABASE_URL']
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

csv_file = "shopify.csv"

if not os.path.exists(csv_file):
    print(f"❌ File not found: {csv_file}")
    sys.exit(1)

print(f"🚀 Importing products to Railway from {csv_file}...")
print("=" * 60)

stats = {
    'total_rows': 0,
    'products_imported': 0,
    'products_skipped': 0,
    'categories_created': set(),
    'brands': set()
}

try:
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        current_handle = None
        
        for row in reader:
            stats['total_rows'] += 1
            
            if not row.get('Title') or row['Title'].strip() == '':
                continue
            
            handle = row['Handle']
            
            if handle and handle != current_handle:
                current_handle = handle
                
                title = normalize_text(row['Title'])
                price = float(row['Variant Price']) if row.get('Variant Price') else 29.99
                description = normalize_text(row.get('Body (HTML)', ''))[:500]
                type_field = row.get('Type', '')
                image_url = row.get('Image Src', '')
                
                if len(title) < 5:
                    stats['products_skipped'] += 1
                    continue
                
                brand_from_type = extract_brand_from_type(type_field)
                brand_from_title, model_from_title = extract_brand_model_from_title(title)
                
                brand = brand_from_type if brand_from_type else brand_from_title
                model = model_from_title if model_from_title else 'MANUAL'
                
                if not brand:
                    words = title.split()
                    brand = words[0].upper() if words else 'UNKNOWN'
                
                if not model or len(model) < 2:
                    model = handle.split('-')[0].upper()[:50]
                
                if not brand or len(brand) < 2:
                    stats['products_skipped'] += 1
                    continue
                
                category_name = categorize_product(title, type_field)
                stats['categories_created'].add(category_name)
                stats['brands'].add(brand)
                
                year = extract_year_from_title(title)
                
                slug_base = create_slug(brand, model)
                slug = slug_base
                
                if year:
                    slug = f"{slug_base}-{year}"
                
                counter = 1
                original_slug = slug
                while session.query(Product).filter(Product.slug == slug).first():
                    slug = f"{original_slug}-{counter}"
                    counter += 1
                    if counter > 20:
                        break
                
                product = Product(
                    title=title[:200],
                    brand=brand[:50],
                    model=model[:50],
                    year=int(year) if year and year.isdigit() else None,
                    description=description,
                    price=price,
                    category=category_name,
                    slug=slug,
                    image_url=image_url if image_url else None,
                    pdf_url=None
                )
                
                try:
                    session.add(product)
                    session.commit()
                    stats['products_imported'] += 1
                    if stats['products_imported'] % 100 == 0:
                        print(f"✅ Imported {stats['products_imported']} products...")
                except Exception as e:
                    session.rollback()
                    print(f"❌ Error: {str(e)[:100]}")
                    stats['products_skipped'] += 1
                    continue

    print(f"\n{'='*60}")
    print(f"📊 IMPORT SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Products imported: {stats['products_imported']}")
    print(f"⏭️  Products skipped: {stats['products_skipped']}")
    print(f"📁 Categories created: {len(stats['categories_created'])}")
    print(f"🏷️  Brands found: {len(stats['brands'])}")
    print(f"{'='*60}\n")
    print("✅ Import to Railway completed successfully!")
    print("Your products are now live!")
    
except Exception as e:
    print(f"❌ Critical error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
