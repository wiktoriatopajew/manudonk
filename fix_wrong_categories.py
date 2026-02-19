"""
Fix wrong categories - recategorize based on title analysis
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Product

DATABASE_URL = "postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway"

# Motorcycle brands
MOTORCYCLE_BRANDS = [
    'HONDA', 'YAMAHA', 'KAWASAKI', 'SUZUKI', 'HARLEY', 'DUCATI', 'BMW', 'KTM', 
    'TRIUMPH', 'APRILIA', 'MV AGUSTA', 'BENELLI', 'ROYAL ENFIELD', 'CFMOTO',
    'ZONTES', 'MODENAS', 'NAZA', 'SYM', 'MOTO GUZZI'
]

# Car brands (comprehensive list)
CAR_BRANDS = [
    'AUDI', 'BMW', 'MERCEDES', 'VOLKSWAGEN', 'TOYOTA', 'HONDA', 'NISSAN',
    'FORD', 'CHEVROLET', 'CADILLAC', 'BUICK', 'GMC', 'DODGE', 'CHRYSLER',
    'JEEP', 'RAM', 'LEXUS', 'INFINITI', 'ACURA', 'MAZDA', 'MITSUBISHI',
    'SUBARU', 'HYUNDAI', 'KIA', 'GENESIS', 'VOLVO', 'SAAB', 'FIAT',
    'ALFA ROMEO', 'FERRARI', 'LAMBORGHINI', 'MASERATI', 'PORSCHE',
    'BENTLEY', 'ROLLS ROYCE', 'ASTON MARTIN', 'JAGUAR', 'LAND ROVER',
    'RANGE ROVER', 'MINI', 'SMART', 'TESLA', 'PEUGEOT', 'RENAULT',
    'CITROEN', 'OPEL', 'SKODA', 'SEAT', 'DACIA', 'BYD', 'GEELY',
    'CHERY', 'HAVAL', 'MG', 'PROTON', 'PERODUA', 'DAIHATSU', 'ISUZU',
    'SSANGYONG', 'NAZA', 'LOTUS', 'MCLAREN', 'KOENIGSEGG', 'PAGANI'
]

def detect_category(title):
    """Detect if product is car, motorcycle, truck, or engine based on title"""
    title_upper = title.upper()
    
    # Check for engine keywords
    engine_keywords = ['ENGINE', 'MOTOR', 'DURATORQ', 'DURAMAX', 'ECOTEC', 
                       'POWERTRAIN', 'HINO', 'CUMMINS', 'DIESEL']
    
    # Check for motorcycle keywords
    moto_keywords = ['CBR', 'YZF', 'R1', 'R6', 'NINJA', 'ZX', 'GSX', 
                     'FIREBLADE', 'SUPERSPORT', 'SPORTBIKE', 'MOTORCYCLE',
                     'BIKE', 'SCOOTER', 'MOTO']
    
    # Check for truck keywords
    truck_keywords = ['TRUCK', 'F-150', 'F-250', 'F-350', 'SILVERADO', 
                      'RAM 1500', 'TUNDRA', 'TACOMA', 'RANGER', 'COLORADO',
                      'HILUX', 'TRITON', 'NAVARA', 'D-MAX']
    
    # First check brand
    for brand in MOTORCYCLE_BRANDS:
        if brand in title_upper:
            # Check if it's really a motorcycle
            for keyword in moto_keywords:
                if keyword in title_upper:
                    return f'Motorcycles/{brand.title()}'
            # Check for BMW motorcycles specifically
            if brand == 'BMW' and any(k in title_upper for k in ['R1200', 'R1250', 'F800', 'F850', 'S1000RR', 'K1600']):
                return f'Motorcycles/BMW'
    
    # Check for engine-specific products
    if any(kw in title_upper for kw in engine_keywords) and 'MANUAL SET' not in title_upper:
        for brand in CAR_BRANDS:
            if brand in title_upper:
                return f'Engines/{brand.title()}'
        return 'Engines/Generic'
    
    # Check for trucks
    if any(kw in title_upper for kw in truck_keywords):
        for brand in CAR_BRANDS:
            if brand in title_upper:
                return f'Trucks/{brand.title()}'
    
    # Default to Cars
    for brand in CAR_BRANDS:
        if brand in title_upper:
            return f'Cars/{brand.title()}'
    
    return None

def main():
    print("\n" + "="*70)
    print("  FIX WRONG CATEGORIES")
    print("="*70 + "\n")
    
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Get products with problematic categories
    wrong_cats = []
    
    # 1. Cars/motorcycles in Engines category
    engines = session.query(Product).filter(Product.category.like('Engines%')).all()
    print(f"[1] Checking {len(engines)} products in Engines...")
    for p in engines:
        new_cat = detect_category(p.title)
        if new_cat and not new_cat.startswith('Engines'):
            wrong_cats.append((p, new_cat))
            print(f"  [{p.id}] {p.title[:50]} → {new_cat}")
    
    # 2. Products in "Automobiles" category
    autos = session.query(Product).filter(Product.category == 'Automobiles').all()
    print(f"\n[2] Checking {len(autos)} products in Automobiles...")
    for p in autos:
        new_cat = detect_category(p.title)
        if new_cat:
            wrong_cats.append((p, new_cat))
            print(f"  [{p.id}] {p.title[:50]} → {new_cat}")
    
    # Apply fixes
    print(f"\n[√] Fixing {len(wrong_cats)} products...")
    for product, new_category in wrong_cats:
        product.category = new_category
    
    session.commit()
    
    print("\n" + "="*70)
    print(f"[√] COMPLETE! Fixed {len(wrong_cats)} categories")
    print("="*70 + "\n")
    
    session.close()

if __name__ == "__main__":
    main()
