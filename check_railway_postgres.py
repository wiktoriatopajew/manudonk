"""
Sprawdź użytkowników bezpośrednio w Postgres Railway
"""
import os
import psycopg2

db_url = os.getenv('DATABASE_URL')
print(f"Łączę się z Railway Postgres...")

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    # Sprawdź wszystkich użytkowników
    cur.execute("""
        SELECT id, email, is_admin, is_verified, created_at 
        FROM users 
        ORDER BY id;
    """)
    
    users = cur.fetchall()
    
    print("\n" + "="*70)
    print(f"WSZYSCY UŻYTKOWNICY W RAILWAY POSTGRES ({len(users)})")
    print("="*70)
    
    admins = []
    regular = []
    
    for user in users:
        user_id, email, is_admin, is_verified, created_at = user
        
        if is_admin:
            admins.append(user)
        else:
            regular.append(user)
    
    # Pokaż adminów
    if admins:
        print(f"\n👑 ADMINOWIE ({len(admins)}):")
        print("-"*70)
        for user_id, email, is_admin, is_verified, created_at in admins:
            print(f"\n  ✅ ID: {user_id}")
            print(f"     Email: {email}")
            print(f"     Is Admin: {is_admin}")
            print(f"     Is Verified: {is_verified}")
            print(f"     Created: {created_at}")
    else:
        print("\n❌ BRAK ADMINÓW W BAZIE!")
    
    # Pokaż zwykłych użytkowników
    if regular:
        print(f"\n\n👤 ZWYKLI UŻYTKOWNICY ({len(regular)}):")
        print("-"*70)
        for user_id, email, is_admin, is_verified, created_at in regular:
            print(f"\n  - ID: {user_id}")
            print(f"    Email: {email}")
            print(f"    Is Verified: {is_verified}")
            print(f"    Created: {created_at}")
    
    print("\n" + "="*70)
    print("PODSUMOWANIE:")
    print("="*70)
    print(f"Wszystkich użytkowników: {len(users)}")
    print(f"Adminów: {len(admins)}")
    print(f"Zwykłych użytkowników: {len(regular)}")
    
    if admins:
        print("\n⚠️  HASŁA SĄ ZAHASHOWANE - nie można ich odczytać!")
        print("\nJeśli nie pamiętasz hasła, resetuj je:")
        for user_id, email, _, _, _ in admins:
            print(f"  railway run python create_admin.py {email} NoweHaslo123")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ BŁĄD: {e}")
    import traceback
    traceback.print_exc()
