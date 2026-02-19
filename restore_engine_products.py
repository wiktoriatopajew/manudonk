"""
Restore ENGINE products to Engines category
EXCEPT specific vehicle models (MINI COOPER, BMW X5, CBR1000RR)
"""
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from database.models import Product

DATABASE_URL = "postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway"

def main():
    print("\n" + "="*70)
    print("  RESTORE ENGINE PRODUCTS TO ENGINES CATEGORY")
    print("="*70 + "\n")
    
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Find products with ENGINE in title but NOT in Engines category
    engine_products = session.query(Product).filter(
        Product.title.ilike('%ENGINE%')
    ).all()
    
    print(f"[√] Found {len(engine_products)} products with ENGINE in title\n")
    
    # Exceptions - keep these in Cars/Motorcycles
    exceptions = [
        'CBR1000RR',
        'MINI COOPER R55/56/57 N12',
        'BMW X5 E70',
        'MINI COOPER S R55/56/57 N14'
    ]
    
    updated = 0
    
    for product in engine_products:
        # Check if this is an exception
        is_exception = False
        for exc in exceptions:
            if exc.replace('/', '').replace(' ', '') in product.title.replace('/', '').replace(' ', ''):
                is_exception = True
                print(f"  [SKIP] {product.title[:60]} (exception - vehicle model)")
                break
        
        if is_exception:
            continue
        
        # Check if already in Engines
        if product.category and product.category.startswith('Engines'):
            continue
        
        # Extract brand from current category or title
        if product.category and '/' in product.category:
            parts = product.category.split('/')
            brand = parts[1] if len(parts) > 1 else 'Generic'
        else:
            # Try to extract from title
            title_upper = product.title.upper()
            brand = 'Generic'
            for possible_brand in ['TOYOTA', 'HONDA', 'MERCEDES', 'FORD', 'ISUZU', 
                                   'MITSUBISHI', 'HYUNDAI', 'PROTON', 'BMW', 'MINI',
                                   'NISSAN', 'MAZDA', 'VOLKSWAGEN', 'AUDI']:
                if possible_brand in title_upper:
                    brand = possible_brand.title()
                    break
        
        old_category = product.category
        new_category = f'Engines/{brand}'
        product.category = new_category
        updated += 1
        
        print(f"  [{product.id}] {product.title[:50]}")
        print(f"         {old_category} → {new_category}")
    
    session.commit()
    
    print("\n" + "="*70)
    print(f"[√] COMPLETE! Restored {updated} products to Engines category")
    print("="*70 + "\n")
    
    session.close()

if __name__ == "__main__":
    main()
