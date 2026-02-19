"""
Fix failed orders - process PDFs and send emails
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Order, Product
from railway_pdf_processor import RailwayPDFProcessor
from email_utils import send_manual_ready_email

load_dotenv()

# Railway database
database_url = os.getenv('DATABASE_URL')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()

print("="*80)
print("🔧 NAPRAWIANIE NIEUDANYCH ZAMÓWIEŃ")
print("="*80)

# Orders to fix: #15 and #16
orders_to_fix = [15, 16]

processor = RailwayPDFProcessor()

for order_id in orders_to_fix:
    order = session.query(Order).filter_by(id=order_id).first()
    
    if not order:
        print(f"\n❌ Order #{order_id} nie znaleziony")
        continue
    
    product = session.query(Product).filter_by(id=order.product_id).first()
    
    if not product:
        print(f"\n❌ Product nie znaleziony dla Order #{order_id}")
        continue
    
    print(f"\n📦 Przetwarzam Order #{order_id}")
    print(f"   Email: {order.email}")
    print(f"   Product: {product.title}")
    
    # Check if already has Google Drive link
    if product.google_drive_link:
        print(f"   ✅ Google Drive link już istnieje: {product.google_drive_link[:60]}...")
        download_link = product.google_drive_link
    else:
        # Process PDF
        print(f"   📥 Pobieram i uploaduję PDF...")
        success = processor.process_product(product.id)
        
        if success:
            # Refresh product to get new google_drive_link
            session.refresh(product)
            download_link = product.google_drive_link
            print(f"   ✅ Sukces! Google Drive: {download_link[:60]}...")
        else:
            print(f"   ❌ Błąd podczas przetwarzania PDF")
            continue
    
    # Update order
    order.download_link = download_link
    session.commit()
    
    # Send email
    print(f"   📧 Wysyłam email do {order.email}...")
    try:
        send_manual_ready_email(
            to_email=order.email,
            order_id=order.id,
            product_title=product.title,
            download_link=download_link
        )
        print(f"   ✅ Email wysłany!")
    except Exception as e:
        print(f"   ❌ Błąd wysyłania emaila: {str(e)}")

processor.close()
session.close()

print("\n" + "="*80)
print("✅ GOTOWE!")
print("="*80)
