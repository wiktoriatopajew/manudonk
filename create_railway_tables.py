"""
Create database tables in Railway PostgreSQL
"""
import os
os.environ['DATABASE_URL'] = 'postgresql://postgres:oqaUYkSoHsdnycMDGTyflRMRBeWQOOdY@caboose.proxy.rlwy.net:54886/railway'

from database.models import Base
from sqlalchemy import create_engine

print("Creating tables in Railway PostgreSQL...")
print(f"Database: {os.environ['DATABASE_URL'][:50]}...")

engine = create_engine(os.environ['DATABASE_URL'])
Base.metadata.create_all(bind=engine)

print("✅ All tables created successfully!")
print("\nTables created:")
print("  - users")
print("  - products")
print("  - orders")
print("  - order_items")
print("  - newsletter")
print("  - verification_codes")
print("  - password_reset_tokens")
print("  - discount_codes")
print("  - email_campaigns")
