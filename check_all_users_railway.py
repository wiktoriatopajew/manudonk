"""
Sprawdź wszystkich użytkowników przez Railway run
"""
import os
import sys

print("=" * 80)
print("Diagnostyka użytkowników w Railway DB")
print("=" * 80)

db_url = os.getenv('DATABASE_URL')
if not db_url:
    print("ERROR: DATABASE_URL not found!")
    sys.exit(1)

print(f"✅ DATABASE_URL found")
print()

try:
    import psycopg2
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    # Get all users
    cur.execute("""
        SELECT id, email, username, is_verified, is_admin, created_at,
               SUBSTRING(password_hash, 1, 20) as hash_preview
        FROM users
        ORDER BY id;
    """)
    
    users = cur.fetchall()
    
    if not users:
        print("❌ BRAK UŻYTKOWNIKÓW!")
        cur.close()
        conn.close()
        sys.exit(0)
    
    print(f"Znaleziono {len(users)} użytkowników:")
    print("=" * 80)
    
    for user in users:
        user_id, email, username, is_verified, is_admin, created_at, hash_preview = user
        print(f"\nID: {user_id}")
        print(f"Email: {email}")
        print(f"Username: {username or 'BRAK'}")
        print(f"Is Verified: {is_verified} {'✅' if is_verified else '❌ PROBLEM!'}")
        print(f"Is Admin: {is_admin}")
        print(f"Created: {created_at}")
        print(f"Password Hash: {hash_preview}...")
        
        if not is_verified:
            print("  ⚠️  TEN UŻYTKOWNIK NIE MOŻE SIĘ ZALOGOWAĆ - is_verified=False")
    
    print("\n" + "=" * 80)
    print("PODSUMOWANIE:")
    print("=" * 80)
    
    verified = sum(1 for u in users if u[3])
    unverified = len(users) - verified
    
    print(f"Wszystkich: {len(users)}")
    print(f"Zweryfikowanych: {verified}")
    print(f"Niezweryfikowanych: {unverified}")
    
    if unverified == 0:
        print("\n✅ WSZYSCY UŻYTKOWNICY MOGĄ SIĘ ZALOGOWAĆ!")
    else:
        print(f"\n❌ {unverified} użytkownik(ów) NIE MOŻE SIĘ ZALOGOWAĆ!")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ BŁĄD: {e}")
    import traceback
    traceback.print_exc()
