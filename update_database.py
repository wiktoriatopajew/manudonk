"""
Update Database with Google Drive Links and Preview Images
"""
import json
import sys
from pathlib import Path
from database.models import Product, get_session


def update_products_from_results(results_file: str = "complete_results.json", dry_run: bool = False):
    """
    Update products in database with Google Drive links and preview paths
    
    Args:
        results_file: JSON file with processing results
        dry_run: If True, only show what would be updated without making changes
    """
    
    if not Path(results_file).exists():
        print(f"❌ Results file not found: {results_file}")
        print("💡 Run process_pdfs.py first to generate results")
        return
    
    # Load results
    with open(results_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    session = get_session()
    
    try:
        print("="*70)
        print("📝 UPDATING DATABASE")
        print("="*70)
        
        if dry_run:
            print("\n🔍 DRY RUN MODE - No changes will be made\n")
        
        updated_count = 0
        not_found_count = 0
        failed_count = 0
        
        for product_id_str, data in results.items():
            product_id = int(product_id_str)
            
            # Find product in database
            product = session.query(Product).filter(Product.id == product_id).first()
            
            if not product:
                print(f"⚠️  Product {product_id} not found in database")
                not_found_count += 1
                continue
            
            if data['status'] != 'success':
                print(f"❌ Product {product_id} failed processing, skipping")
                failed_count += 1
                continue
            
            print(f"\n📦 Product: {product.title} (ID: {product_id})")
            
            # Update Google Drive link if available
            if 'google_drive_link' in data:
                if dry_run:
                    print(f"   [DRY RUN] Would set Google Drive link: {data['google_drive_link'][:50]}...")
                else:
                    product.google_drive_link = data['google_drive_link']
                    product.pdf_processed = True  # Mark as processed
                    print(f"   ✅ Set Google Drive link")
            
            # Update preview images
            if 'preview_paths' in data and data['preview_paths']:
                # Convert absolute paths to relative web paths
                preview_paths = data['preview_paths']
                web_paths = []
                
                for path in preview_paths:
                    # Convert: storage/previews/123/page_1.jpg -> /static/images/previews/123/page_1.jpg
                    path_obj = Path(path)
                    relative_path = str(path_obj).replace('static\\', '/static/').replace('\\', '/')
                    if not relative_path.startswith('/'):
                        relative_path = '/' + relative_path
                    web_paths.append(relative_path)
                
                preview_images_json = json.dumps(web_paths)
                
                if dry_run:
                    print(f"   [DRY RUN] Would set {len(web_paths)} preview images")
                else:
                    product.preview_images = preview_images_json
                    print(f"   ✅ Set {len(web_paths)} preview images")
            
            if not dry_run:
                updated_count += 1
        
        if not dry_run:
            session.commit()
            print("\n" + "="*70)
            print("✅ DATABASE UPDATED SUCCESSFULLY")
            print("="*70)
            print(f"\n📊 Summary:")
            print(f"   • Updated: {updated_count} products")
            print(f"   • Not found: {not_found_count} products")
            print(f"   • Failed: {failed_count} products")
        else:
            print("\n" + "="*70)
            print("🔍 DRY RUN COMPLETE")
            print("="*70)
            print(f"\n📊 Would update: {len(results) - not_found_count - failed_count} products")
            print("\n💡 Run without --dry-run to apply changes")
    
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error updating database: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        session.close()


def add_preview_images_column():
    """
    Add preview_images column to Product table if it doesn't exist
    """
    from sqlalchemy import text
    session = get_session()
    
    try:
        print("🔧 Adding preview_images column to Product table...")
        
        # Check if column exists
        result = session.execute(text(
            "SELECT COUNT(*) FROM pragma_table_info('products') WHERE name='preview_images'"
        ))
        exists = result.scalar() > 0
        
        if exists:
            print("✅ Column already exists")
            return
        
        # Add column
        session.execute(text(
            "ALTER TABLE products ADD COLUMN preview_images TEXT"
        ))
        session.commit()
        
        print("✅ Column added successfully")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {str(e)}")
    finally:
        session.close()


def main():
    """Main entry point"""
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--dry-run":
            update_products_from_results(dry_run=True)
        elif sys.argv[1] == "--add-column":
            add_preview_images_column()
        elif sys.argv[1] == "--help":
            print("Usage:")
            print("  python update_database.py              # Update database")
            print("  python update_database.py --dry-run    # Show what would be updated")
            print("  python update_database.py --add-column # Add preview_images column")
        else:
            results_file = sys.argv[1]
            update_products_from_results(results_file)
    else:
        # Interactive mode
        print("="*70)
        print("DATABASE UPDATE TOOL")
        print("="*70)
        print("\nThis will update products in database with:")
        print("  • Google Drive download links")
        print("  • Preview image paths")
        print("\nUsing data from: complete_results.json")
        
        response = input("\nContinue? (y/n): ")
        
        if response.lower() == 'y':
            update_products_from_results()
        else:
            print("Cancelled")


if __name__ == "__main__":
    main()
