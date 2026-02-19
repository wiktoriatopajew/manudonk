"""
Import All Products from CSV with Descriptions and Prices
"""
import csv
import random
from database.models import Product, get_session

def parse_title(title):
    """Extract brand and model from title"""
    parts = title.split()
    
    # Try to detect brand (first word usually)
    brand = parts[0] if parts else "Unknown"
    
    # Model is usually the next few words
    if len(parts) > 1:
        model = " ".join(parts[1:4])  # Take 2-3 words for model
    else:
        model = "Manual"
    
    # Clean up model
    model = model.replace("Service", "").replace("Repair", "").replace("Manual", "").strip()
    if not model:
        model = "Service Manual"
    
    return brand, model

def generate_description(title, brand, model, category):
    """Generate HTML description for product"""
    
    # Random details based on category
    category_features = {
        'Trucks': [
            'Complete engine repair procedures',
            'Transmission and drivetrain service',
            'Brake system diagnostics',
            'Suspension and steering guides',
            'Electrical system schematics'
        ],
        'Engines': [
            'Engine tear-down and rebuild',
            'Carburetor and fuel system',
            'Ignition and electrical',
            'Cooling system maintenance',
            'Performance tuning guides'
        ],
        'Tractors': [
            'Hydraulic system repair',
            'PTO and implements',
            'Engine overhaul procedures',
            'Transmission service',
            'Electrical troubleshooting'
        ]
    }
    
    features = category_features.get(category, [
        'Complete service procedures',
        'Detailed repair instructions',
        'Maintenance schedules',
        'Troubleshooting guides',
        'Technical specifications'
    ])
    
    feature_list = "\n".join([f"    <li>✅ {f}</li>" for f in features[:5]])
    
    return f"""
<h3>Complete Service & Repair Manual</h3>
<p>This comprehensive manual covers all aspects of service, maintenance, and repair for your {brand} {model}.</p>

<h4>What's Included:</h4>
<ul>
{feature_list}
    <li>✅ Detailed diagrams and illustrations</li>
    <li>✅ Wiring and hydraulic schematics</li>
</ul>

<h4>Perfect for:</h4>
<ul>
    <li>🔧 Professional mechanics</li>
    <li>🚗 DIY enthusiasts</li>
    <li>⚙️ Workshop and fleet maintenance</li>
    <li>📚 Technical reference</li>
</ul>

<p><strong>Format:</strong> Digital PDF - Instant download after purchase</p>
<p><strong>Pages:</strong> {random.randint(200, 800)}+ pages of detailed technical information</p>
<p><strong>Language:</strong> English</p>
"""

def import_all_products():
    """Import all products from CSV"""
    
    print("="*70)
    print("📦 IMPORTING ALL PRODUCTS FROM CSV")
    print("="*70)
    print()
    
    session = get_session()
    
    try:
        added = 0
        updated = 0
        
        with open('test2.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                product_id = int(row['ID'])
                title = row['English Title']
                category = row['Category'].strip('*')  # Remove asterisks
                pdf_url = row['Link PDF']
                
                # Parse brand and model
                brand, model = parse_title(title)
                
                # Generate description
                description = generate_description(title, brand, model, category)
                
                # Random price between 7.99 and 14.99
                price = round(random.uniform(7.99, 14.99), 2)
                
                # Create slug
                slug = title.lower()
                slug = slug.replace(' ', '-').replace('&', 'and').replace(',', '')
                slug = ''.join(c for c in slug if c.isalnum() or c == '-')
                slug = slug[:200]  # Limit length
                
                # Check if exists
                existing = session.query(Product).filter(Product.id == product_id).first()
                
                if existing:
                    # Update
                    existing.title = title
                    existing.brand = brand
                    existing.model = model
                    existing.category = category
                    existing.description = description
                    existing.price = price
                    existing.pdf_url = pdf_url
                    existing.slug = slug
                    existing.is_featured = (added + updated) < 5  # First 5 are featured
                    updated += 1
                    print(f"✅ Updated: {title} (${price})")
                else:
                    # Create new
                    product = Product(
                        id=product_id,
                        title=title,
                        brand=brand,
                        model=model,
                        category=category,
                        description=description,
                        price=price,
                        pdf_url=pdf_url,
                        slug=slug,
                        is_featured=(added + updated) < 5  # First 5 are featured
                    )
                    session.add(product)
                    added += 1
                    print(f"✅ Added: {title} (${price})")
        
        session.commit()
        
        print()
        print("="*70)
        print("✅ IMPORT COMPLETE!")
        print("="*70)
        print(f"📊 Added: {added} products")
        print(f"🔄 Updated: {updated} products")
        print(f"💰 Total products: {added + updated}")
        print()
        print("🌐 View products at: http://localhost:8000")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    import_all_products()
