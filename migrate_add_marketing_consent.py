"""
Add marketing_consent column to users table
Run this ONCE on Railway database
"""
import os
from sqlalchemy import create_engine, text

# Railway database URL
DATABASE_URL = "postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway"

def migrate_add_marketing_consent():
    """Add marketing_consent column to users table"""
    print("🔄 Adding marketing_consent column to users table...")
    
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='marketing_consent'
            """))
            
            if result.fetchone():
                print("✅ Column 'marketing_consent' already exists!")
                return
            
            # Add the column
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN marketing_consent BOOLEAN DEFAULT FALSE
            """))
            conn.commit()
            
            print("✅ Successfully added marketing_consent column!")
            print("📊 All existing users have marketing_consent=FALSE by default")
            
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        raise
    finally:
        engine.dispose()

if __name__ == "__main__":
    print("🚀 MARKETING CONSENT MIGRATION")
    print(f"📦 Database: {DATABASE_URL[:50]}...")
    print()
    
    confirm = input("⚠️  Run migration on Railway database? (yes/no): ").lower()
    if confirm == 'yes':
        migrate_add_marketing_consent()
        print("\n✅ Migration completed!")
    else:
        print("❌ Migration cancelled")
