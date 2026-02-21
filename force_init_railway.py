"""
Force initialize Railway database - ignoring cache
"""
import os

# Set Railway URL BEFORE importing anything
os.environ['DATABASE_URL'] = 'postgresql://postgres:oqaUYkSoHsdnycMDGTyflRMRBeWQOOdY@caboose.proxy.rlwy.net:54886/railway'

from database.models import Base
from sqlalchemy import create_engine

def force_init_railway():
    """Create all tables in Railway database"""
    DATABASE_URL = os.environ['DATABASE_URL']
    print(f"Connecting to: {DATABASE_URL[:50]}...")
    
    engine = create_engine(DATABASE_URL)
    
    print("\nCreating all tables...")
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database tables created successfully in Railway!")
    print("\nTables created:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")
    
    engine.dispose()

if __name__ == "__main__":
    force_init_railway()
