"""Sprawdź adminów przez API"""
import requests

try:
    response = requests.get("https://manualbear.com/api/auth/admin/diagnose-users")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nWszystkich użytkowników: {data['total_users']}")
        
        admins = [u for u in data['users'] if u['is_admin']]
        
        if admins:
            print(f"\n{'='*60}")
            print(f"KONTA ADMINÓW ({len(admins)}):")
            print(f"{'='*60}")
            
            for admin in admins:
                print(f"\nEmail: {admin['email']}")
                print(f"Is Admin: {admin['is_admin']}")
                print(f"Is Verified: {admin['is_verified']}")
                print(f"Created: {admin['created_at']}")
                print("-" * 60)
                
            print("\n⚠️  UWAGA: Hasła NIE SĄ PRZECHOWYWANE w plaintext!")
            print("Jeśli nie pamiętasz hasła, musisz je zresetować.")
            print("\nAby zresetować hasło admina:")
            print("railway run python create_admin.py admin@email.com NoweHaslo123")
        else:
            print("\n❌ BRAK ADMINÓW W BAZIE!")
            print("\nUtwórz admina:")
            print("railway run python create_admin.py admin@example.com admin123")
    else:
        print(f"Błąd: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"Błąd: {e}")
