"""
Diagnoza problemu z logowaniem - Railway PostgreSQL
Sprawdza użytkowników i potencjalne problemy z bazą danych
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from database.models import User, Base
from passlib.context import CryptContext

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def diagnose_login():
    """Sprawdź wszystkie aspekty logowania w Railway DB"""
    
    # Połączenie z Railway PostgreSQL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ BŁĄD: DATABASE_URL nie znaleziono w .env!")
        return
    
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    print("=" * 80)
    print("🔍 DIAGNOZA LOGOWANIA - RAILWAY POSTGRESQL")
    print("=" * 80)
    print(f"📡 Baza danych: {database_url.split('@')[1] if '@' in database_url else 'unknown'}")
    print()
    
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Test połączenia
        print("✅ Połączenie z bazą: SUKCES")
        print()
        
        # Sprawdź strukturę tabeli users
        inspector = inspect(engine)
        if 'users' not in inspector.get_table_names():
            print("❌ BŁĄD KRYTYCZNY: Tabela 'users' nie istnieje!")
            print("   Musisz uruchomić init_db.py aby utworzyć tabele")
            return
        
        print("✅ Tabela 'users' istnieje")
        
        # Sprawdź kolumny tabeli
        columns = [col['name'] for col in inspector.get_columns('users')]
        print(f"📊 Kolumny tabeli users: {', '.join(columns)}")
        print()
        
        # Pobierz wszystkich użytkowników
        users = session.query(User).all()
        
        if not users:
            print("⚠️  PROBLEM: Brak użytkowników w bazie danych!")
            print("   Musisz utworzyć konto przez rejestrację lub create_admin.py")
            print()
            return
        
        print(f"👥 Znaleziono {len(users)} użytkowników:")
        print("=" * 80)
        
        for i, user in enumerate(users, 1):
            print(f"\n{i}. Email: {user.email}")
            print(f"   🔑 ID: {user.id}")
            print(f"   ✉️  is_verified: {user.is_verified} {'✅' if user.is_verified else '❌ PROBLEM!'}")
            print(f"   👑 is_admin: {user.is_admin}")
            print(f"   📅 created_at: {user.created_at}")
            print(f"   🔐 password_hash: {user.password_hash[:50]}...")
            
            # Sprawdź czy hash hasła jest prawidłowy
            if user.password_hash:
                if user.password_hash.startswith('$2b$') or user.password_hash.startswith('$2a$'):
                    print(f"   ✅ Hash hasła wygląda prawidłowo (bcrypt)")
                else:
                    print(f"   ❌ PROBLEM: Hash hasła ma nieprawidłowy format!")
            else:
                print(f"   ❌ BŁĄD: Brak hashu hasła!")
            
            # Diagnoza problemów
            problems = []
            if not user.is_verified:
                problems.append("Konto nie jest zweryfikowane (is_verified = False)")
            if not user.password_hash:
                problems.append("Brak hashu hasła")
            
            if problems:
                print(f"\n   ⚠️  ZDIAGNOZOWANE PROBLEMY:")
                for problem in problems:
                    print(f"      - {problem}")
        
        print("\n" + "=" * 80)
        print("📋 PODSUMOWANIE:")
        print("=" * 80)
        
        verified_count = sum(1 for u in users if u.is_verified)
        admin_count = sum(1 for u in users if u.is_admin)
        
        print(f"Wszystkich użytkowników: {len(users)}")
        print(f"Zweryfikowanych: {verified_count}")
        print(f"Niezweryfikowanych: {len(users) - verified_count}")
        print(f"Administratorów: {admin_count}")
        print()
        
        # Główne problemy
        print("🔍 MOŻLIWE PRZYCZYNY PROBLEMU Z LOGOWANIEM:")
        print()
        
        if len(users) == 0:
            print("❌ 1. Brak użytkowników w bazie")
            print("   Rozwiązanie: Utwórz konto przez rejestrację lub uruchom create_admin.py")
        
        unverified_users = [u for u in users if not u.is_verified]
        if unverified_users:
            print(f"❌ 2. {len(unverified_users)} konto(a) nie są zweryfikowane:")
            for u in unverified_users:
                print(f"   - {u.email}")
            print("   Rozwiązanie: Zweryfikuj konta ręcznie lub przez email")
        
        bad_hash_users = [u for u in users if not u.password_hash or not (u.password_hash.startswith('$2b$') or u.password_hash.startswith('$2a$'))]
        if bad_hash_users:
            print(f"❌ 3. {len(bad_hash_users)} konto(a) mają nieprawidłowy hash hasła")
            for u in bad_hash_users:
                print(f"   - {u.email}")
            print("   Rozwiązanie: Resetuj hasła dla tych kont")
        
        if not unverified_users and not bad_hash_users and len(users) > 0:
            print("✅ Wszystkie konta wyglądają prawidłowo!")
            print()
            print("Jeśli nadal nie możesz się zalogować, sprawdź:")
            print("  1. Czy używasz prawidłowego emaila")
            print("  2. Czy hasło jest prawidłowe")
            print("  3. Czy aplikacja używa prawidłowego DATABASE_URL")
            print("  4. Logi aplikacji w Railway")
        
        session.close()
        
    except Exception as e:
        print(f"\n❌ BŁĄD POŁĄCZENIA: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("Możliwe przyczyny:")
        print("  1. Błędny DATABASE_URL w .env")
        print("  2. Baza danych Railway jest niedostępna")
        print("  3. Problemy z siecią/firewallem")

if __name__ == "__main__":
    diagnose_login()
