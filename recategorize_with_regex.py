"""
Regex-based product recategorization - ACCURATE & FAST
Fixes AI errors, properly categorizes based on title patterns
"""

import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Product

# Database connection
DATABASE_URL = "postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway"

# Categories
CATEGORIES = [
    "Automobiles",
    "Motorcycles",
    "Trucks",
    "Construction Equipment",
    "Engines",
    "Other"
]

def categorize_product(title):
    """Categorize product based on title using regex patterns"""
    title_upper = title.upper()
    
    # 1. ENGINES - specific engine manuals
    engine_patterns = [
        r'ENGINE\s+(SERVICE|REPAIR|WORKSHOP|MANUAL)',
        r'(ECOBLUE|ECOBOOST|POWERSTROKE|DURAMAX|CUMMINS)',
        r'^\w+\s+ENGINE\s+',  # "FORD ENGINE", "ISUZU ENGINE"
    ]
    for pattern in engine_patterns:
        if re.search(pattern, title_upper):
            return "Engines"
    
    # 2. CONSTRUCTION EQUIPMENT - brands
    construction_brands = [
        'CATERPILLAR', 'CAT ', 'KOMATSU', 'HITACHI', 'VOLVO CE',
        'JOHN DEERE', 'JCB', 'CASE', 'BOBCAT', 'DOOSAN',
        'EXCAVATOR', 'LOADER', 'BULLDOZER', 'BACKHOE'
    ]
    for brand in construction_brands:
        if brand in title_upper:
            return "Construction Equipment"
    
    # 3. TRUCKS - specific truck models and brands
    truck_patterns = [
        r'\b(ISUZU\s+(ELF|NPR|NKR|NHR|DMAX|MU-X|FORWARD|GIGA))',
        r'\b(HINO|FUSO|UD TRUCK|SCANIA)',
        r'\b(FORD\s+(F-?150|F-?250|F-?350|RANGER|SUPER DUTY))',
        r'\b(CHEVROLET\s+(SILVERADO|COLORADO))',
        r'\b(RAM\s+\d{4})',
        r'\bTRUCK\b',
    ]
    for pattern in truck_patterns:
        if re.search(pattern, title_upper):
            return "Trucks"
    
    # 4. MOTORCYCLES - brands and models
    motorcycle_brands = [
        # Pure motorcycle brands
        'DUCATI', 'KTM', 'TRIUMPH', 'HUSQVARNA', 'APRILIA',
        'MV AGUSTA', 'BENELLI', 'ROYAL ENFIELD',
        
        # Motorcycle models (multi-brand)
        r'\bCBR\d+', r'\bCB\d+R', r'\bCB\d+F', r'\bCBF\d+',
        r'\bNINJA\b', r'\bZ\d+', r'\bVERSYS\b', r'\bVULCAN\b',
        r'\bYZF-?R\d+', r'\bMT-?\d+', r'\bTENERE\b', r'\bFZ\d+',
        r'\bGSX-?R\d+', r'\bGSX-?S\d+', r'\bV-?STROM\b', r'\bHAYABUSA\b',
        r'\bFJR\d+', r'\bXMAX\b', r'\bNMAX\b', r'\bAEROX\b',
        
        # Honda/Yamaha/Suzuki/Kawasaki motorcycles
        'PCX', 'FORZA', 'SCOOPY', 'BEAT', 'VARIO', 'WAVE', 'SONIC',
        'SUPER CUB', 'GROM', 'MSX', 'NSR', 'CBX', 'VFR', 'VTR',
        'MAJESTY', 'MIO', 'SOUL', 'VIXION', 'R15', 'R25',
        'BURGMAN', 'ADDRESS', 'BANDIT', 'KATANA', 'INTRUDER',
        'NINJA', 'KLX', 'D-TRACKER', 'ESTRELLA',
        
        # BMW motorcycles (R, S, K, F series)
        r'\bBMW\s+[RSKF]\s*\d+',
    ]
    
    for pattern in motorcycle_brands:
        if isinstance(pattern, str):
            if pattern in title_upper:
                return "Motorcycles"
        else:  # regex pattern
            if re.search(pattern, title_upper):
                return "Motorcycles"
    
    # 5. AUTOMOBILES - car brands (excluding already matched)
    automobile_brands = [
        'TOYOTA', 'HONDA', 'NISSAN', 'MAZDA', 'MITSUBISHI', 'SUBARU',
        'LEXUS', 'INFINITI', 'ACURA',
        'BMW', 'MERCEDES', 'AUDI', 'VOLKSWAGEN', 'VW ', 'PORSCHE',
        'FORD', 'CHEVROLET', 'CHEVY', 'DODGE', 'CHRYSLER', 'JEEP',
        'HYUNDAI', 'KIA', 'GENESIS',
        'VOLVO', 'SAAB', 'PEUGEOT', 'CITROEN', 'RENAULT',
        'FIAT', 'ALFA ROMEO', 'LANCIA',
        'JAGUAR', 'LAND ROVER', 'RANGE ROVER',
        'TESLA', 'RIVIAN', 'LUCID',
        'PERODUA', 'PROTON', 'DAIHATSU',
        
        # Car model patterns
        'CAMRY', 'COROLLA', 'PRIUS', 'RAV4', 'HIGHLANDER', '4RUNNER',
        'CIVIC', 'ACCORD', 'CR-V', 'HR-V', 'PILOT',
        'SENTRA', 'ALTIMA', 'MAXIMA', 'ROGUE', 'PATHFINDER',
        'MAZDA3', 'MAZDA6', 'CX-3', 'CX-5', 'CX-9',
        'LANCER', 'PAJERO', 'OUTLANDER', 'TRITON',
        'IMPREZA', 'LEGACY', 'OUTBACK', 'FORESTER', 'XV', 'CROSSTREK', 'WRX',
        'MUSTANG', 'FUSION', 'ESCAPE', 'EXPLORER', 'EXPEDITION',
        'MALIBU', 'IMPALA', 'EQUINOX', 'TAHOE', 'SUBURBAN',
        'ELANTRA', 'SONATA', 'TUCSON', 'SANTA FE',
        'OPTIMA', 'SORENTO', 'SPORTAGE', 'TELLURIDE',
        'GOLF', 'JETTA', 'PASSAT', 'TIGUAN', 'TOUAREG',
        'MODEL S', 'MODEL 3', 'MODEL X', 'MODEL Y', 'ROADSTER',
    ]
    
    for brand in automobile_brands:
        if brand in title_upper:
            return "Automobiles"
    
    # 6. OTHER - publications, guides, training materials WITHOUT vehicle brands
    other_patterns = [
        r'\b(GUIDE|MANUAL|HANDBOOK|TRAINING|TECHNICIAN)\b.*\b(AUTOMOTIVE|VEHICLE|DIESEL|GASOLINE)',
        r'\bELECTRIC\s+AND\s+HYBRID\s+VEHICLES\b',
        r'\bAUTO\s+BODY\s+REPAIR\b',
        r'\bENGINE\s+(BLUEPRINTING|BUILDING|REBUILDING|PERFORMANCE)\b',
        r'\bSUPERCHARGED\b',
        r'\bFOUR-WHEELER',
        r'\bTRANSMISSION\s+(REBUILD|REPAIR)',
    ]
    
    # Only categorize as Other if no vehicle brand detected
    has_vehicle_brand = False
    all_brands = automobile_brands + motorcycle_brands + construction_brands
    for brand in all_brands:
        if isinstance(brand, str) and brand in title_upper:
            has_vehicle_brand = True
            break
    
    if not has_vehicle_brand:
        for pattern in other_patterns:
            if re.search(pattern, title_upper):
                return "Other"
    
    # Default fallback
    return "Automobiles"

def main():
    print("[REGEX] Regex-based Product Recategorization")
    print(f"[DB] Database: {DATABASE_URL[:50]}...")
    
    # Connect to database
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Get all products
        products = session.query(Product).all()
        print(f"\n[>>] Found {len(products)} products")
        
        # Categorize each product
        changes = 0
        for i, product in enumerate(products, 1):
            old_category = product.category
            new_category = categorize_product(product.title)
            
            if old_category != new_category:
                product.category = new_category
                changes += 1
                print(f"  {old_category:20s} → {new_category:20s} | {product.title[:60]}")
            
            if i % 100 == 0:
                print(f"[>>] Processed {i}/{len(products)}")
        
        # Commit changes
        session.commit()
        print(f"\n[OK] Updated {changes} products")
        
        # Show final distribution
        from sqlalchemy import func
        results = session.query(Product.category, func.count(Product.id)).group_by(Product.category).all()
        print("\n[FINAL DISTRIBUTION]")
        for category, count in sorted(results, key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count}")
        
    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()
