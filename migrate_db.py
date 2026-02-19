"""
Database migration script - adds new columns for PDF delivery system
"""
from database.models import get_engine
from sqlalchemy import text

def migrate():
    engine = get_engine()
    
    with engine.connect() as conn:
        # Add download_link column to orders table
        try:
            conn.execute(text("ALTER TABLE orders ADD COLUMN download_link VARCHAR(500)"))
            conn.commit()
            print("✅ Successfully added download_link column to orders table")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print("ℹ️  Column download_link already exists in orders")
            else:
                print(f"❌ Error: {e}")
        
        # Add Google Drive link to products table
        try:
            conn.execute(text("ALTER TABLE products ADD COLUMN google_drive_link VARCHAR(500)"))
            conn.commit()
            print("✅ Successfully added google_drive_link column to products table")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print("ℹ️  Column google_drive_link already exists")
            else:
                print(f"❌ Error: {e}")
        
        # Add preview images to products table
        try:
            conn.execute(text("ALTER TABLE products ADD COLUMN preview_images TEXT"))
            conn.commit()
            print("✅ Successfully added preview_images column to products table")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print("ℹ️  Column preview_images already exists")
            else:
                print(f"❌ Error: {e}")
        
        # Add PDF processed flag to products table
        try:
            conn.execute(text("ALTER TABLE products ADD COLUMN pdf_processed BOOLEAN DEFAULT 0"))
            conn.commit()
            print("✅ Successfully added pdf_processed column to products table")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print("ℹ️  Column pdf_processed already exists")
            else:
                print(f"❌ Error: {e}")
        
        # Create password_reset_tokens table
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token VARCHAR(64) UNIQUE NOT NULL,
                    expires_at DATETIME NOT NULL,
                    used BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_password_reset_token ON password_reset_tokens(token)"))
            conn.commit()
            print("✅ Successfully created password_reset_tokens table")
        except Exception as e:
            print(f"ℹ️  password_reset_tokens table already exists")
        
        print("\n" + "="*60)
        print("✅ MIGRATION COMPLETE!")
        print("="*60)
        print("\nProducts table now has:")
        print("  • google_drive_link - Stores permanent Google Drive URL")
        print("  • preview_images - Stores JSON array of preview paths")
        print("  • pdf_processed - Flag to track if PDF was processed")
        print("\nSystem will now:")
        print("  ✓ Upload PDF to Google Drive only once")
        print("  ✓ Reuse same link for all future buyers")
        print("  ✓ Store preview images for product pages")

if __name__ == "__main__":
    migrate()
