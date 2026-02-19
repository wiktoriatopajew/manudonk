"""
Add Example Product from CSV to Database
"""
import csv
from database.models import Product, get_session

def add_example_product():
    """Add first product from test2.csv to database"""
    
    # Read first product from CSV
    with open('test2.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        row = next(reader)  # Get first row
    
    product_id = int(row['ID'])
    category = row['Category']
    title = row['English Title']
    pdf_link = row['Link PDF']
    
    # Create product data
    # Parse title to extract brand and model
    parts = title.split()
    brand = parts[0] if parts else "Ford"
    model = " ".join(parts[1:3]) if len(parts) > 1 else "F-150"
    
    print("="*60)
    print("📦 Adding Example Product to Database")
    print("="*60)
    print(f"ID: {product_id}")
    print(f"Title: {title}")
    print(f"Brand: {brand}")
    print(f"Model: {model}")
    print(f"Category: {category}")
    print(f"PDF Link: {pdf_link[:50]}...")
    print()
    
    session = get_session()
    try:
        # Check if product already exists
        existing = session.query(Product).filter(Product.id == product_id).first()
        
        if existing:
            print(f"⚠️  Product {product_id} already exists!")
            print(f"   Updating with new data...")
            
            existing.title = title
            existing.brand = brand
            existing.model = model
            existing.category = category
            existing.description = f"""
<h3>Complete Service & Repair Manual</h3>
<p>This comprehensive manual covers all aspects of service, maintenance, and repair for your {brand} {model}.</p>

<h4>What's Included:</h4>
<ul>
    <li>✅ Complete step-by-step repair procedures</li>
    <li>✅ Detailed diagrams and illustrations</li>
    <li>✅ Troubleshooting guides</li>
    <li>✅ Wiring diagrams</li>
    <li>✅ Maintenance schedules</li>
    <li>✅ Technical specifications</li>
</ul>

<h4>Perfect for:</h4>
<ul>
    <li>🔧 Professional mechanics</li>
    <li>🚗 DIY enthusiasts</li>
    <li>⚙️ Fleet maintenance</li>
</ul>

<p><strong>Format:</strong> Digital PDF - Instant download after purchase</p>
<p><strong>Pages:</strong> 500+ pages of detailed information</p>
            """
            existing.price = 9.99
            existing.pdf_url = pdf_link
            existing.is_featured = True
            existing.slug = title.lower().replace(' ', '-').replace('&', 'and')
            
            session.commit()
            print(f"✅ Product updated!")
            
        else:
            print(f"✨ Creating new product...")
            
            product = Product(
                id=product_id,
                title=title,
                brand=brand,
                model=model,
                category=category,
                description=f"""
<h3>Complete Service & Repair Manual</h3>
<p>This comprehensive manual covers all aspects of service, maintenance, and repair for your {brand} {model}.</p>

<h4>What's Included:</h4>
<ul>
    <li>✅ Complete step-by-step repair procedures</li>
    <li>✅ Detailed diagrams and illustrations</li>
    <li>✅ Troubleshooting guides</li>
    <li>✅ Wiring diagrams</li>
    <li>✅ Maintenance schedules</li>
    <li>✅ Technical specifications</li>
</ul>

<h4>Perfect for:</h4>
<ul>
    <li>🔧 Professional mechanics</li>
    <li>🚗 DIY enthusiasts</li>
    <li>⚙️ Fleet maintenance</li>
</ul>

<p><strong>Format:</strong> Digital PDF - Instant download after purchase</p>
<p><strong>Pages:</strong> 500+ pages of detailed information</p>
                """,
                price=9.99,
                pdf_url=pdf_link,
                is_featured=True,
                slug=title.lower().replace(' ', '-').replace('&', 'and')
            )
            
            session.add(product)
            session.commit()
            print(f"✅ Product created!")
        
        print()
        print("="*60)
        print("✅ SUCCESS!")
        print("="*60)
        print()
        print(f"🌐 View product at: http://localhost:8000/manuals/{title.lower().replace(' ', '-').replace('&', 'and')}")
        print(f"🛒 Price: $9.99")
        print()
        print("📝 Next steps:")
        print("1. Go to the product page")
        print("2. Add to cart and checkout")
        print("3. Use Stripe test card: 4242 4242 4242 4242")
        print("4. Watch the console - it will:")
        print("   • Download the PDF")
        print("   • Upload to Google Drive")
        print("   • Send you an email with the link")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    add_example_product()
