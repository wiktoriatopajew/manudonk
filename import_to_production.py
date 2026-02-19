"""
Import products from CSV to Railway PostgreSQL database
Usage: python import_to_production.py
"""
import pandas as pd
import sys
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def import_products_to_production(csv_file='products.csv'):
    """
    Import products from CSV file to Railway PostgreSQL database
    
    Args:
        csv_file: Path to the CSV file with products
    """
    print(f"🚀 Starting import from {csv_file} to Railway PostgreSQL...")
    
    # Get DATABASE_URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL not found in .env file!")
        print("Please add your Railway PostgreSQL connection string to .env")
        sys.exit(1)
    
    # Fix postgres:// to postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    print(f"📡 Connecting to: {database_url.split('@')[1] if '@' in database_url else 'database'}...")
    
    # Read CSV file
    print(f"📂 Reading CSV file: {csv_file}...")
    try:
        df = pd.read_csv(csv_file)
        print(f"✅ Found {len(df)} products in CSV file")
    except FileNotFoundError:
        print(f"❌ ERROR: File {csv_file} not found!")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR reading CSV file: {e}")
        sys.exit(1)
    
    # Validate required columns
    required_columns = ['title', 'description', 'price', 'category', 'brand', 'model']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"❌ ERROR: Missing required columns: {missing_columns}")
        sys.exit(1)
    
    # Clean data
    print("🧹 Cleaning data...")
    df = df.dropna(subset=['title', 'price', 'category', 'brand', 'model'])
    df['description'] = df['description'].fillna('')
    
    # Handle image_url
    if 'image_url' in df.columns:
        df['image_url'] = df['image_url'].fillna('')
        print(f"🖼️  Found {(df['image_url'] != '').sum()} products with images")
    else:
        df['image_url'] = ''
    
    # Ensure price is float
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df = df.dropna(subset=['price'])
    
    # Trim string columns
    for col in ['title', 'description', 'category', 'brand', 'model', 'image_url']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    
    # Generate slugs
    print("🔗 Generating SEO-friendly slugs...")
    def generate_slug(title, brand, model):
        import re
        slug_parts = []
        if brand:
            slug_parts.append(brand.lower())
        if model:
            slug_parts.append(model.lower())
        slug_parts.append(title.lower())
        slug = '-'.join(slug_parts)
        slug = re.sub(r'[^a-z0-9-]', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')
    
    df['slug'] = df.apply(
        lambda row: generate_slug(row['title'], row['brand'], row['model']), 
        axis=1
    )
    
    # Make slugs unique
    df['slug'] = df.apply(lambda row: f"{row['slug']}-{row.name + 1}", axis=1)
    
    print(f"✅ {len(df)} products ready to import")
    
    # Import to database
    print("💾 Importing to Railway PostgreSQL...")
    try:
        engine = create_engine(database_url)
        df.to_sql('products', engine, if_exists='append', index=False, method='multi')
        print(f"\n🎉 Successfully imported {len(df)} products to production database!")
        print(f"📊 Total products in database: {len(df)}")
        
        # Show sample products
        print("\n📦 Sample products imported:")
        for idx, row in df.head(3).iterrows():
            print(f"  • {row['brand']} {row['model']} - {row['title']} (${row['price']})")
        
    except Exception as e:
        print(f"\n❌ ERROR importing to database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import_products_to_production()
