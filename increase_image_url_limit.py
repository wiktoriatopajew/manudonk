"""
Increase image_url column size to handle multiple images
"""
import os
os.environ['DATABASE_URL'] = 'postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway'

from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])

print("🔧 Increasing image_url column size from 500 to 2000 characters...")

with engine.connect() as conn:
    # Alter column to allow longer URLs (for multiple images)
    conn.execute(text("ALTER TABLE products ALTER COLUMN image_url TYPE VARCHAR(2000)"))
    conn.commit()
    print("✅ Column size increased successfully!")

# Verify
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT column_name, character_maximum_length 
        FROM information_schema.columns 
        WHERE table_name = 'products' AND column_name = 'image_url'
    """)).fetchone()
    print(f"\nVerification: image_url now has {result[1]} character limit")
