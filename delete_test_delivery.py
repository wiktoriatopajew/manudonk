"""
Delete Test Delivery Product from Railway Database (manualdonkey)
"""
import os

# Railway database URL for manualdonkey
RAILWAY_DB_URL = 'postgresql://postgres:oqaUYkSoHsdnycMDGTyflRMRBeWQOOdY@caboose.proxy.rlwy.net:54886/railway'

os.environ['DATABASE_URL'] = RAILWAY_DB_URL

from database.models import Product, Order
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def delete_test_delivery_product():
    """Delete the test product named 'Delivery'"""
    
    print("="*60)
    print("🗑️  Deleting Test Delivery Product from Railway Database")
    print("="*60)
    
    engine = create_engine(RAILWAY_DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Find product
        product = session.query(Product).filter(Product.title == "Delivery").first()
        
        if not product:
            print("⚠️  Product 'Delivery' not found in database")
            session.close()
            return
        
        print(f"📦 Found product:")
        print(f"   ID: {product.id}")
        print(f"   Title: {product.title}")
        print(f"   Price: ${product.price}")
        print(f"   Category: {product.category}")
        print()
        
        # Find and delete related orders
        related_orders = session.query(Order).filter(Order.product_id == product.id).all()
        if related_orders:
            print(f"🗑️  Deleting {len(related_orders)} related order(s)...")
            for order in related_orders:
                session.delete(order)
            print(f"✅ Deleted {len(related_orders)} order(s)")
        
        # Delete product
        session.delete(product)
        session.commit()
        
        print("✅ Test product 'Delivery' deleted successfully from Railway!")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error deleting test product: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    delete_test_delivery_product()
