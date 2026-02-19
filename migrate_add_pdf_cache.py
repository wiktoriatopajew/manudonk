"""
Migration script to add PDFCache table to database
Run this once to create the new table
"""
from database.models import Base, get_engine

def migrate():
    """Create PDFCache table"""
    engine = get_engine()
    
    # Import PDFCache to ensure it's registered
    from database.models import PDFCache
    
    print("Creating PDFCache table...")
    Base.metadata.create_all(bind=engine)
    print("✅ Migration complete! PDFCache table created.")

if __name__ == "__main__":
    migrate()
