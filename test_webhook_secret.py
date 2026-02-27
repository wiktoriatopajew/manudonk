"""Sprawdź czy webhook secret jest poprawnie skonfigurowany"""
import os
from dotenv import load_dotenv

load_dotenv()

webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

print("🔐 STRIPE_WEBHOOK_SECRET status:")
print(f"   Set: {'YES' if webhook_secret else 'NO'}")
print(f"   Length: {len(webhook_secret) if webhook_secret else 0}")
print(f"   Prefix: {webhook_secret[:20] if webhook_secret else 'NOT SET'}...")
print(f"   Is placeholder: {webhook_secret == 'whsec_your_webhook_secret_here'}")

if webhook_secret == "whsec_your_webhook_secret_here":
    print("\n❌ PROBLEM: Webhook secret jest placeholderem!")
    print("\n📝 Musisz zaktualizować STRIPE_WEBHOOK_SECRET w Railway:")
    print("   1. W Stripe Dashboard → Webhooks → kliknij swój endpoint")
    print("   2. W sekcji 'Signing secret' kliknij 'Reveal'")
    print("   3. Skopiuj secret (whsec_...)")
    print("   4. W Railway → Variables → zaktualizuj STRIPE_WEBHOOK_SECRET")
elif not webhook_secret:
    print("\n❌ PROBLEM: Webhook secret nie jest ustawiony!")
else:
    print("\n✅ Webhook secret wygląda dobrze")
    print("\nSprawdź w Stripe Dashboard → Webhooks czy requesty przychodzą.")
