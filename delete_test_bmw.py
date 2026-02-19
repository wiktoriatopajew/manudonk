"""
Delete Test BMW Product from Railway Database
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set DATABASE_URL BEFORE any imports
os.environ['DATABASE_URL'] = 'postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway'

from database.models import Product, Order

def delete_test_bmw():
    """Delete test BMW product (ID: 4782) and related orders"""
    
    print("🚀 Connecting to Railway database...")
    engine = create_engine(os.environ['DATABASE_URL'])
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Find the test product
        product = session.query(Product).filter(Product.slug == 'bmw-test-full-manual-set').first()
        
        if product:
            print(f"🗑️  Deleting test product:")
            print(f"   ID: {product.id}")
            print(f"   Title: {product.title}")
            print(f"   Slug: {product.slug}")
            
            # First delete related orders
            orders = session.query(Order).filter(Order.product_id == product.id).all()
            if orders:
                print(f"   Found {len(orders)} related orders - deleting them first...")
                for order in orders:
                    session.delete(order)
                print(f"   ✅ Deleted {len(orders)} orders")
            
            # Now delete the product
            session.delete(product)
            session.commit()
            
            print("✅ Test BMW product deleted successfully from Railway!")
        else:
            print("⚠️  Test BMW product not found")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error deleting product: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    delete_test_bmw()
