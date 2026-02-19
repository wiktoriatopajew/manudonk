# 🗺️ Struktura URL - Mapa strony

## Hierarchia URL sklepu

```
https://strona.pl/
│
├── / (Strona główna)
│   └── Wyświetla: najnowsze produkty, wielka wyszukiwarka
│
├── /search (Katalog z filtrami)
│   ├── ?q=search_term
│   ├── ?category=Electronics
│   ├── ?brand=Samsung
│   └── ?page=2
│   └── Wyświetla: lista produktów z paginacją
│
├── /instrukcje/{slug} ✨ CLEAN URLs
│   ├── /instrukcje/ford-f150-repair-manual-123
│   ├── /instrukcje/samsung-galaxy-s21-instrukcja-456
│   └── /instrukcje/bosch-waw28560pl-manual-789
│   └── Wyświetla: szczegóły produktu, przycisk zakupu
│
├── /product/{id} (Legacy - przekierowanie)
│   └── → 301 Redirect → /instrukcje/{slug}
│
├── /success (Po zakupie)
│   └── Wyświetla: potwierdzenie, informacje o dostawie
│
├── /robots.txt (SEO)
│   └── Instrukcje dla robotów Google
│
├── /sitemap.xml (SEO)
│   └── Mapa wszystkich 100 000+ produktów
│
└── /api/
    └── /api/brands?category=...
        └── JSON: lista marek dla kategorii
```

---

## Przykłady Clean URLs

### Format
```
/instrukcje/{brand}-{model}-{keywords}-{id}
```

### Przykłady rzeczywiste:

#### 1. Elektronika
```
/instrukcje/samsung-galaxy-s21-instrukcja-1
/instrukcje/sony-xr-55a90j-manual-2
/instrukcje/hp-laserjet-pro-m404n-guide-3
```

#### 2. Motoryzacja
```
/instrukcje/ford-f150-2012-repair-manual-4
/instrukcje/toyota-corolla-owners-manual-5
```

#### 3. AGD
```
/instrukcje/bosch-waw28560pl-pralka-manual-6
/instrukcje/electrolux-eob8s31x-piekarnik-instrukcja-7
/instrukcje/siemens-eq6-plus-ekspres-manual-8
```

#### 4. Narzędzia
```
/instrukcje/dewalt-dcd996-drill-manual-9
/instrukcje/makita-dhp484-wiertarka-instrukcja-10
```

---

## Breadcrumbs (Okruszki)

Nawigacja na stronie produktu:

```
Strona główna > Kategoria > Marka > Model
      ↓             ↓          ↓       ↓
      /        /search?   /search?   (aktualna)
               category=  category=
                          &brand=
```

### Przykład dla Samsung Galaxy S21:
```
Strona główna > Electronics > Samsung > Galaxy S21
```

### Przykład dla Ford F-150:
```
Strona główna > Automotive > Ford > F-150 2012
```

---

## SEO URL Best Practices ✅

### ✅ Dobre praktyki (Zaimplementowane)

1. **Czytelność**
   - `/instrukcje/ford-f150-repair-manual-123` ✅
   - vs `?id=123&cat=auto` ❌

2. **Słowa kluczowe**
   - Zawierają markę, model, typ produktu ✅

3. **Krótkie i zwięzłe**
   - Max 100 znaków ✅
   - Bez zbędnych słów ✅

4. **Małe litery i myślniki**
   - `samsung-galaxy-s21` ✅
   - vs `Samsung_Galaxy_S21` ❌

5. **Unikalne**
   - Każdy produkt ma unikalny slug ✅
   - ID na końcu dla gwarancji unikalności ✅

6. **Bez polskich znaków**
   - `instrukcja` zamiast `instrukcją` ✅
   - Automatyczna transliteracja ✅

---

## Routing Flow

```
User Request
     ↓
┌────────────────┐
│ /instrukcje/   │
│ {slug}         │
└────────┬───────┘
         ↓
┌────────────────┐
│ FastAPI        │
│ Route Handler  │
└────────┬───────┘
         ↓
┌────────────────┐
│ Database Query │
│ WHERE slug=... │
└────────┬───────┘
         ↓
    Found? ────→ Yes ──→ Render product.html
         │
         No
         ↓
    404 Error
```

---

## URL Redirection (301)

### Legacy URL → Clean URL

```
Old: /product/123
         ↓
    Check Database
         ↓
   Product found
         ↓
   Has slug? ─→ Yes ──→ 301 Redirect
         │              /instrukcje/{slug}
         │
         No
         ↓
   Render with old URL
   (fallback)
```

---

## Sitemap Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    
    <!-- Homepage -->
    <url>
        <loc>https://strona.pl/</loc>
        <priority>1.0</priority>
        <changefreq>daily</changefreq>
    </url>
    
    <!-- Search -->
    <url>
        <loc>https://strona.pl/search</loc>
        <priority>0.9</priority>
        <changefreq>daily</changefreq>
    </url>
    
    <!-- Products (100,000+) -->
    <url>
        <loc>https://strona.pl/instrukcje/samsung-galaxy-s21-1</loc>
        <priority>0.8</priority>
        <changefreq>weekly</changefreq>
    </url>
    
    <!-- ... more products ... -->
    
</urlset>
```

---

## Analytics Tracking

### Struktura URL ułatwia tracking:

```javascript
// Google Analytics - automatyczna kategoryzacja
/instrukcje/ford-*        → Automotive
/instrukcje/samsung-*     → Electronics
/instrukcje/bosch-*       → Home Appliances
```

### Przykładowe metryki:
- **Najpopularniejsze marki:** `/instrukcje/samsung-*`
- **Najpopularniejsze kategorie:** Electronics
- **Conversion rate per URL pattern**

---

## 🎯 Dlaczego Clean URLs są ważne?

1. **SEO Ranking** ⬆️
   - Google preferuje czytelne URLs
   - Słowa kluczowe w URL = wyższy ranking

2. **User Trust** 🔒
   - Użytkownicy ufają czytelnym adresom
   - Łatwiej udostępnić link

3. **Click-Through Rate** 📈
   - W wynikach Google wyświetla się czytelny URL
   - Więcej kliknięć

4. **Social Sharing** 🌐
   - Ładniejsze linki na Facebook/Twitter
   - Automatyczne podglądy

5. **Analytics** 📊
   - Łatwiejsza analiza ruchu
   - Szybsza identyfikacja popularnych produktów

---

**Clean URLs = Lepsze SEO + Lepszy UX = Więcej sprzedaży! 🚀**
