"""
Add newsletter table to database
"""
import sqlite3

def migrate():
    conn = sqlite3.connect('database/products.db')
    cursor = conn.cursor()
    
    try:
        # Create newsletter table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS newsletter (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR(255) UNIQUE NOT NULL,
                discount_code VARCHAR(50) UNIQUE,
                subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Create index
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_newsletter_email ON newsletter(email)
        ''')
        
        conn.commit()
        print("✅ Newsletter table created successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
