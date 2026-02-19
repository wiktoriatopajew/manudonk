"""
Generate slugs for existing products in the database
Run this after importing products from CSV to create SEO-friendly URLs
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Product, DATABASE_URL
import sys


def generate_slugs_for_all_products():
    """Generate slugs for all products that don't have one"""
    print("Connecting to database...")
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Get all products without slugs
        products_without_slug = session.query(Product).filter(
            (Product.slug == None) | (Product.slug == '')
        ).all()
        
        total = len(products_without_slug)
        print(f"Found {total} products without slugs")
        
        if total == 0:
            print("✓ All products already have slugs!")
            return
        
        print("Generating slugs...")
        
        updated_count = 0
        for i, product in enumerate(products_without_slug, 1):
            try:
                # Generate slug
                product.generate_and_set_slug()
                
                # Progress indicator
                if i % 1000 == 0:
                    print(f"Progress: {i}/{total} products processed...")
                    session.commit()  # Commit in batches
                    
                updated_count += 1
                
            except Exception as e:
                print(f"Error generating slug for product {product.id}: {e}")
                continue
        
        # Final commit
        session.commit()
        
        print(f"\n✓ Successfully generated slugs for {updated_count} products!")
        print(f"Database updated: {DATABASE_URL}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        session.rollback()
        sys.exit(1)
    finally:
        session.close()


def verify_slugs():
    """Verify that all products have slugs"""
    print("\nVerifying slugs...")
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        total_products = session.query(Product).count()
        products_with_slugs = session.query(Product).filter(
            (Product.slug != None) & (Product.slug != '')
        ).count()
        
        print(f"Total products: {total_products}")
        print(f"Products with slugs: {products_with_slugs}")
        print(f"Products without slugs: {total_products - products_with_slugs}")
        
        if products_with_slugs == total_products:
            print("✓ All products have slugs!")
        else:
            print("⚠ Some products still don't have slugs")
            
    finally:
        session.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Slug Generation Tool")
    print("=" * 60)
    print()
    
    generate_slugs_for_all_products()
    verify_slugs()
    
    print()
    print("=" * 60)
    print("Done! You can now access products via clean URLs:")
    print("Example: https://strona.pl/manuals/ford-f150-manual-123")
    print("=" * 60)
