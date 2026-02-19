# 📧 Email Marketing System - Complete Guide

## Overview

Kompletny profesjonalny system email marketingu z:
- ✅ Newsletter popup z automatycznym kodem rabatowym 10%
- ✅ Admin panel do zarządzania subskrybentami
- ✅ Tworzenie i wysyłanie kampanii emailowych
- ✅ Tracking otwarć i kliknięć w emailach
- ✅ System porzuconych koszyków
- ✅ Automatyczne przypomnienia o kodach rabatowych
- ✅ Segmentacja subskrybentów

## Struktura Systemu

### 1. Modele Bazy Danych (`database/models.py`)

#### Newsletter
- `email` - Email subskrybenta (unique)
- `discount_code` - Unikalny kod rabatowy (format: WELCOMEXXXXXX)
- `subscribed_at` - Data subskrypcji
- `is_active` - Czy subskrypcja aktywna
- `has_purchased` - Czy klient dokonał zakupu (do segmentacji)
- `last_reminder_sent` - Kiedy wysłano ostatnie przypomnienie

#### EmailCampaign
- `name` - Nazwa kampanii (wewnętrzna)
- `subject` - Temat emaila
- `html_content` - Treść HTML emaila
- `segment` - Grupa docelowa (all/purchased/not_purchased)
- `status` - Status (draft/sent/scheduled)
- `sent_at` - Kiedy wysłano
- `sent_count` - Liczba wysłanych emaili

#### EmailTracking
- `campaign_id` - ID kampanii
- `subscriber_id` - ID subskrybenta
- `email` - Email odbiorcy
- `tracking_token` - Token do trackingu (unique)
- `opened` - Czy email został otwarty
- `opened_at` - Kiedy otwarty
- `clicked` - Czy kliknięto link
- `clicked_at` - Kiedy kliknięto

#### AbandonedCart
- `email` - Email użytkownika
- `product_ids` - JSON array produktów
- `total_value` - Wartość koszyka
- `reminder_sent` - Czy wysłano przypomnienie
- `reminder_sent_at` - Kiedy wysłano
- `recovered` - Czy użytkownik dokończył zakup

### 2. Email Templates (`email_utils.py`)

#### send_welcome_newsletter_email()
Wysyła email powitalny z kodem rabatowym 10% po zapisie do newslettera.

#### send_marketing_campaign_email()
Wysyła kampanię marketingową z opcjonalnym trackingiem otwarć/kliknięć.

#### send_abandoned_cart_email()
Wysyła przypomnienie o porzuconym koszyku z dodatko wym 5% rabatem.

#### send_discount_reminder_email()
Przypomina o niewykorzystanym kodzie rabatowym po 7 dniach.

### 3. API Endpoints

#### Newsletter (Public)
- `POST /api/newsletter/subscribe` - Zapisz się do newslettera
- `POST /api/newsletter/validate-code` - Waliduj kod rabatowy

#### Email Marketing (Admin Only)
- `GET /api/email-marketing/subscribers?segment=all` - Lista subskrybentów
  - Segments: all, active, purchased, not_purchased
- `POST /api/email-marketing/campaigns` - Utwórz kampanię
- `GET /api/email-marketing/campaigns` - Lista kampanii
- `POST /api/email-marketing/campaigns/{id}/send` - Wyślij kampanię
- `GET /api/email-marketing/campaigns/{id}/stats` - Statystyki kampanii

#### Tracking
- `GET /api/email/track/{token}` - Tracking pixel (1x1 PNG)
- `GET /api/email/click/{token}?url=...` - Tracking kliknięć + redirect
- `POST /api/email/track-cart` - Zapisz porzucony koszyk
- `POST /api/email/mark-purchased` - Oznacz jako kupiony

### 4. Admin Panel

#### Dostęp
- URL: `http://localhost:8000/admin/newsletter`
- Wymaga zalogowania jako admin

#### Funkcje
1. **Subscribers Tab**
   - Przeglądanie wszystkich subskrybentów
   - Filtrowanie: All / Active / Purchased / Not Purchased
   - Widok: email, kod rabatowy, data, status, czy kupił

2. **Campaigns Tab**
   - Lista wszystkich kampanii
   - Status: Draft / Sent
   - Liczba wysłanych emaili
   - Przycisk "Send Now" dla draft
   - Przycisk "View Stats" dla wysłanych

3. **Create Campaign Tab**
   - Nazwa kampanii
   - Temat emaila
   - Segment docelowy
   - Treść HTML
   - Preview przed wysłaniem

4. **Statistics**
   - Total Sent - Ile wysłano
   - Opened - Ile otwarto
   - Open Rate - % otwarć
   - Click Rate - % kliknięć

### 5. Automatyzacja (`email_automation.py`)

#### Abandoned Cart Reminders
Wysyła przypomnienie o porzuconym koszyku po 24 godzinach.

```python
python email_automation.py
```

#### Discount Code Reminders
Wysyła przypomnienie o kodzie rabatowym 7 dni po subskrypcji (jeśli nie kupił).

#### Harmonogram (Windows Task Scheduler)
1. Otwórz Task Scheduler
2. Create Basic Task
3. Nazwa: "Email Marketing Automation"
4. Trigger: Daily, co 1 dzień, o 10:00
5. Action: Start a program
   - Program: `C:\Python\python.exe`
   - Arguments: `email_automation.py`
   - Start in: `C:\Users\Sebek\Desktop\Strona Manuals`
6. Finish

Lub uruchom ręcznie codziennie:
```powershell
cd "C:\Users\Sebek\Desktop\Strona Manuals"
.venv\Scripts\python.exe email_automation.py
```

## Workflow Użycia

### 1. Użytkownik Zapisuje się do Newslettera
1. Popup pojawia się po 5 sekundach
2. Użytkownik podaje email
3. System generuje kod WELCOMEXXXXXX
4. Wysyła email powitalny z kodem
5. Popup pokazuje kod z możliwością skopiowania
6. Kod zapisany w localStorage (popup nie pokazuje się ponownie)

### 2. Użytkownik Korzysta z Kodu
1. Dodaje produkty do koszyka
2. W koszyku wpisuje kod WELCOMEXXXXXX
3. Kod validowany przez API
4. 10% rabat zastosowany do całości
5. Przy checkout rabat zawarty w Stripe session

### 3. Admin Wysyła Kampanię
1. Zaloguj jako admin
2. Przejdź do `/admin/newsletter`
3. Kliknij "Create Campaign"
4. Wypełnij formularz:
   - Nazwa: "Spring Sale 2026"
   - Temat: "20% OFF All Manuals!"
   - Segment: "Not Purchased Yet"
   - Content: HTML template
5. Kliknij "Create Campaign"
6. W zakładce "Campaigns" kliknij "Send Now"
7. System:
   - Tworzy tracking token dla każdego odbiorcy
   - Wysyła email z tracking pixelem
   - Zapisuje statystyki

### 4. Tracking Otwarć i Kliknięć
- Email zawiera: `<img src="/api/email/track/{token}" width="1" height="1">`
- Gdy użytkownik otworzy email → pixel ładuje się → tracking.opened = True
- Linki w emailu: `<a href="/api/email/click/{token}?url=...">`
- Gdy użytkownik kliknie → tracking.clicked = True → redirect do URL

### 5. Porzucone Koszyki
1. Użytkownik dodaje produkty do koszyka
2. JavaScript trackuje: `POST /api/email/track-cart`
3. Po 24h skrypt `email_automation.py` wysyła przypomnienie
4. Email zawiera dodatkowe 5% rabatu
5. Jeśli użytkownik kupi → koszyk oznaczony jako recovered

### 6. Przypomnienia o Kodach
1. Subskrybent zapisał się 7 dni temu
2. Nie dokonał zakupu (`has_purchased = False`)
3. Nie wysłano jeszcze przypomnienia (`last_reminder_sent = None`)
4. Skrypt `email_automation.py` wysyła przypomnienie
5. Email przypomina o kodzie i zachęca do zakupu

## Przykładowy HTML Template Kampanii

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; background: #111827; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: #1f2937; border-radius: 12px; overflow: hidden; }
        .header { background: linear-gradient(135deg, #3b82f6, #06b6d4); padding: 40px; text-align: center; }
        .content { padding: 30px; color: #e5e7eb; }
        .button { display: inline-block; background: linear-gradient(135deg, #3b82f6, #06b6d4); color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="color: white; margin: 0;">20% OFF Spring Sale! 🌸</h1>
        </div>
        <div class="content">
            <p>Hi there!</p>
            <p>Spring is here and we're celebrating with our biggest sale of the year!</p>
            <p><strong>Get 20% OFF</strong> all vehicle manuals this weekend only.</p>
            <div style="text-align: center;">
                <a href="/api/email/click/{{TRACKING_TOKEN}}?url=http://localhost:8000" class="button">
                    Shop Now →
                </a>
            </div>
            <p>Don't miss out - sale ends Sunday midnight!</p>
        </div>
    </div>
</body>
</html>
```

## Statystyki i Monitoring

### Metryki Kluczowe
- **Open Rate** - % otwarć (dobry: >20%)
- **Click Rate** - % kliknięć (dobry: >3%)
- **Conversion Rate** - % zakupów po kliknięciu
- **Unsubscribe Rate** - % wypisów (niski: <1%)

### Monitorowanie w Admin Panel
1. Przejdź do "Campaigns"
2. Kliknij "View Stats" przy kampanii
3. Zobacz:
   - Total Sent
   - Opened (liczba i %)
   - Clicked (liczba i %)

## Best Practices

### Email Design
- ✅ Używaj dark theme matching stronie
- ✅ Jasne Call-to-Action buttony
- ✅ Responsive design (mobile-friendly)
- ✅ Krótkie, konkretne teksty
- ✅ Wyraźne linki z tracking

### Segmentacja
- **All** - Wszyscy (ogłoszenia, nowości)
- **Purchased** - Cross-sell, upsell, loyalty
- **Not Purchased** - Promocje, zachęty, przypomnienia

### Częstotliwość
- Newsletter: Raz w tygodniu
- Promocje: 2-3 razy w miesiącu
- Abandoned cart: 24h po porzuceniu
- Kod reminder: 7 dni po zapisie

### A/B Testing
1. Utwórz dwie kampanie z różnymi tematami
2. Wyślij do połowy segmentu każdą
3. Porównaj open rate i click rate
4. Używaj lepszej wersji w przyszłości

## Troubleshooting

### Emaile nie dochodzą
1. Sprawdź SMTP credentials w `.env`
2. Sprawdź spam folder
3. Zobacz terminal logs przy wysyłaniu
4. Test: `python test_newsletter_email.py`

### Tracking nie działa
1. Sprawdź czy tracking_token jest unikalny
2. Sprawdź logs w terminalu przy otwarciu
3. Verify pixel URL: `/api/email/track/{token}`

### Automation nie wysyła
1. Sprawdź czy task scheduler działa
2. Uruchom ręcznie: `python email_automation.py`
3. Zobacz logs - ile znaleziono do wysłania
4. Sprawdź warunki (24h dla cart, 7 dni dla reminder)

## Rozszerzenia (Future)

- ✅ A/B Testing kampanii
- ✅ Email templates library
- ✅ Scheduled campaigns (auto-wysyłka)
- ✅ Drip campaigns (serie emaili)
- ✅ SMS notifications
- ✅ Push notifications
- ✅ Advanced analytics dashboard
- ✅ Export subscriber lists (CSV)
- ✅ GDPR compliance tools (unsubscribe, data export)

## Support

W razie pytań lub problemów:
1. Sprawdź logi w terminalu
2. Zobacz dokumentację API
3. Testuj pojedyncze komponenty osobno
4. Używaj development mode w `email_utils.py`
