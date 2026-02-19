"""
Professional Shopify CSV Product Importer
Automatically creates categories and brands, imports products with proper organization
"""
import csv
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, Product
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Database connection - use SQLite for import
DATABASE_URL = "sqlite:///./database/products.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
session = Session()

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
    """Remove special characters and normalize text"""
    if not text:
        return ""
    text = str(text).strip()
    # Remove HTML entities
    text = text.replace('â€"', '-').replace('â€™', "'").replace('Â', ' ')
    return text

def extract_brand_from_type(type_str):
    """Extract brand from Type field (e.g., 'Car>Toyota' -> 'Toyota')"""
    if not type_str or '>' not in type_str:
        return None
    parts = type_str.split('>')
    return normalize_text(parts[-1]) if len(parts) > 1 else None

def extract_brand_model_from_title(title):
    """
    Extract brand and model from title
    Examples:
    'VW ATLAS 2O17-2024 Full Manual Set' -> brand='VW', model='ATLAS'
    'TOYOTA HIGHLANDER / KLUGER HYBRID 2020+' -> brand='TOYOTA', model='HIGHLANDER'
    """
    title = normalize_text(title)
    
    # Remove common words that aren't brand/model
    title_clean = title
    for word in ['Full', 'Manual', 'Set', 'Repair', 'Maintenance', 'Service', 'Workshop', 
                 'Guide', 'Owner', 'Handbook', 'Book', 'Online', 'ONLINE', '–', '-']:
        title_clean = title_clean.replace(word, ' ')
    
    # Common patterns
    words = [w.strip() for w in title_clean.split() if len(w.strip()) > 0]
    if len(words) >= 2:
        brand = words[0].upper()
        # Take second word, but clean it
        model = words[1].upper()
        
        # Clean model from special chars but keep alphanumeric and dash
        model = re.sub(r'[^\w-]', '', model)
        
        # If model is too short or looks like a year, try next word
        if len(model) < 2 or model.isdigit():
            if len(words) >= 3:
                model = words[2].upper()
                model = re.sub(r'[^\w-]', '', model)
        
        return brand, model
    elif len(words) == 1:
        # Single word title - use as both brand and model
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
    """Create URL-friendly slug"""
    text = f"{brand}-{model}".lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def get_or_create_category(category_name):
    """Just return category name - using simple string approach"""
    return category_name

def extract_year_from_title(title):
    """Extract year or year range from title"""
    # Look for patterns like 2020, 2017-2024, 2O17-2024 (with O instead of 0)
    year_pattern = r'20[0-2O][0-9O]'
    matches = re.findall(year_pattern, title)
    if matches:
        # Clean up (replace O with 0)
        year = matches[0].replace('O', '0')
        return year
    return None

def import_shopify_csv(csv_file):
    """Import products from Shopify CSV"""
    print(f"\n{'='*60}")
    print(f"🚀 PROFESSIONAL SHOPIFY PRODUCT IMPORTER")
    print(f"{'='*60}\n")
    
    # Track statistics
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
            current_product_data = None
            
            for row in reader:
                stats['total_rows'] += 1
                
                # Skip rows without title (image rows)
                if not row.get('Title') or row['Title'].strip() == '':
                    continue
                
                handle = row['Handle']
                
                # If this is a new product (not an image row)
                if handle and handle != current_handle:
                    current_handle = handle
                    
                    title = normalize_text(row['Title'])
                    price = float(row['Variant Price']) if row.get('Variant Price') else 29.99
                    description = normalize_text(row.get('Body (HTML)', ''))[:500]  # Limit description
                    type_field = row.get('Type', '')
                    image_url = row.get('Image Src', '')
                    
                    # Skip if title is too short
                    if len(title) < 5:
                        stats['products_skipped'] += 1
                        continue
                    
                    # Extract information
                    brand_from_type = extract_brand_from_type(type_field)
                    brand_from_title, model_from_title = extract_brand_model_from_title(title)
                    
                    # Prefer brand from type field if available
                    brand = brand_from_type if brand_from_type else brand_from_title
                    model = model_from_title if model_from_title else 'MANUAL'
                    
                    # Fallback: if still no brand, use first word of title
                    if not brand:
                        words = title.split()
                        brand = words[0].upper() if words else 'UNKNOWN'
                    
                    if not model or len(model) < 2:
                        # Use handle as model
                        model = handle.split('-')[0].upper()[:50]
                    
                    if not brand or len(brand) < 2:
                        print(f"⚠️  Skipping: {title[:50]}... (invalid brand)")
                        stats['products_skipped'] += 1
                        continue
                    
                    # Determine category
                    category_name = categorize_product(title, type_field)
                    stats['categories_created'].add(category_name)
                    stats['brands'].add(brand)
                    
                    # Extract year
                    year = extract_year_from_title(title)
                    
                    # Create slug - make it more unique
                    slug_base = create_slug(brand, model)
                    slug = slug_base
                    
                    # Add year if available to make it more unique
                    if year:
                        slug = f"{slug_base}-{year}"
                    
                    # Check if slug exists and make it unique by adding counter
                    counter = 1
                    original_slug = slug
                    while session.query(Product).filter(Product.slug == slug).first():
                        slug = f"{original_slug}-{counter}"
                        counter += 1
                        if counter > 20:  # Safety break
                            break
                    
                    # Create product
                    product = Product(
                        title=title[:200],  # Limit title length
                        brand=brand[:50],
                        model=model[:50],
                        year=int(year) if year and year.isdigit() else None,
                        description=description,
                        price=price,
                        category=category_name,  # Using string instead of ForeignKey
                        slug=slug,
                        image_url=image_url if image_url else None,
                        pdf_url=None  # To be added later
                    )
                    
                    try:
                        session.add(product)
                        session.commit()
                        stats['products_imported'] += 1
                        print(f"✅ Imported: {brand} {model} → {category_name} (${price})")
                    except Exception as e:
                        session.rollback()
                        print(f"❌ Error importing {title[:50]}: {str(e)}")
                        stats['products_skipped'] += 1
                        continue
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"📊 IMPORT SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Products imported: {stats['products_imported']}")
        print(f"⏭️  Products skipped: {stats['products_skipped']}")
        print(f"📁 Categories created: {len(stats['categories_created'])}")
        print(f"🏷️  Brands found: {len(stats['brands'])}")
        print(f"\n📂 Categories:")
        for cat in sorted(stats['categories_created']):
            count = session.query(Product).filter(Product.category == cat).count()
            print(f"   • {cat}: {count} products")
        print(f"\n🏢 Top Brands:")
        for brand in sorted(stats['brands'])[:20]:
            count = session.query(Product).filter(Product.brand == brand).count()
            print(f"   • {brand}: {count} products")
        print(f"{'='*60}\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Critical error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    csv_file = "shopify.csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ File not found: {csv_file}")
        exit(1)
    
    print("Starting import...")
    success = import_shopify_csv(csv_file)
    
    if success:
        print("✅ Import completed successfully!")
    else:
        print("❌ Import failed!")
