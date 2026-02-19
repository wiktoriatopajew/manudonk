"""
Add Test BMW Product to Railway Database
"""
import os
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set DATABASE_URL BEFORE any imports
os.environ['DATABASE_URL'] = 'postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway'

from database.models import Product

def slugify(text):
    """Simple slugify function"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def add_test_bmw_railway():
    """Add test BMW product for $0.10 to Railway"""
    
    print("🚀 Connecting to Railway database...")
    engine = create_engine(os.environ['DATABASE_URL'])
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Create test product
        product = Product(
            title="BMW TEST - Full Manual Set",
            brand="BMW",
            model="TEST",
            category="Cars > BMW",
            description="Test product for BMW manual. Digital download PDF format.",
            price=0.10,
            pdf_url="https://example.com/test.pdf",
            image_url="https://manualbear.com/static/images/logo.png",
            slug=slugify("BMW TEST Full Manual Set"),
            year=2024,
            product_type="vehicles"
        )
        
        session.add(product)
        session.commit()
        
        print("✅ Test BMW product created successfully on Railway!")
        print(f"   ID: {product.id}")
        print(f"   Title: {product.title}")
        print(f"   Price: ${product.price}")
        print(f"   Slug: {product.slug}")
        print(f"   URL: https://manualbear.com/manuals/{product.slug}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error creating product: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    add_test_bmw_railway()
