"""
Initialize database and create tables
"""
from database.models import Base, get_engine, get_session, Product

def init_database():
    """Create all tables in the database"""
    print("Creating database tables...")
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully!")
    
    # Add some sample products
    session = get_session()
    try:
        # Check if we already have products
        count = session.query(Product).count()
        if count > 0:
            print(f"Database already contains {count} products.")
            return
        
        print("Adding sample products...")
        sample_products = [
            Product(
                title="Ford F-150 Repair Manual 2015-2023",
                description="Complete repair and maintenance manual for Ford F-150 trucks. Includes engine specifications, electrical diagrams, maintenance schedules, and troubleshooting guides. Perfect for DIY mechanics and professionals.",
                price=29.99,
                category="Automotive",
                brand="Ford",
                model="F-150"
            ),
            Product(
                title="Samsung Galaxy S21 User Guide",
                description="Comprehensive user manual for Samsung Galaxy S21 smartphone. Learn all features, settings, camera tips, and advanced functions. Includes troubleshooting section.",
                price=9.99,
                category="Electronics",
                brand="Samsung",
                model="Galaxy S21"
            ),
            Product(
                title="Bosch WAW28750GB Washing Machine Manual",
                description="Complete instruction manual for Bosch WAW28750GB washing machine. Installation guide, program descriptions, maintenance tips, and error code explanations.",
                price=12.99,
                category="Home Appliances",
                brand="Bosch",
                model="WAW28750GB"
            ),
            Product(
                title="DeWalt DCD996B Drill Driver Manual",
                description="User manual for DeWalt DCD996B cordless drill driver. Safety instructions, technical specifications, battery charging guide, and maintenance procedures.",
                price=7.99,
                category="Power Tools",
                brand="DeWalt",
                model="DCD996B"
            ),
            Product(
                title="Canon EOS R5 User Manual",
                description="Professional user guide for Canon EOS R5 mirrorless camera. Complete coverage of all functions, menu settings, shooting modes, video recording, and Wi-Fi connectivity.",
                price=19.99,
                category="Photography",
                brand="Canon",
                model="EOS R5"
            ),
            Product(
                title="LG OLED55C1 TV Service Manual",
                description="Technical service manual for LG OLED55C1 4K Smart TV. Includes setup instructions, Smart TV features, troubleshooting, and advanced picture settings.",
                price=15.99,
                category="Electronics",
                brand="LG",
                model="OLED55C1"
            ),
            Product(
                title="Honda CR-V Owner's Manual 2020-2024",
                description="Complete owner's manual for Honda CR-V SUV. Vehicle features, safety systems, maintenance schedule, specifications, and warranty information.",
                price=24.99,
                category="Automotive",
                brand="Honda",
                model="CR-V"
            ),
            Product(
                title="Makita XPH12Z Hammer Drill Manual",
                description="Operating instructions for Makita XPH12Z brushless hammer drill. Safety guidelines, operation modes, battery care, and maintenance procedures.",
                price=8.99,
                category="Power Tools",
                brand="Makita",
                model="XPH12Z"
            ),
        ]
        
        for product in sample_products:
            product.generate_and_set_slug()
            session.add(product)
        
        session.commit()
        print(f"✓ Added {len(sample_products)} sample products!")
        print("\nDatabase is ready! You can now:")
        print("1. Import more products from CSV: python import_csv.py your_file.csv")
        print("2. Visit http://localhost:8000 to see the website")
        
    except Exception as e:
        session.rollback()
        print(f"Error adding sample products: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    init_database()
