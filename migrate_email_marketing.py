"""
Migration script for email marketing system
Adds EmailCampaign, EmailTracking, AbandonedCart tables
and updates Newsletter table with new fields
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, inspect, text
from database.models import Base, Newsletter, EmailCampaign, EmailTracking, AbandonedCart

DATABASE_URL = "sqlite:///./database/products.db"

def migrate():
    """Run migration"""
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    inspector = inspect(engine)
    
    # Check if new tables exist
    existing_tables = inspector.get_table_names()
    
    print("🔄 Starting email marketing migration...")
    
    # Create new tables
    if 'email_campaigns' not in existing_tables:
        EmailCampaign.__table__.create(engine)
        print("✅ Created email_campaigns table")
    else:
        print("⏭️  email_campaigns table already exists")
    
    if 'email_tracking' not in existing_tables:
        EmailTracking.__table__.create(engine)
        print("✅ Created email_tracking table")
    else:
        print("⏭️  email_tracking table already exists")
    
    if 'abandoned_carts' not in existing_tables:
        AbandonedCart.__table__.create(engine)
        print("✅ Created abandoned_carts table")
    else:
        print("⏭️  abandoned_carts table already exists")
    
    # Update newsletter table with new columns
    newsletter_columns = [col['name'] for col in inspector.get_columns('newsletter')]
    
    with engine.connect() as conn:
        if 'has_purchased' not in newsletter_columns:
            conn.execute(text("ALTER TABLE newsletter ADD COLUMN has_purchased BOOLEAN DEFAULT 0"))
            conn.commit()
            print("✅ Added has_purchased column to newsletter")
        
        if 'last_reminder_sent' not in newsletter_columns:
            conn.execute(text("ALTER TABLE newsletter ADD COLUMN last_reminder_sent DATETIME"))
            conn.commit()
            print("✅ Added last_reminder_sent column to newsletter")
    
    print("✅ Migration completed successfully!")

if __name__ == "__main__":
    migrate()
