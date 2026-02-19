"""Sprawdź WSZYSTKICH użytkowników i pokaż adminów"""
import requests

response = requests.get("https://manualbear.com/api/auth/admin/diagnose-users")

if response.status_code == 200:
    data = response.json()
    print(f"\n{'='*70}")
    print(f"WSZYSCY UŻYTKOWNICY W BAZIE ({data['total_users']})")
    print(f"{'='*70}\n")
    
    admins = []
    regular_users = []
    
    for user in data['users']:
        if user['is_admin']:
            admins.append(user)
        else:
            regular_users.append(user)
    
    # Pokaż adminów
    if admins:
        print(f"👑 ADMINOWIE ({len(admins)}):")
        print("-" * 70)
        for admin in admins:
            print(f"\n  ✅ Email: {admin['email']}")
            print(f"     Is Verified: {admin['is_verified']}")
            print(f"     Created: {admin['created_at']}")
            print(f"     Status: {'AKTYWNY' if admin['is_verified'] else 'NIE ZWERYFIKOWANY'}")
    else:
        print("❌ BRAK ADMINÓW!")
    
    # Pokaż zwykłych użytkowników  
    if regular_users:
        print(f"\n\n👤 ZWYKLI UŻYTKOWNICY ({len(regular_users)}):")
        print("-" * 70)
        for user in regular_users:
            print(f"\n  - Email: {user['email']}")
            print(f"    Is Verified: {user['is_verified']}")
            print(f"    Created: {user['created_at']}")
    
    print("\n" + "="*70)
    print("PODSUMOWANIE:")
    print("="*70)
    print(f"Wszystkich użytkowników: {data['total_users']}")
    print(f"Adminów: {len(admins)}")
    print(f"Zwykłych użytkowników: {len(regular_users)}")
    
    if admins:
        print("\n⚠️  Hasła NIE są przechowywane w plaintext!")
        print("Jeśli nie pamiętasz hasła admina, musisz je zresetować:")
        print("\n🔧 Opcje:")
        print("1. Użyj 'Forgot password' na stronie logowania")
        print("2. Lub zresetuj przez Railway CLI:")
        for admin in admins:
            print(f"   railway run python create_admin.py {admin['email']} NoweHaslo123")
else:
    print(f"Błąd: {response.status_code}")
    print(response.text)
