"""Sprawdź konfigurację Stripe webhook"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

DOMAIN = os.getenv("DOMAIN", "https://manualbear.com")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

print("="*80)
print("🔍 STRIPE WEBHOOK DIAGNOSTYKA")
print("="*80)

# 1. Sprawdź zmienne środowiskowe
print("\n📋 Zmienne środowiskowe:")
print(f"   DOMAIN: {DOMAIN}")
print(f"   STRIPE_SECRET_KEY: {'SET' if STRIPE_SECRET_KEY else 'NOT SET'}")
print(f"   STRIPE_WEBHOOK_SECRET: {os.getenv('STRIPE_WEBHOOK_SECRET', 'NOT SET')[:20]}...")

# 2. Sprawdź endpoint webhook
webhook_url = f"{DOMAIN}/api/orders/webhook"
print(f"\n🔗 Webhook URL który powinieneś użyć w Stripe:")
print(f"   {webhook_url}")

# 3. Sprawdź webhooks w Stripe
if STRIPE_SECRET_KEY:
    print("\n📡 Sprawdzam webhooks w Stripe...")
    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        
        # Lista webhooks
        webhooks = stripe.WebhookEndpoint.list(limit=10)
        
        if not webhooks.data:
            print("\n❌ BRAK SKONFIGUROWANYCH WEBHOOKÓW!")
            print("\n📝 Musisz dodać webhook w Stripe Dashboard:")
            print("   1. Wejdź: https://dashboard.stripe.com/webhooks")
            print("   2. Kliknij 'Add endpoint'")
            print(f"   3. URL: {webhook_url}")
            print("   4. Event: checkout.session.completed")
            print("   5. Skopiuj 'Signing secret' i dodaj do Railway jako STRIPE_WEBHOOK_SECRET")
        else:
            print(f"\n✅ Znaleziono {len(webhooks.data)} webhook(ów):")
            for wh in webhooks.data:
                print(f"\n   URL: {wh.url}")
                print(f"   Status: {wh.status}")
                print(f"   Events: {', '.join(wh.enabled_events)}")
                
                # Sprawdź czy URL się zgadza
                if wh.url == webhook_url:
                    print("   ✅ URL się zgadza!")
                    if 'checkout.session.completed' in wh.enabled_events:
                        print("   ✅ Event 'checkout.session.completed' jest włączony!")
                    else:
                        print("   ❌ Event 'checkout.session.completed' NIE jest włączony!")
                        print(f"      Włączone eventy: {wh.enabled_events}")
                else:
                    print(f"   ⚠️  URL nie pasuje! Powinno być: {webhook_url}")
                    
    except Exception as e:
        print(f"\n❌ Błąd: {e}")
else:
    print("\n❌ STRIPE_SECRET_KEY nie jest ustawiony!")

# 4. Sprawdź ostatnie płatności bez zamówień
print("\n\n💳 Sprawdzam ostatnie payment_intents bez zamówień...")
try:
    response = requests.get(f"{DOMAIN}/api/orders/debug-config")
    if response.status_code == 200:
        data = response.json()
        print(f"\n   Stripe Keys: {'✅ SET' if data.get('stripe_key_set') else '❌ NOT SET'}")
        print(f"   Webhook Secret: {'✅ SET' if data.get('webhook_secret_set') else '❌ NOT SET'}")
except:
    pass

print("\n" + "="*80)
print("📌 PODSUMOWANIE:")
print("="*80)
print("""
Jeśli webhook NIE jest skonfigurowany:

1. Wejdź na: https://dashboard.stripe.com/webhooks
2. Upewnij się że jesteś w odpowiednim trybie (Test/Live)
3. Kliknij 'Add endpoint'
4. Wpisz URL: """ + webhook_url + """
5. Dodaj event: checkout.session.completed
6. Kliknij 'Add endpoint'
7. Kliknij na utworzony endpoint
8. Skopiuj 'Signing secret' (whsec_...)
9. Dodaj do Railway Variables:
   STRIPE_WEBHOOK_SECRET=whsec_twoj_secret

Po dodaniu webhook secret, Railway zrestartuje aplikację.
Wtedy płatności będą automatycznie tworzyć zamówienia!
""")
