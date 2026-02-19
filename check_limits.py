import os
os.environ['DATABASE_URL'] = 'postgresql://postgres:TeiduPLPjjISbQncemTWAkkBXNCdaRak@tramway.proxy.rlwy.net:38542/railway'

from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT column_name, character_maximum_length 
        FROM information_schema.columns 
        WHERE table_name = 'products' 
        AND column_name IN ('title', 'slug', 'brand', 'model', 'category')
        ORDER BY column_name
    """)).fetchall()
    
    print("Column limits in Railway database:")
    for row in result:
        print(f"  {row[0]}: {row[1]}")

print(f"\nTotal products: ", end="")
with engine.connect() as conn:
    count = conn.execute(text("SELECT COUNT(*) FROM products")).fetchone()[0]
    print(count)
