"""
Add Test Delivery Product to Railway Database (manualdonkey)
"""
import os

# Railway database URL for manualdonkey
RAILWAY_DB_URL = 'postgresql://postgres:oqaUYkSoHsdnycMDGTyflRMRBeWQOOdY@caboose.proxy.rlwy.net:54886/railway'

os.environ['DATABASE_URL'] = RAILWAY_DB_URL

from database.models import Product
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def add_test_delivery_product():
    """Add a test product named 'Delivery' for 0.50 USD"""
    
    print("="*60)
    print("📦 Adding Test Delivery Product to Railway Database")
    print("="*60)
    
    engine = create_engine(RAILWAY_DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if product already exists
        existing = session.query(Product).filter(Product.title == "Delivery").first()
        
        if existing:
            print(f"⚠️  Product 'Delivery' already exists (ID: {existing.id})")
            print(f"   Updating price to $0.50...")
            existing.price = 0.50
            session.commit()
            print(f"✅ Product updated successfully!")
            print(f"   ID: {existing.id}")
            print(f"   Title: {existing.title}")
            print(f"   Price: ${existing.price}")
            print(f"   Category: {existing.category}")
            session.close()
            return
        
        # Create test product
        product = Product(
            title="Delivery",
            description="Test delivery product for manualdonkey.com",
            price=0.50,
            category="others",
            brand="Test",
            model="Delivery",
            product_type="other",
            slug="test-delivery-product"
        )
        
        session.add(product)
        session.commit()
        
        print("✅ Test product 'Delivery' added successfully to Railway!")
        print(f"   ID: {product.id}")
        print(f"   Title: {product.title}")
        print(f"   Price: ${product.price}")
        print(f"   Category: {product.category}")
        print(f"   Slug: {product.slug}")
        print()
        print(f"🛒 You can now purchase this product at:")
        print(f"   https://manualdonkey.com/manuals/{product.slug}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error adding test product: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    add_test_delivery_product()
