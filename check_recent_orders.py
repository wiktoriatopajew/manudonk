"""
Check recent orders and their status
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database.models import Order, Product

load_dotenv()

# Railway database
database_url = os.getenv('DATABASE_URL')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()

print("="*80)
print("📋 OSTATNIE ZAMÓWIENIA")
print("="*80)

# Get last 10 orders
recent_orders = session.query(Order).order_by(desc(Order.created_at)).limit(10).all()

if not recent_orders:
    print("\n❌ Brak zamówień w bazie!")
else:
    for order in recent_orders:
        product = session.query(Product).filter_by(id=order.product_id).first()
        
        print(f"\n📦 Order #{order.id}")
        print(f"   Email: {order.email}")
        print(f"   Status: {order.status}")
        print(f"   Created: {order.created_at}")
        print(f"   Price: ${order.price}")
        
        if product:
            print(f"   Product: {product.title}")
            print(f"   Product ID: {product.id}")
            print(f"   PDF URL: {'✅ ' + product.pdf_url[:50] + '...' if product.pdf_url else '❌ Brak'}")
            print(f"   Google Drive: {'✅ ' + product.google_drive_link[:50] + '...' if product.google_drive_link else '❌ NIE UPLOADOWANE'}")
        
        print(f"   Download Link: {'✅ ' + order.download_link[:50] + '...' if order.download_link else '❌ Brak'}")

session.close()

print("\n" + "="*80)
print("💡 Sprawdź logi Railway aby zobaczyć co się stało podczas płatności")
print("="*80)
