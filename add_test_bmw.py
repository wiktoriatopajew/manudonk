"""
Add Test BMW Product
"""
from database.models import Product, get_session
from slugify import slugify

def add_test_bmw():
    """Add test BMW product for $0.10"""
    
    session = get_session()
    try:
        # Create test product
        product = Product(
            title="BMW TEST - Full Manual Set",
            brand="BMW",
            model="TEST",
            category="Cars > BMW",
            description="Test product for BMW manual. Digital download PDF format.",
            price=0.10,
            pdf_link="https://example.com/test.pdf",
            image_url="https://manualbear.com/static/images/logo.png",
            slug=slugify("BMW TEST Full Manual Set"),
            year="2024",
            manual_type="Full Manual Set"
        )
        
        session.add(product)
        session.commit()
        
        print("✅ Test BMW product created successfully!")
        print(f"   ID: {product.id}")
        print(f"   Title: {product.title}")
        print(f"   Price: ${product.price}")
        print(f"   Slug: {product.slug}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error creating product: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    add_test_bmw()
