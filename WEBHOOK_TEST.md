# 🧪 Test Stripe Webhook Lokalnie

## Problem
Stripe nie może wysłać webhook do localhost z internetu.

## Rozwiązanie: Stripe CLI

### 1. Pobierz Stripe CLI
https://stripe.com/docs/stripe-cli

Lub użyj Scoop (Windows):
```powershell
scoop bucket add stripe https://github.com/stripe/scoop-stripe-cli.git
scoop install stripe
```

### 2. Zaloguj się
```powershell
stripe login
```

### 3. Uruchom webhook forwarding
```powershell
stripe listen --forward-to localhost:8000/api/orders/webhook
```

To da Ci **webhook signing secret** - skopiuj go!

### 4. Dodaj webhook secret do .env
```
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
```

### 5. Restart serwera

### 6. Testuj zakup
Stripe CLI będzie przekazywał eventy z Stripe do Twojego localhost!

---

## Opcja 2: Manualny test (szybsze teraz)

Możemy symulować zakup bezpośrednio w kodzie:

```powershell
python test_purchase.py
```

Który wolisz?
