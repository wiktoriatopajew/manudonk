"""
Import products to Manual Bear Railway Database
Uses NEW Manual Bear database credentials
"""
import os
import sys

# Set DATABASE_URL BEFORE any imports
os.environ['DATABASE_URL'] = 'postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway'

import csv
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
from database.models import Base, Product
import re

def extract_brand_model_from_title(title):
    """Extract brand and model from product title"""
    # Common brand patterns
    brands = [
        'Toyota', 'Honda', 'Ford', 'Chevrolet', 'Nissan', 'BMW', 'Mercedes', 'Audi',
        'Volkswagen', 'Mazda', 'Hyundai', 'Kia', 'Subaru', 'Lexus', 'Jeep', 'Dodge',
        'RAM', 'GMC', 'Cadillac', 'Chrysler', 'Buick', 'Acura', 'Infiniti', 'Volvo',
        'Porsche', 'Land Rover', 'Jaguar', 'Mini', 'Fiat', 'Alfa Romeo', 'Maserati',
        'Tesla', 'Mitsubishi', 'Suzuki', 'Isuzu', 'Peugeot', 'Renault', 'Citroen',
        'Skoda', 'Seat', 'Opel', 'Saab', 'Pontiac', 'Mercury', 'Oldsmobile', 'Saturn',
        'Hummer', 'Lincoln', 'Genesis', 'Yamaha', 'Kawasaki', 'Harley-Davidson',
        'Ducati', 'Triumph', 'KTM', 'Husqvarna', 'Beta', 'Sherco', 'GasGas',
        'Caterpillar', 'John Deere', 'Bobcat', 'Case', 'New Holland', 'Kubota',
        'Massey Ferguson', 'Claas', 'Fendt', 'Deutz', 'Fahr', 'McCormick', 'Valtra',
        'JCB', 'Komatsu', 'Hitachi', 'Volvo CE', 'Liebherr', 'Terex', 'Doosan',
        'Hyundai Heavy', 'Kobelco', 'Sumitomo', 'Samsung', 'Daewoo', 'SANY', 'XCMG',
        'Zoomlion', 'LiuGong', 'Lonking', 'SDLG', 'Shantui', 'Yanmar', 'Iseki',
        'Hinomoto', 'Shibaura', 'Mitsubishi Agricultural', 'Mahindra', 'Farmtrac',
        'LS Tractor', 'TYM', 'Branson', 'Kioti', 'Yanmar Marine', 'Mercury Marine',
        'Suzuki Marine', 'Honda Marine', 'Yamaha Marine', 'Tohatsu', 'Evinrude',
        'Johnson', 'Mariner', 'Force', 'Selva', 'Parsun', 'Polaris', 'Arctic Cat',
        'Ski-Doo', 'Sea-Doo', 'Can-Am', 'BRP', 'Aprilia', 'MV Agusta', 'Royal Enfield',
        'Indian', 'Victory', 'Ural', 'Buell', 'Erik Buell Racing', 'Norton',
        'BSA', 'Bimota', 'Benelli', 'Moto Guzzi', 'Laverda', 'Cagiva', 'Husaberg'
    ]
    
    title_upper = title.upper()
    brand = None
    
    # Try to find brand in title
    for b in brands:
        if b.upper() in title_upper:
            brand = b
            break
    
    # If no brand found, try to extract first word
    if not brand:
        words = title.split()
        if words:
            brand = words[0]
    
    # Extract model (everything after brand)
    if brand:
        # Find brand position and take rest as model
        brand_pos = title_upper.find(brand.upper())
        if brand_pos != -1:
            rest = title[brand_pos + len(brand):].strip()
            # Clean up model name
            model = re.sub(r'^[-\s:]+', '', rest)
            # Take first few words as model, limit to 50 chars
            model_words = model.split()[:3]
            model = ' '.join(model_words)
            # Truncate model to 50 chars max
            if len(model) > 50:
                model = model[:50].strip()
        else:
            model = title.replace(brand, '').strip()[:50]
    else:
        model = title[:50]
    
    return brand or 'Unknown', model or title[:50]

def categorize_product(product_type, title):
    """Categorize product based on type and title with improved logic"""
    if not product_type:
        product_type = ""
    
    type_upper = product_type.upper()
    title_upper = title.upper()
    
    # PRIORITY 1: Technical publications and manuals (goes to Other)
    technical_keywords = ['HOW TO', 'DESIGNING', 'TUNING', 'CYLINDER HEAD', 'PORT AND FLOW', 'SA161', 'SA268', 'HANDBOOK', 'GUIDE TO']
    if any(keyword in title_upper for keyword in technical_keywords):
        return 'Other'
    
    # PRIORITY 2: Construction Equipment (Komatsu, Caterpillar, etc) - BEFORE checking engines
    construction_brands = ['KOMATSU', 'CATERPILLAR', 'CAT ', 'BOBCAT', 'CASE', 'JCB', 'HITACHI', 'VOLVO CE', 'LIEBHERR', 'DOOSAN', 'HYUNDAI HEAVY']
    construction_keywords = ['EXCAVATOR', 'BULLDOZER', 'LOADER', 'CRANE', 'FORKLIFT', 'DIGGER', 'BACKHOE', 'SKID STEER', 'PC200', 'PC210', 'PC220', 'PC250']
    if any(brand in title_upper for brand in construction_brands) or any(keyword in type_upper for keyword in construction_keywords) or any(keyword in title_upper for keyword in construction_keywords):
        return 'Construction Equipment'
    
    # PRIORITY 3: Engines (must start with ENGINE or brand ENGINE)
    # e.g., "FORD ENGINE DURATORQ", "HINO ENGINE EH700", "TOYOTA ENGINE 2NR-VE", "MERCEDES-BENZ ENGINE M103"
    if title_upper.startswith('ENGINE') or \
       re.match(r'^[A-Z\-]+\s+ENGINE\b', title_upper) or \
       re.match(r'^[A-Z\-]+\s+BENZ\s+ENGINE\b', title_upper) or \
       'ENGINE WORKSHOP' in title_upper[:50] or \
       'ENGINE DURATORQ' in title_upper or \
       'ENGINE EH' in title_upper or \
       'ENGINE D4D' in title_upper or \
       'ENGINE DURATEC' in title_upper:
        return 'Engines'
    
    # PRIORITY 4: Check if it's a CAR/VEHICLE manual that mentions ENGINE
    # If title starts with car brand/model, it's a CAR manual (even if ENGINE mentioned later)
    car_brands_start = ['TOYOTA', 'HONDA', 'FORD', 'CHEVROLET', 'NISSAN', 'BMW', 'MERCEDES', 'AUDI', 
                        'VOLKSWAGEN', 'VW', 'MAZDA', 'HYUNDAI', 'KIA', 'LEXUS', 'MINI', 'FIAT', 
                        'PEUGEOT', 'RENAULT', 'CITROEN', 'OPEL', 'SKODA', 'SEAT', 'SUZUKI',
                        'MITSUBISHI', 'SUBARU', 'JEEP', 'DODGE', 'RAM', 'GMC', 'CADILLAC']
    if any(title_upper.startswith(brand.upper()) for brand in car_brands_start):
        # Check if it's actually a motorcycle or truck
        if 'MOTORCYCLE' not in title_upper and 'BIKE' not in title_upper and 'TRUCK' not in title_upper:
            # It's a car manual (even if mentions ENGINE, N12, M271 etc)
            return 'Automobiles'
    
    # PRIORITY 4: Motorcycles (specific bike models)
    moto_keywords = ['MOTORCYCLE', 'MOTORBIKE', 'BIKE', 'SCOOTER', 'MOPED', 'ATV', 'QUAD', 'DIRT BIKE', 'SPORT BIKE']
    # Suzuki motorcycles vs cars
    if 'SUZUKI' in title_upper:
        suzuki_cars = ['GRAND VITARA', 'JIMNY', 'SWIFT', 'VITARA', 'SX4', 'BALENO', 'IGNIS', 'CELERIO']
        if any(car in title_upper for car in suzuki_cars):
            return 'Automobiles'
        # If not a car model, assume motorcycle for Suzuki
        if any(keyword in title_upper for keyword in moto_keywords) or 'SUZUKI' in title_upper:
            # Check if it's explicitly a car
            if 'CAR' not in title_upper and 'AUTO' not in title_upper and 'SUV' not in title_upper:
                # Default Suzuki to motorcycles unless it's a known car
                pass  # Will check other motorcycle keywords below
    
    if any(keyword in type_upper for keyword in moto_keywords) or any(keyword in title_upper for keyword in moto_keywords):
        return 'Motorcycles'
    
    # PRIORITY 5: Trucks
    truck_keywords = ['TRUCK', 'PICKUP', 'VAN', 'LORRY', 'SEMI', 'FREIGHT']
    if any(keyword in type_upper for keyword in truck_keywords) or any(keyword in title_upper for keyword in truck_keywords):
        return 'Trucks'
    
    # PRIORITY 6: Tractors
    tractor_keywords = ['TRACTOR', 'COMBINE', 'HARVESTER']
    if any(keyword in type_upper for keyword in tractor_keywords) or any(keyword in title_upper for keyword in tractor_keywords):
        return 'Tractors'
    
    # PRIORITY 7: Marine
    marine_keywords = ['BOAT', 'MARINE', 'SHIP', 'YACHT', 'OUTBOARD', 'WATERCRAFT', 'JET SKI', 'JETSKI']
    if any(keyword in type_upper for keyword in marine_keywords) or any(keyword in title_upper for keyword in marine_keywords):
        return 'Marine'
    
    # PRIORITY 8: Automobiles (default for car brands)
    car_keywords = ['CAR', 'AUTO', 'SEDAN', 'COUPE', 'HATCHBACK', 'WAGON', 'SUV', 'CROSSOVER', 'VEHICLE']
    car_brands = ['TOYOTA', 'HONDA', 'FORD', 'CHEVROLET', 'NISSAN', 'BMW', 'MERCEDES', 'AUDI', 'VOLKSWAGEN', 'MAZDA', 'HYUNDAI', 'KIA']
    if any(keyword in type_upper for keyword in car_keywords) or any(keyword in title_upper for keyword in car_keywords):
        return 'Automobiles'
    # Check car brands but EXCLUDE if it's "BRAND ENGINE" pattern
    for brand in car_brands:
        if brand in title_upper:
            # If it's "FORD ENGINE" or "TOYOTA ENGINE", skip (it's an engine manual)
            if not re.search(rf'\b{brand}\s+ENGINE\b', title_upper):
                return 'Automobiles'
    
    # Default
    return 'Other'

def create_slug(brand, model, year=None):
    """Create URL-friendly slug from brand, model, and year (max 95 chars for counters)"""
    # Combine brand, model, and year
    if year:
        slug_text = f"{brand} {model} {year}"
    else:
        slug_text = f"{brand} {model}"
    
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = slug_text.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    slug = slug.strip('-')
    
    # Truncate to 95 characters to leave room for counter suffix (-1, -2, etc.)
    if len(slug) > 95:
        slug = slug[:95].rstrip('-')
    
    return slug

def extract_year_from_title(title):
    """Extract year from title if present"""
    # Look for 4-digit year between 1900 and 2030
    years = re.findall(r'\b(19\d{2}|20[0-3]\d)\b', title)
    if years:
        return int(years[0])
    return None

def import_products():
    """Import products from shopify.csv to Manual Bear Railway database"""
    print("🐻 Importing products to Manual Bear Railway from shopify.csv...")
    print(f"📦 Database: {os.environ['DATABASE_URL'][:50]}...")
    
    # Create engine and session
    engine = create_engine(os.environ['DATABASE_URL'])
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create tables if they don't exist
    print("📊 Creating tables...")
    Base.metadata.create_all(engine)
    
    # Read CSV
    csv_path = 'shopify.csv'
    if not os.path.exists(csv_path):
        print(f"❌ Error: {csv_path} not found!")
        return
    
    print(f"📂 Reading {csv_path}...")
    
    products_data = {}
    
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            handle = row['Handle']
            image_src = row['Image Src']
            
            # If this is an image row (Handle is empty), add image to existing product
            if not handle and image_src:
                # Find the last product handle we processed
                if products_data:
                    last_handle = list(products_data.keys())[-1]
                    if 'images' in products_data[last_handle]:
                        products_data[last_handle]['images'].append(image_src)
                continue
            
            # Skip if no handle
            if not handle:
                continue
            
            # If this product doesn't exist yet, create it
            if handle not in products_data:
                title = row['Title']
                body = row['Body (HTML)']
                vendor = row['Vendor']
                product_type = row['Type']
                price_str = row['Variant Price']
                
                # Parse price
                try:
                    price = float(price_str) if price_str else 19.99
                except:
                    price = 19.99
                
                # Extract brand and model
                brand, model = extract_brand_model_from_title(title)
                
                # Extract year
                year = extract_year_from_title(title)
                
                # Categorize
                category = categorize_product(product_type, title)
                
                # Create slug
                slug = create_slug(brand, model, year)
                
                products_data[handle] = {
                    'title': title,
                    'description': body or f"Professional service manual for {title}",
                    'brand': brand,
                    'model': model,
                    'year': year,
                    'category': category,
                    'slug': slug,
                    'images': [image_src] if image_src else [],
                    'price': price
                }
            else:
                # If product exists and has a new image, add it
                if image_src and image_src not in products_data[handle]['images']:
                    products_data[handle]['images'].append(image_src)
    
    print(f"📊 Found {len(products_data)} unique products")
    
    # Check for existing slugs in database
    existing_slugs = {}
    for slug_obj in session.query(Product.slug).all():
        slug = slug_obj[0]
        if slug in existing_slugs:
            existing_slugs[slug] += 1
        else:
            existing_slugs[slug] = 1
    
    print(f"📊 Found {len(existing_slugs)} existing slugs in database")
    
    # Import products
    added = 0
    skipped = 0
    
    for handle, data in products_data.items():
        # Check if product already exists by slug
        slug = data['slug']
        
        # Handle duplicate slugs
        if slug in existing_slugs:
            counter = existing_slugs[slug]
            original_slug = slug
            slug = f"{original_slug}-{counter}"
            existing_slugs[original_slug] += 1
        else:
            existing_slugs[slug] = 1
        
        data['slug'] = slug
        
        # Check if product exists
        existing = session.query(Product).filter_by(slug=slug).first()
        
        if existing:
            skipped += 1
            continue
        
        # Combine images into comma-separated string
        image_url = ', '.join(data['images']) if data['images'] else '/static/images/placeholder.jpg'
        
        # Create product
        product = Product(
            title=data['title'],
            description=data['description'],
            brand=data['brand'],
            model=data['model'],
            year=data['year'],
            category=data['category'],
            slug=data['slug'],
            image_url=image_url,
            price=data['price']
        )
        
        session.add(product)
        added += 1
        
        if added % 100 == 0:
            print(f"  ✅ Imported {added} products...")
            session.commit()
    
    # Final commit
    session.commit()
    
    print(f"\n✅ Import to Manual Bear completed successfully!")
    print(f"   Added: {added} products")
    print(f"   Skipped: {skipped} products (already existed)")
    
    # Show category breakdown
    print(f"\n📊 Category breakdown:")
    category_counts = session.query(
        Product.category,
        func.count(Product.id)
    ).group_by(Product.category).all()
    
    for category, count in sorted(category_counts, key=lambda x: x[1], reverse=True):
        print(f"   {category}: {count}")
    
    session.close()

if __name__ == '__main__':
    try:
        import_products()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
