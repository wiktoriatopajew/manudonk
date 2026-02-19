"""
Recategorize existing products in Manual Bear database
Updates categories without reimporting CSV
"""
import os
import re

# Set DATABASE_URL BEFORE any imports
os.environ['DATABASE_URL'] = 'postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway'

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Product

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
    # e.g., "FORD ENGINE DURATORQ", "HINO ENGINE EH700", "TOYOTA ENGINE 2NR-VE"
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

def recategorize_all():
    """Recategorize all products in database"""
    print("🐻 Recategorizing products in Manual Bear Railway database...")
    print(f"📦 Database: {os.environ['DATABASE_URL'][:50]}...")
    
    # Create engine and session
    engine = create_engine(os.environ['DATABASE_URL'])
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Get all products
    products = session.query(Product).all()
    print(f"📊 Found {len(products)} products to recategorize")
    
    changes = {}
    updated_count = 0
    
    for product in products:
        # Get new category
        new_category = categorize_product(product.product_type, product.title)
        
        # Track changes
        if product.category != new_category:
            old_cat = product.category
            if old_cat not in changes:
                changes[old_cat] = {}
            if new_category not in changes[old_cat]:
                changes[old_cat][new_category] = []
            
            changes[old_cat][new_category].append(product.title[:80])
            
            # Update category
            product.category = new_category
            updated_count += 1
            
            if updated_count % 50 == 0:
                print(f"  ✅ Updated {updated_count} products...")
    
    # Commit changes
    session.commit()
    
    print(f"\n✅ Recategorization completed!")
    print(f"   Updated: {updated_count} products")
    print(f"   Unchanged: {len(products) - updated_count} products")
    
    if changes:
        print(f"\n📊 Category Changes:")
        for old_cat, new_cats in changes.items():
            print(f"\n  FROM: {old_cat}")
            for new_cat, titles in new_cats.items():
                print(f"    TO: {new_cat} ({len(titles)} products)")
                # Show first 3 examples
                for title in titles[:3]:
                    print(f"       - {title}")
    
    # Show final category breakdown
    print(f"\n📊 Final Category Distribution:")
    from sqlalchemy import func
    category_counts = session.query(
        Product.category,
        func.count(Product.id)
    ).group_by(Product.category).all()
    
    for category, count in sorted(category_counts, key=lambda x: x[1], reverse=True):
        print(f"   {category}: {count}")
    
    session.close()

if __name__ == '__main__':
    try:
        recategorize_all()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
