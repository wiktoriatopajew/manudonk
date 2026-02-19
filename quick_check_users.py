"""
Szybkie sprawdzenie użytkowników w Railway DB
"""
import os

# Sprawdź DATABASE_URL
db_url = os.getenv('DATABASE_URL', 'BRAK')
print(f"DATABASE_URL: {db_url}")
print()

if db_url == 'BRAK':
    print("ERROR: DATABASE_URL not set!")
    exit(1)

# Import po sprawdzeniu zmiennych
try:
    import psycopg2
    from psycopg2 import sql
    
    # Połącz się z bazą
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    # Sprawdź czy tabela istnieje
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'users'
        );
    """)
    table_exists = cur.fetchone()[0]
    
    if not table_exists:
        print("❌ Tabela 'users' nie istnieje!")
        conn.close()
        exit(1)
    
    print("✅ Tabela 'users' istnieje")
    print()
    
    # Pobierz użytkowników
    cur.execute("""
        SELECT id, email, username, is_admin, is_verified, created_at, 
               SUBSTRING(password_hash, 1, 50) as hash_preview
        FROM users 
        ORDER BY id;
    """)
    
    users = cur.fetchall()
    
    if not users:
        print("❌ BRAK UŻYTKOWNIKÓW W BAZIE!")
        conn.close()
        exit(1)
    
    print(f"Znaleziono {len(users)} użytkowników:")
    print("=" * 100)
    
    for user in users:
        user_id, email, username, is_admin, is_verified, created_at, hash_preview = user
        print(f"\nID: {user_id}")
        print(f"Email: {email}")
        print(f"Username: {username}")
        print(f"Is Admin: {is_admin}")
        print(f"Is Verified: {is_verified} {'✅' if is_verified else '❌'}")
        print(f"Created: {created_at}")
        print(f"Password Hash: {hash_preview}...")
        
        if not is_verified:
            print("  ⚠️  PROBLEM: Użytkownik nie jest zweryfikowany!")
    
    print("\n" + "=" * 100)
    
    # Podsumowanie
    verified = sum(1 for u in users if u[4])
    unverified = len(users) - verified
    
    print(f"\nPodsumowanie:")
    print(f"  Wszystkich: {len(users)}")
    print(f"  Zweryfikowanych: {verified}")
    print(f"  Niezweryfikowanych: {unverified}")
    
    if unverified > 0:
        print(f"\n⚠️  {unverified} użytkownik(ów) nie może się zalogować - brak weryfikacji!")
        print("Rozwiązanie: Ustaw is_verified=true dla tych użytkowników")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ BŁĄD: {e}")
    import traceback
    traceback.print_exc()
