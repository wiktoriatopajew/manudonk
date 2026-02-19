# ✅ PRODUCTION DEPLOYMENT CHECKLIST

## 🚨 BEZPIECZEŃSTWO - KLUCZOWE ZMIANY PRZED WGRANIEM!

### 1. IMPORT SECURITY (api_routes.py)
**ZNAJDŹ LINIĘ ~1050:**
```python
IMPORT_TEST_MODE = True   # ← ZMIEŃ NA False !
```

### 2. DOMENY W EMAIL TEMPLATES
**Zaktualizuj wszystkie linki w email_campaign_templates.html:**
```html
http://localhost:8000 → https://twoja-domena.pl
```

### 3. STRIPE CONFIGURATION (.env)
```
STRIPE_SECRET_KEY=sk_live_xxxxx        # LIVE key!
STRIPE_WEBHOOK_SECRET=whsec_xxxxx      # LIVE webhook!
```

### 4. EMAIL CONFIGURATION (.env)  
```
EMAIL_HOST_USER=twoj-email@gmail.com   # TWÓJ EMAIL!
EMAIL_HOST_PASSWORD=app-password       # APP PASSWORD!
```

### 5. DOMAIN SETTINGS (main.py)
```python
DOMAIN = "https://twoja-domena.pl"     # ZMIEŃ Z localhost!
```

## 🔒 CO SIĘ ZMIENI PO USTAWIENIU IMPORT_TEST_MODE = False:

✅ **Import monitor** będzie wymagał logowania admina  
✅ **JWT token validation** aktywne  
✅ **Protected endpoints** zabezpieczone  
✅ **Admin-only access** do bulk import  

## 📋 DEPLOYMENT CHECKLIST

### Przed uploadem:
- [ ] `IMPORT_TEST_MODE = False` w api_routes.py
- [ ] Stripe LIVE keys w .env
- [ ] Email credentials w .env  
- [ ] Domain changed w main.py
- [ ] Email template links zaktualizowane
- [ ] Admin password zmieniony (`python create_admin.py`)
- [ ] Database backup wykonany

### Po wgraniu:
- [ ] Test admin login
- [ ] Test email wysyłania  
- [ ] Test płatności Stripe
- [ ] Test discount codes
- [ ] Import monitor wymaga admina (sprawdź!)
- [ ] Wszystkie email linki działają
- [ ] SSL certificates działają

## 📦 Instalacja i konfiguracja

- [ ] Zainstalowano zależności Python (`pip install -r requirements.txt`)
- [ ] Przygotowano plik `products.csv` z produktami
- [ ] Zaimportowano produkty do bazy (`python import_csv.py`)
- [ ] Wygenerowano slugi dla wszystkich produktów (`python generate_slugs.py`)

## 🔧 Konfiguracja

- [ ] Ustawiono `PAYPAL_CLIENT_ID` (zmienna środowiskowa lub w kodzie)
- [ ] Ustawiono `DOMAIN` na właściwą domenę produkcyjną
- [ ] Skopiowano `.env.example` jako `.env` i wypełniono danymi
- [ ] Zweryfikowano konfigurację bazy danych

## 🎨 Dostosowanie

- [ ] Dostosowano nazwę sklepu w [templates/base.html](templates/base.html)
- [ ] Zaktualizowano kontakt email w footerze
- [ ] Zmieniono meta opisy stron na własne
- [ ] (Opcjonalnie) Dodano logo do `static/`
- [ ] (Opcjonalnie) Dostosowano kolory w Tailwind

## 🔍 SEO

- [ ] Zweryfikowano działanie `/robots.txt`
- [ ] Zweryfikowano działanie `/sitemap.xml`
- [ ] Sprawdzono czy wszystkie produkty mają slugi
- [ ] Przetestowano clean URLs (`/instrukcje/...`)
- [ ] Sprawdzono breadcrumbs na stronach produktów
- [ ] Zweryfikowano meta tagi na stronach produktów
- [ ] Zmieniono domenę w sitemap.xml (zmienna `DOMAIN`)

## 🧪 Testowanie funkcjonalności

- [ ] Strona główna się ładuje
- [ ] Wyszukiwarka działa
- [ ] Filtry kategorii i marki działają
- [ ] Paginacja działa poprawnie
- [ ] Clean URLs działają
- [ ] Legacy URLs przekierowują (301) na clean URLs
- [ ] Strony produktów wyświetlają się poprawnie
- [ ] PayPal button się wyświetla
- [ ] Breadcrumbs są widoczne
- [ ] Strona success działa po "zakupie"

## 💳 Płatności

- [ ] PayPal Client ID jest ustawiony
- [ ] PayPal sandbox działa (tryb testowy)
- [ ] (Production) Przełączono na live PayPal credentials
- [ ] Przycisk PayPal renderuje się na stronie produktu
- [ ] Test płatności zakończył się sukcesem
- [ ] Strona success wyświetla się po płatności

## 🚀 Deployment

- [ ] Wybrany hosting/serwer
- [ ] Zainstalowano Python 3.8+
- [ ] Zainstalowano wszystkie zależności
- [ ] Ustawiono zmienne środowiskowe
- [ ] Baza danych jest dostępna
- [ ] Aplikacja uruchamia się bez błędów
- [ ] Skonfigurowano reverse proxy (Nginx/Apache)
- [ ] Skonfigurowano SSL/HTTPS
- [ ] Testowano działanie na produkcji

## 📊 Google Search Console

- [ ] Utworzono konto Google Search Console
- [ ] Dodano właściwość (domenę)
- [ ] Zweryfikowano własność domeny
- [ ] Przesłano sitemap: `https://twoja-domena.pl/sitemap.xml`
- [ ] Sprawdzono status indeksowania
- [ ] Dodano Google Analytics (opcjonalnie)

## 🔐 Bezpieczeństwo

- [ ] Zmieniono domyślne hasła (jeśli istnieją)
- [ ] Ustawiono HTTPS (SSL certificate)
- [ ] Skonfigurowano firewall
- [ ] Ograniczono dostęp do plików wrażliwych
- [ ] Backup bazy danych jest skonfigurowany
- [ ] Ustawiono monitoring błędów

## 📧 Email (opcjonalnie)

- [ ] Skonfigurowano SMTP server
- [ ] Testowano wysyłkę emaili
- [ ] Skonfigurowano template emaila z instrukcją
- [ ] Testowano automatyczną wysyłkę po płatności

## 📈 Monitoring

- [ ] Skonfigurowano Google Analytics
- [ ] Dodano monitoring uptime (UptimeRobot itp.)
- [ ] Skonfigurowano alerty dla błędów
- [ ] Monitoring wydajności bazy danych
- [ ] Regularne backupy bazy danych

## 📝 Dokumentacja

- [ ] README.md jest aktualny
- [ ] Zaktualizowano kontaktowe dane
- [ ] Dokumentacja dla zespołu jest gotowa
- [ ] Proces dodawania nowych produktów jest udokumentowany

## ✅ Launch Day

- [ ] Wszystkie powyższe checklisty są ukończone
- [ ] Wykonano final test wszystkich funkcji
- [ ] Zrobiono backup przed launch
- [ ] Strona jest dostępna publicznie
- [ ] Google indexing started (Search Console)
- [ ] Social media announcement (opcjonalnie)
- [ ] Email do pierwszych klientów (opcjonalnie)

---

## 🎉 Post-Launch

### Dzień 1-7
- [ ] Monitorować błędy i logi
- [ ] Sprawdzić Google Search Console codziennie
- [ ] Odpowiadać na feedback użytkowników
- [ ] Optymalizować powolne zapytania

### Tydzień 2-4
- [ ] Analizować dane Google Analytics
- [ ] Optymalizować popularne strony
- [ ] Dodawać nowe produkty
- [ ] Zbierać opinie klientów

### Miesiąc 2+
- [ ] Regularne audyty SEO
- [ ] A/B testing różnych elementów
- [ ] Optymalizacja conversion rate
- [ ] Rozbudowa funkcjonalności

---

## 📞 W razie problemów

1. Sprawdź logi aplikacji
2. Sprawdź Google Search Console
3. Sprawdź dokumentację: [README.md](README.md)
4. Zobacz troubleshooting w README
5. Kontakt z developerem

---

**Powodzenia z uruchomieniem sklepu! 🚀**
