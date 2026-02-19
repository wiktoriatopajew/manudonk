"""
Napraw użytkowników - ustaw is_verified=True dla wszystkich
"""
import os
import sys

# Pobierz DATABASE_URL
db_url = os.getenv('DATABASE_URL')

if not db_url:
    print("ERROR: DATABASE_URL not set!")
    sys.exit(1)

print(f"Connecting to database...")

try:
    import psycopg2
    
    # Połącz się
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    # Sprawdź niezweryfikowanych użytkowników
    cur.execute("""
        SELECT id, email, is_verified 
        FROM users 
        WHERE is_verified = FALSE
        ORDER BY id;
    """)
    
    unverified = cur.fetchall()
    
    if not unverified:
        print("✅ Wszyscy użytkownicy są już zweryfikowani!")
        cur.close()
        conn.close()
        sys.exit(0)
    
    print(f"\n❌ Znaleziono {len(unverified)} niezweryfikowanych użytkowników:")
    for user_id, email, verified in unverified:
        print(f"  - ID: {user_id}, Email: {email}, Verified: {verified}")
    
    # Napraw
    print(f"\n🔧 Naprawiam użytkowników...")
    cur.execute("""
        UPDATE users 
        SET is_verified = TRUE 
        WHERE is_verified = FALSE;
    """)
    
    conn.commit()
    updated = cur.rowcount
    
    print(f"✅ Zaktualizowano {updated} użytkowników!")
    
    # Sprawdź ponownie
    cur.execute("SELECT COUNT(*) FROM users WHERE is_verified = FALSE;")
    remaining = cur.fetchone()[0]
    
    if remaining == 0:
        print("✅ Wszyscy użytkownicy są teraz zweryfikowani!")
    else:
        print(f"⚠️  Nadal {remaining} użytkowników nie jest zweryfikowanych")
    
    cur.close()
    conn.close()
    
    print("\n🎉 Gotowe! Użytkownicy powinni móc się teraz zalogować.")
    
except Exception as e:
    print(f"❌ BŁĄD: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
