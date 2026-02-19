"""
Napraw użytkownika w Railway PostgreSQL
- Zweryfikuj konto
- Zresetuj hasło
- Nadaj uprawnienia admina
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import User

load_dotenv()

def fix_user(email: str, verify: bool = True, make_admin: bool = False, new_password: str = None):
    """
    Napraw użytkownika w Railway DB
    
    Args:
        email: Email użytkownika
        verify: Czy zweryfikować konto (ustaw is_verified = True)
        make_admin: Czy nadać uprawnienia admina
        new_password: Nowe hasło (jeśli None, hasło nie zostanie zmienione)
    """
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ BŁĄD: DATABASE_URL nie znaleziono!")
        return False
    
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    print("=" * 80)
    print("🔧 NAPRAWA UŻYTKOWNIKA - RAILWAY POSTGRESQL")
    print("=" * 80)
    print(f"📧 Email: {email}")
    print(f"✉️  Weryfikacja: {'TAK' if verify else 'NIE'}")
    print(f"👑 Admin: {'TAK' if make_admin else 'NIE'}")
    print(f"🔑 Nowe hasło: {'TAK' if new_password else 'NIE'}")
    print()
    
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Znajdź użytkownika
        user = session.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"❌ BŁĄD: Użytkownik {email} nie istnieje w bazie!")
            print("   Utwórz konto przez rejestrację lub create_admin.py")
            session.close()
            return False
        
        print(f"✅ Znaleziono użytkownika:")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   is_verified (przed): {user.is_verified}")
        print(f"   is_admin (przed): {user.is_admin}")
        print()
        
        # Wykonaj naprawy
        changes_made = False
        
        if verify and not user.is_verified:
            user.is_verified = True
            print("✅ Ustawiono is_verified = True")
            changes_made = True
        
        if make_admin and not user.is_admin:
            user.is_admin = True
            print("✅ Ustawiono is_admin = True")
            changes_made = True
        
        if new_password:
            user.set_password(new_password)
            print(f"✅ Ustawiono nowe hasło: {new_password}")
            changes_made = True
        
        if changes_made:
            session.commit()
            print()
            print("💾 Zapisano zmiany w bazie danych")
            print()
            print("📊 STAN PO NAPRAWIE:")
            print(f"   Email: {user.email}")
            print(f"   is_verified: {user.is_verified} {'✅' if user.is_verified else '❌'}")
            print(f"   is_admin: {user.is_admin} {'👑' if user.is_admin else ''}")
            if new_password:
                print(f"   Hasło: {new_password}")
            print()
            print("✅ Użytkownik naprawiony! Możesz teraz się zalogować.")
        else:
            print("ℹ️  Brak zmian do wykonania - użytkownik już jest prawidłowy")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"\n❌ BŁĄD: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("🔧 NAPRAWA UŻYTKOWNIKA W RAILWAY")
    print("=" * 80)
    print()
    
    # Pobierz email
    if len(sys.argv) > 1:
        email = sys.argv[1]
    else:
        email = input("Podaj email użytkownika: ").strip()
    
    if not email:
        print("❌ Musisz podać email!")
        sys.exit(1)
    
    # Opcje
    print()
    print("Co chcesz zrobić?")
    print("1. Zweryfikować konto (is_verified = True)")
    print("2. Nadać uprawnienia admina")
    print("3. Zresetować hasło")
    print("4. Wszystko powyższe")
    print()
    
    choice = input("Wybierz opcję (1-4): ").strip()
    
    verify = False
    make_admin = False
    new_password = None
    
    if choice == "1":
        verify = True
    elif choice == "2":
        make_admin = True
    elif choice == "3":
        new_password = input("Podaj nowe hasło: ").strip()
        if not new_password:
            print("❌ Hasło nie może być puste!")
            sys.exit(1)
    elif choice == "4":
        verify = True
        make_admin = True
        new_password = input("Podaj nowe hasło: ").strip()
        if not new_password:
            print("❌ Hasło nie może być puste!")
            sys.exit(1)
    else:
        print("❌ Nieprawidłowy wybór!")
        sys.exit(1)
    
    print()
    fix_user(email, verify=verify, make_admin=make_admin, new_password=new_password)
