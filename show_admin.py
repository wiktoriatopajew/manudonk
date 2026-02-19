"""
Sprawdź konta adminów w bazie
"""
import os
from database.models import get_session, User

session = get_session()

try:
    # Znajdź wszystkich adminów
    admins = session.query(User).filter(User.is_admin == True).all()
    
    if not admins:
        print("❌ Brak kont adminów w bazie!")
        print("\nUtwórz admina:")
        print("railway run python create_admin.py admin@example.com admin123")
    else:
        print(f"✅ Znaleziono {len(admins)} admin(ów):\n")
        for admin in admins:
            print(f"Email: {admin.email}")
            print(f"Is Admin: {admin.is_admin}")
            print(f"Is Verified: {admin.is_verified}")
            print(f"Created: {admin.created_at}")
            print("-" * 50)
            
except Exception as e:
    print(f"❌ Błąd: {e}")
finally:
    session.close()
