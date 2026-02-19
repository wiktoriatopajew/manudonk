"""
Migration script to add discount_codes table
Run this once to add discount code functionality
"""
from sqlalchemy import create_engine, inspect, text
from database.models import Base, DiscountCode
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./database/products.db')

def migrate():
    """Add discount_codes table"""
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    inspector = inspect(engine)
    
    # Check if discount_codes table already exists
    if 'discount_codes' in inspector.get_table_names():
        print("✓ discount_codes table already exists")
        return
    
    print("Creating discount_codes table...")
    
    # Create the table
    Base.metadata.create_all(bind=engine, tables=[DiscountCode.__table__])
    
    print("✓ discount_codes table created successfully!")
    
    # Add some example discount codes
    from database.models import get_session
    session = get_session()
    
    try:
        # Welcome discount
        welcome_code = DiscountCode(
            code='WELCOME10',
            type='percentage',
            value=10.0,
            description='Welcome discount - 10% off first purchase',
            max_uses=None,  # Unlimited uses
            active=True,
            created_by='system'
        )
        
        # VIP discount
        vip_code = DiscountCode(
            code='VIP20',
            type='percentage',
            value=20.0,
            description='VIP customers - 20% off',
            max_uses=100,
            active=True,
            created_by='system'
        )
        
        session.add(welcome_code)
        session.add(vip_code)
        session.commit()
        
        print("✓ Example discount codes created:")
        print("  - WELCOME10 (10% off, unlimited uses)")
        print("  - VIP20 (20% off, max 100 uses)")
        
    except Exception as e:
        print(f"Note: Could not create example codes: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    migrate()
