"""
Delete duplicate lowercase categories from old manualbear.com database
DELETES all products with lowercase categories (cars, motorcycles, etc.)
Keeps products with Capitalized categories (Cars, Motorcycles, etc.)
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OLD ManualBear database (earnest-nurturing / manualbear.com)
# You need to get this from Railway - earnest-nurturing project
OLD_DATABASE_URL = input("Paste OLD ManualBear DATABASE_URL (from earnest-nurturing Railway): ").strip()

# Lowercase categories to DELETE
LOWERCASE_CATEGORIES = ['cars', 'motorcycles', 'trucks', 'construction', 'engines', 'other']

def delete_lowercase_categories():
    """Delete all products with lowercase categories"""
    engine = create_engine(OLD_DATABASE_URL)
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            # Check what will be deleted
            print("\n⚠️  PRODUCTS TO BE DELETED:")
            for cat in LOWERCASE_CATEGORIES:
                result = conn.execute(
                    text("SELECT COUNT(*) as count FROM products WHERE category = :cat"),
                    {"cat": cat}
                )
                count = result.fetchone()[0]
                if count > 0:
                    print(f"  🗑️  '{cat}': {count} products")
            
            # Total to delete
            result = conn.execute(
                text("SELECT COUNT(*) as count FROM products WHERE category IN :cats"),
                {"cats": tuple(LOWERCASE_CATEGORIES)}
            )
            total_to_delete = result.fetchone()[0]
            
            print(f"\n❌ TOTAL TO DELETE: {total_to_delete} products")
            
            # Show what will remain
            print("\n✅ PRODUCTS THAT WILL REMAIN:")
            result = conn.execute(text("""
                SELECT category, COUNT(*) as count 
                FROM products 
                WHERE category NOT IN :cats
                GROUP BY category 
                ORDER BY category
            """), {"cats": tuple(LOWERCASE_CATEGORIES)})
            
            for row in result:
                print(f"  ✓ '{row.category}': {row.count} products")
            
            # Confirm deletion
            print("\n" + "="*80)
            confirm = input(f"⚠️  DELETE {total_to_delete} products? Type 'DELETE' to confirm: ").strip()
            
            if confirm != 'DELETE':
                print("❌ Cancelled - nothing deleted")
                trans.rollback()
                return
            
            # Delete products
            result = conn.execute(
                text("DELETE FROM products WHERE category IN :cats"),
                {"cats": tuple(LOWERCASE_CATEGORIES)}
            )
            deleted = result.rowcount
            
            # Commit transaction
            trans.commit()
            
            print(f"\n✅ Deleted {deleted} products with lowercase categories")
            
            # Show final distribution
            print("\n📊 Final categories:")
            result = conn.execute(text("""
                SELECT category, COUNT(*) as count 
                FROM products 
                WHERE category IS NOT NULL
                GROUP BY category 
                ORDER BY category
            """))
            
            for row in result:
                print(f"  {row.category}: {row.count} products")
            
        except Exception as e:
            trans.rollback()
            print(f"\n❌ Error: {e}")
            raise
    
    print("\n✅ Cleanup complete!")

if __name__ == "__main__":
    print("="*80)
    print("🗑️  OLD ManualBear.com - DELETE Duplicate Categories")
    print("="*80)
    print("\n⚠️  WARNING: This will DELETE all products with lowercase categories!")
    print("\nCategories to DELETE:")
    print("  • cars")
    print("  • motorcycles")
    print("  • trucks")
    print("  • construction")
    print("  • engines")
    print("  • other")
    print("\nCategories to KEEP:")
    print("  • Cars")
    print("  • Motorcycles")
    print("  • Trucks")
    print("  • Construction")
    print("  • Engines")
    print("  • Other")
    print()
    
    delete_lowercase_categories()
