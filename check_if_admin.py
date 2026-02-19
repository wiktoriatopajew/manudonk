"""Test który użytkownik ma uprawnienia admina"""
import requests

# Test login który wcześniej działał
email = "alphasouiri@gmail.com"
password = "test123"

print("=" * 60)
print("SPRAWDZANIE KONTA ADMINA")
print("=" * 60)

# Login
data = {"username": email, "password": password}
response = requests.post("https://manualbear.com/api/auth/login", data=data)

if response.status_code == 200:
    token_data = response.json()
    print(f"\n✅ Logowanie udane!")
    print(f"Email: {email}")
    print(f"Is Admin: {token_data.get('is_admin', False)}")
    
    if token_data.get('is_admin'):
        print(f"\n🎉 To jest konto ADMINA!")
        print(f"\nDane logowania:")
        print(f"  Email: {email}")
        print(f"  Hasło: test123")
    else:
        print(f"\n⚠️  To NIE jest konto admina - to zwykły użytkownik")
        print(f"\nMusisz utworzyć admina:")
        print(f"railway run python create_admin.py admin@example.com admin123")
else:
    print(f"\n❌ Logowanie nieudane: {response.status_code}")
    print(response.text)
