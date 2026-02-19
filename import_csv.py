"""
Import products from CSV file to SQLite database
Usage: python import_csv.py
"""
import pandas as pd
import sys
import re
from sqlalchemy import create_engine
from database.models import init_db, DATABASE_URL


def extract_year(text_input):
    """
    Extract year from text (title or model)
    Looks for 4-digit years between 1900-2099
    Returns the most recent year found or None
    """
    if not text_input or pd.isna(text_input):
        return None
    
    # Find all 4-digit numbers that could be years
    years = re.findall(r'\b(19\d{2}|20\d{2})\b', str(text_input))
    
    if years:
        # Return the most recent year found
        return int(max(years))
    
    return None


def determine_product_type(category):
    """
    Determine product type based on category
    Returns: vehicles, electronics, publications, or other
    """
    if not category or pd.isna(category):
        return 'other'
    
    category_lower = str(category).lower()
    
    # Vehicles
    vehicle_keywords = ['automotive', 'car', 'truck', 'motorcycle', 'bike', 'bus', 
                       'airplane', 'aircraft', 'boat', 'marine', 'vehicle', 'atv',
                       'scooter', 'van', 'suv', 'trailer', 'jet ski']
    
    # Electronics
    electronics_keywords = ['electronics', 'phone', 'computer', 'laptop', 'tablet',
                           'camera', 'photography', 'audio', 'tv', 'television',
                           'smartphone', 'watch', 'gaming', 'console', 'printer',
                           'scanner', 'monitor', 'speaker', 'headphones']
    
    # Publications
    publication_keywords = ['manual', 'magazine', 'book', 'publication', 'guide',
                           'journal', 'catalog', 'brochure', 'document']
    
    # Check category against keywords
    for keyword in vehicle_keywords:
        if keyword in category_lower:
            return 'vehicles'
    
    for keyword in electronics_keywords:
        if keyword in category_lower:
            return 'electronics'
    
    for keyword in publication_keywords:
        if keyword in category_lower:
            return 'publications'
    
    return 'other'

def import_products_from_csv(csv_file='products.csv'):
    """
    Import products from CSV file to SQLite database
    
    Args:
        csv_file: Path to the CSV file with products
    """
    print(f"Starting import from {csv_file}...")
    
    # Initialize database (create tables if they don't exist)
    print("Initializing database...")
    init_db()
    
    # Read CSV file
    print(f"Reading CSV file: {csv_file}...")
    try:
        df = pd.read_csv(csv_file)
        print(f"Found {len(df)} products in CSV file")
    except FileNotFoundError:
        print(f"ERROR: File {csv_file} not found!")
        print("Please make sure products.csv is in the same directory as this script.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR reading CSV file: {e}")
        sys.exit(1)
    
    # Validate required columns
    required_columns = ['title', 'description', 'price', 'category', 'brand', 'model']
    optional_columns = ['image_url']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"ERROR: Missing required columns: {missing_columns}")
        print(f"Available columns: {list(df.columns)}")
        print(f"Optional columns: {optional_columns}")
        sys.exit(1)
    
    # Clean data
    print("Cleaning data...")
    # Remove rows with missing critical data
    df = df.dropna(subset=['title', 'price', 'category', 'brand', 'model'])
    
    # Fill missing descriptions with empty string
    df['description'] = df['description'].fillna('')
    
    # Fill missing image_url with empty string if column exists
    if 'image_url' in df.columns:
        df['image_url'] = df['image_url'].fillna('')
        print(f"Found {(df['image_url'] != '').sum()} products with images")
    else:
        df['image_url'] = ''  # Add empty image_url column if not present
        print("No image_url column found, products will use default placeholder")
    
    # Ensure price is float
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df = df.dropna(subset=['price'])
    
    # Trim string columns
    string_columns = ['title', 'description', 'category', 'brand', 'model', 'image_url']
    for col in string_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    
    # Generate slugs for SEO-friendly URLs
    print("Generating SEO-friendly slugs...")
    from database.models import Product
    df['slug'] = df.apply(
        lambda row: Product.generate_slug(row['title'], row['brand'], row['model']), 
        axis=1
    )
    
    # Auto-detect year from title and model
    print("Auto-detecting years from titles and models...")
    df['year'] = df.apply(
        lambda row: extract_year(row['model']) or extract_year(row['title']),
        axis=1
    )
    years_detected = df['year'].notna().sum()
    print(f"  ✓ Detected years for {years_detected}/{len(df)} products")
    
    # Auto-detect product type from category
    print("Auto-detecting product types from categories...")
    df['product_type'] = df['category'].apply(determine_product_type)
    type_counts = df['product_type'].value_counts()
    print(f"  Product type distribution:")
    for ptype, count in type_counts.items():
        print(f"    - {ptype}: {count} products")
    
    print(f"After cleaning: {len(df)} products ready to import")
    
    # Import to database
    print("Importing to database...")
    engine = create_engine(DATABASE_URL)
    
    # Import in chunks for better performance with large datasets
    chunk_size = 10000
    total_chunks = (len(df) - 1) // chunk_size + 1
    
    for i, chunk_start in enumerate(range(0, len(df), chunk_size)):
        chunk_end = min(chunk_start + chunk_size, len(df))
        chunk = df[chunk_start:chunk_end]
        
        # Add ID suffix to slugs for uniqueness within this chunk
        chunk['slug'] = chunk.apply(
            lambda row: f"{row['slug']}-{chunk_start + row.name + 1}",
            axis=1
        )
        
        # Import chunk to database
        chunk.to_sql('products', engine, if_exists='append', index=False, method='multi')
        
        print(f"Progress: {i+1}/{total_chunks} chunks imported ({chunk_end}/{len(df)} products)")
    
    print(f"\n✓ Successfully imported {len(df)} products to database!")
    print(f"Database location: {DATABASE_URL}")


if __name__ == "__main__":
    import_products_from_csv()
