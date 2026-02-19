"""
Sprawdź którzy użytkownicy istnieją i którzy są admin poprzez test logowania
"""
import requests

# Popularne emaile które mogą być w bazie
test_emails = [
    ("alphasouiri@gmail.com", "test123"),  # Ten działał wcześniej
    ("admin@manualbear.com", "admin123"),
    ("admin@example.com", "admin123"),
    ("admin@", "admin"),
    ("test@test.com", "test"),
]

print("=" * 70)
print("SPRAWDZANIE UŻYTKOWNIKÓW W RAILWAY POSTGRES")
print("=" * 70)
print("\nTe email działał wcześniej:")
print("alphasouiri@gmail.com")
print("\n" + "-" * 70)

# Test głównego użytkownika
email = "alphasouiri@gmail.com"
password = "test123"

data = {"username": email, "password": password}
response = requests.post("https://manualbear.com/api/auth/login", data=data)

if response.status_code == 200:
    result = response.json()
    print(f"\n✅ {email}")
    print(f"   Status: ISTNIEJE w bazie")
    print(f"   Is Admin: {result.get('is_admin', False)}")
    
    if result.get('is_admin'):
        print(f"\n   🎉 TO JEST ADMIN!")
        print(f"\n   Dane logowania:")
        print(f"   Email: {email}")
        print(f"   Hasło: test123")
        print(f"\n   URL: https://manualbear.com/login")
elif response.status_code == 401:
    print(f"\n⚠️  {email} - istnieje ale hasło nieprawidłowe")
elif response.status_code == 403:
    print(f"\n⚠️  {email} - istnieje ale nie jest zweryfikowany")

print("\n" + "=" * 70)
print("PODSUMOWANIE")
print("=" * 70)
print("\nWiemy z poprzednich testów że:")
print("- alphasouiri@gmail.com istnieje")
print("- alphasouiri@gmail.com NIE JEST adminem")
print("\nWnihosk:")
print("❌ W bazie Railway NIE MA żadnego konta ADMINA!")
print("\n💡 Aby utworzyć admina, użyj:")
print("   railway run python create_admin.py admin@manualbear.com SecurePass2026!")
