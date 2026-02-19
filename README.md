# � Manual Bear - Profesjonalny Sklep z Instrukcjami

Nowoczesny, szybki i responsywny sklep internetowy z katalogiem produktów. Zoptymalizowany pod kątem wydajności i SEO, gotowy do obsługi 100 000+ produktów.

> **🚀 Szybki start:** Zobacz [QUICKSTART.md](QUICKSTART.md) aby uruchomić sklep w 5 minut!

## 🚀 Technologie

- **Backend**: FastAPI (Python)
- **Baza danych**: SQLite z indeksami (obsługa 100k+ produktów)
- **Frontend**: Tailwind CSS (CDN) + Jinja2 templates
- **Płatności**: PayPal Checkout
- **Wydajność**: Bez ciężkich frameworków JS - czyste HTML

## 📋 Funkcjonalności

✅ **Strona główna** z wielką wyszukiwarką i najnowszymi produktami  
✅ **Wyszukiwarka** z filtrami (kategoria, marka)  
✅ **Paginacja** wyników wyszukiwania  
✅ **Strony produktów** z dynamicznymi meta tagami SEO  
✅ **Clean URLs** - SEO-friendly adresy (np. `/instrukcje/ford-f150-repair-manual-123`)  
✅ **Breadcrumbs** - okruszki nawigacyjne ze schema.org markup  
✅ **Robots.txt** - instrukcje dla robotów Google  
✅ **Sitemap.xml** - dynamiczna mapa strony dla 100k+ produktów  
✅ **Integracja PayPal** - bezpieczne płatności online  
✅ **Responsywny design** - działa na wszystkich urządzeniach  
✅ **Optymalizacja wydajności** - indeksy bazodanowe, lazy loading  

## 📁 Struktura projektu

```
Strona Manuals/
├── database/
│   ├── __init__.py
│   ├── models.py          # Modele SQLAlchemy + generowanie slugów
│   └── products.db        # Baza SQLite (po imporcie)
├── templates/
│   ├── base.html          # Szablon bazowy z header/footer
│   ├── index.html         # Strona główna z wyszukiwarką
│   ├── search.html        # Strona wyszukiwania z filtrami
│   ├── product.html       # Strona produktu z breadcrumbs i SEO
│   └── success.html       # Strona potwierdzenia zakupu
├── static/                # Pliki statyczne (CSS, JS, images)
├── app/                   # Placeholder dla dodatkowych modułów
├── main.py                # Główna aplikacja FastAPI z routami
├── import_csv.py          # Skrypt importu CSV z generowaniem slugów
├── generate_slugs.py      # Skrypt do generowania slugów dla istniejących produktów
├── requirements.txt       # Zależności Python
├── products_example.csv   # Przykładowy plik CSV
├── .env.example           # Przykładowa konfiguracja środowiska
├── .gitignore             # Git ignore rules
├── README.md              # Ten plik - główna dokumentacja
├── QUICKSTART.md          # ⚡ Przewodnik szybkiego startu (5 min)
├── SEO_GUIDE.md           # 📚 Szczegółowy przewodnik SEO
├── CHANGELOG.md           # 📝 Historia zmian i nowe funkcje
└── URL_STRUCTURE.md       # 🗺️ Mapa struktury URL
```

## 🔧 Instalacja i uruchomienie

### 1. Instalacja zależności

```powershell
pip install -r requirements.txt
```

### 2. Przygotowanie danych

Umieść plik `products.csv` w głównym katalogu projektu. Plik powinien zawierać kolumny:
- `title` - tytuł produktu
- `description` - opis produktu
- `price` - cena (liczba)
- `category` - kategoria
- `brand` - marka
- `model` - model

**Przykładowy plik:** Zobacz [products_example.csv](products_example.csv) dla formatu referencyjnego.

### 3. Import danych do bazy

```powershell
python import_csv.py
```

Skrypt:
- Utworzy bazę danych SQLite
- Wczyta dane z CSV
- Wyczyści dane (usuwa duplikaty, sprawdza typy)
- **Automatycznie wygeneruje SEO-friendly slugi dla każdego produktu**
- Importuje w chunksach dla lepszej wydajności
- Stworzy indeksy dla szybkiego wyszukiwania

**Dla istniejącej bazy:** Jeśli już masz bazę bez slugów, uruchom:
```powershell
python generate_slugs.py
```

### 4. Konfiguracja

#### PayPal Client ID
Ustaw swój PayPal Client ID jako zmienną środowiskową:

```powershell
$env:PAYPAL_CLIENT_ID="TWOJ_PAYPAL_CLIENT_ID"
```

**Jak uzyskać PayPal Client ID:**
1. Zaloguj się na https://developer.paypal.com
2. Przejdź do "My Apps & Credentials"
3. Utwórz nową aplikację lub użyj istniejącej
4. Skopiuj "Client ID"

#### Domena (dla production)
⚠️ **Ważne:** Przed wdrożeniem zmień domenę w sitemap i robots.txt:

```powershell
$env:DOMAIN="https://twoja-domena.pl"
```

Lub edytuj [main.py](main.py) i zmień wartość `DOMAIN = "https://twoja-domena.pl"`

### 5. Uruchomienie aplikacji

```powershell
python main.py
```

Lub:

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Aplikacja będzie dostępna pod adresem: **http://localhost:8000**

## 🔍 Endpointy API

- `GET /` - Strona główna
- `GET /search?q=...&category=...&brand=...&page=1` - Wyszukiwanie produktów
- `GET /instrukcje/{slug}` - Strona produktu (clean URL)
- `GET /product/{id}` - Legacy endpoint (przekierowuje do clean URL)
- `GET /api/brands?category=...` - API: pobierz marki dla kategorii
- `GET /robots.txt` - Robots.txt dla SEO
- `GET /sitemap.xml` - Dynamiczna mapa strony (wszystkie produkty)
- `GET /success` - Strona potwierdzenia zakupu
- `GET /health` - Health check

## 🎨 SEO Optymalizacja

### Clean URLs
Zamiast `/product?id=123` używamy SEO-friendly URLs:
```
https://strona.pl/instrukcje/ford-f150-repair-manual-123
```

### Breadcrumbs (Okruszki nawigacyjne)
Każda strona produktu ma strukturalne breadcrumbs ze schema.org markup:
```
Strona główna > Kategoria > Marka > Model
```
Google to uwielbia - ułatwia mu zrozumienie struktury sklepu.

### Robots.txt
```
User-agent: *
Allow: /
Allow: /search
Allow: /instrukcje/
Sitemap: https://strona.pl/sitemap.xml
```

### Sitemap.xml
Dynamicznie generowana mapa strony zawierająca wszystkie 100 000+ produktów.
Google może łatwo odkryć i zaindeksować cały katalog.

### Meta tagi
Każda strona produktu ma unikalne meta tagi:

```html
<title>{Tytuł produktu} - {Marka} {Model} | Instrukcja Obsługi</title>
<meta name="description" content="Kup instrukcję obsługi do {Marka} {Model}...">
```

## ⚡ Optymalizacje wydajności

1. **Indeksy bazodanowe** na kolumnach `title`, `category`, `brand`, `slug`
2. **Composite index** na `(category, brand)` dla szybkiego filtrowania
3. **Unique index** na `slug` dla szybkiego wyszukiwania po URL
4. **Paginacja** - ładowanie tylko 24 produktów na stronę
4. **Lazy rendering** - Jinja2 renderuje tylko to, co potrzebne
5. **CDN Tailwind** - szybkie ładowanie CSS
6. **Brak ciężkich frameworków JS** - czysty HTML
7. **SQLite z optymalizacjami** - `check_same_thread=False`

## 💳 Proces zakupu

1. Użytkownik wybiera produkt
2. Klika "Kup teraz" i podaje email
3. Klika przycisk PayPal i dokonuje płatności
4. Po pomyślnej płatności → przekierowanie na stronę `/success`
5. Wyświetlany komunikat: *"Dziękujemy! Twoja instrukcja zostanie wysłana na email w ciągu 1-5 minut"*

**Uwaga**: Automatyczna wysyłka emaili wymaga dodatkowej implementacji (np. webhook PayPal + serwer SMTP).

## 📧 Automatyzacja wysyłki (opcjonalne)

Aby zautomatyzować wysyłkę instrukcji, możesz:

1. **Dodać webhook PayPal**: Słuchaj na `PAYMENT.CAPTURE.COMPLETED`
2. **Utworzyć endpoint**: `POST /webhook/paypal`
3. **Wysłać email**: Użyj `smtplib` lub SendGrid API
4. **Dołączyć PDF**: Załącz instrukcję jako attachment

Przykładowy kod:

```python
from fastapi import BackgroundTasks
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

@app.post("/webhook/paypal")
async def paypal_webhook(request: Request, background_tasks: BackgroundTasks):
    # Weryfikacja webhooka PayPal
    # Wyciągnij email i product_id z custom_id
    # background_tasks.add_task(send_email, email, product_id)
    pass
```

## 🛠️ Możliwe rozszerzenia

- 📧 Automatyczna wysyłka emaili z instrukcjami
- 🔐 Panel administratora do zarządzania produktami
- 📊 Dashboard z statystykami sprzedaży
- 🔎 Elasticsearch dla jeszcze szybszego wyszukiwania
- 🖼️ Upload i wyświetlanie okładek instrukcji
- ⭐ System opinii i ocen
- 🌍 Wsparcie dla wielu języków (i18n)
- 💰 Stripe jako alternatywa dla PayPal

## 📝 Przykładowa struktura CSV

```csv
title,description,price,category,brand,model
"Instrukcja obsługi Samsung Galaxy S21","Pełna instrukcja obsługi dla Samsung Galaxy S21 w języku polskim",29.99,Electronics,Samsung,Galaxy S21
"Manual for iPhone 13 Pro","Complete user guide for iPhone 13 Pro",34.99,Electronics,Apple,iPhone 13 Pro
```

## 🐛 Troubleshooting

### Problem: Brak produktów po imporcie
**Rozwiązanie**: Sprawdź, czy plik `products.csv` zawiera wszystkie wymagane kolumny i czy import zakończył się sukcesem.

### Problem: Clean URLs nie działają (404)
**Rozwiązanie**: 
1. Sprawdź czy produkty mają slugi: uruchom `python generate_slugs.py`
2. Upewnij się, że używasz nowej struktury URL: `/instrukcje/{slug}`

### Problem: Sitemap jest pusty
**Rozwiązanie**: 
1. Wygeneruj slugi: `python generate_slugs.py`
2. Odśwież stronę `/sitemap.xml`

### Problem: PayPal button się nie wyświetla
**Rozwiązanie**: 
1. Sprawdź czy ustawiłeś `PAYPAL_CLIENT_ID`
2. Upewnij się, że masz połączenie z internetem (SDK ładowany z CDN)

### Problem: Wolne wyszukiwanie
**Rozwiązanie**: 
1. Upewnij się, że utworzyłeś indeksy (automatycznie przy imporcie)
2. Sprawdź rozmiar bazy - `database/products.db` nie powinien być zbyt duży
3. Rozważ użycie `LIMIT` w zapytaniach

## 📚 Dodatkowa dokumentacja

- **[QUICKSTART.md](QUICKSTART.md)** - ⚡ Przewodnik szybkiego startu (uruchom w 5 minut!)
- **[SEO_GUIDE.md](SEO_GUIDE.md)** - 📖 Szczegółowy przewodnik po funkcjach SEO
- **[URL_STRUCTURE.md](URL_STRUCTURE.md)** - 🗺️ Mapa struktury URL i routingu
- **[CHANGELOG.md](CHANGELOG.md)** - 📝 Historia zmian i nowe funkcje
- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - ✅ Checklist przed wdrożeniem
- **[products_example.csv](products_example.csv)** - Przykładowy format pliku CSV

## 📄 Licencja

Ten projekt jest szablonem demonstracyjnym. Możesz go swobodnie modyfikować i używać do celów komercyjnych.

## 🤝 Wsparcie

Masz pytania? Napisz na: kontakt@manuals.pl

---

**Zbudowano z ❤️ używając FastAPI, SQLite i Tailwind CSS**
