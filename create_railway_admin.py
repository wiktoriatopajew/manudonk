"""
Create admin account in Railway database
"""
import os
import sys

# Set DATABASE_URL before importing models
os.environ['DATABASE_URL'] = 'postgresql://postgres:oqaUYkSoHsdnycMDGTyflRMRBeWQOOdY@caboose.proxy.rlwy.net:54886/railway'

from database.models import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def create_or_update_admin(email, password):
    DATABASE_URL = os.environ['DATABASE_URL']
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if user exists
        user = session.query(User).filter(User.email == email).first()
        
        if user:
            print(f"✓ Użytkownik {email} istnieje. Aktualizuję hasło...")
            user.is_admin = True
            user.is_verified = True
            user.set_password(password)
        else:
            print(f"✓ Tworzę nowe konto admin: {email}")
            user = User(
                email=email,
                is_admin=True,
                is_verified=True
            )
            user.set_password(password)
            session.add(user)
        
        session.commit()
        
        print("\n" + "="*60)
        print("✅ KONTO ADMIN UTWORZONE/ZAKTUALIZOWANE")
        print("="*60)
        print(f"Email:    {email}")
        print(f"Hasło:    {password}")
        print(f"Admin:    True")
        print(f"Verified: True")
        print("="*60)
        print("\nMożesz się zalogować na:")
        print("https://web-production-3a772.up.railway.app/login")
        print("="*60)
        
        return True
        
    except Exception as e:
        session.rollback()
        print(f"❌ Błąd: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        email = sys.argv[1]
        password = sys.argv[2]
    else:
        email = "admin@manualdonkey.com"
        password = "admin123"
        print(f"Używam domyślnych danych:")
        print(f"Email: {email}")
        print(f"Hasło: {password}")
        print()
    
    create_or_update_admin(email, password)
