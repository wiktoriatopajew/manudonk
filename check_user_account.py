"""
Check user account and orders
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import User, Order

load_dotenv()

# Railway database
database_url = os.getenv('DATABASE_URL')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()

email = "cnhindustrialpolska@gmail.com"

print("="*80)
print(f"🔍 SPRAWDZAM KONTO: {email}")
print("="*80)

# Check user
user = session.query(User).filter_by(email=email).first()

if user:
    print(f"\n✅ Użytkownik istnieje:")
    print(f"   Email: {user.email}")
    print(f"   Verified: {user.is_verified}")
    print(f"   Created: {user.created_at}")
    print(f"   Is Admin: {user.is_admin}")
    
    # Check orders
    orders = session.query(Order).filter_by(email=email).all()
    
    print(f"\n📦 Zamówienia: {len(orders)}")
    
    if orders:
        for order in orders:
            print(f"\n   Order #{order.id}")
            print(f"   Status: {order.status}")
            print(f"   Created: {order.created_at}")
            print(f"   Price: ${order.price}")
            print(f"   Product ID: {order.product_id}")
            print(f"   Download link: {order.download_link}")
    else:
        print("   ❌ Brak zamówień dla tego użytkownika!")
else:
    print(f"\n❌ Użytkownik {email} NIE ISTNIEJE w bazie!")

session.close()
print("\n" + "="*80)
